from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .interfaces import CaseRepository
from .models import (
    AccountCategory,
    ApprovalAction,
    ApprovalDecision,
    ApprovalRequirement,
    AssetInstructionType,
    EmailMessage,
    TransactionRequest,
    TransactionType,
    WorkflowCase,
    utc_now,
)


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported type: {type(value)}")


def dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_json_default)


def loads(payload: str) -> Any:
    return json.loads(payload)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_transaction(data: dict[str, Any]) -> TransactionRequest:
    return TransactionRequest(
        client_name=data["client_name"],
        account_no=data["account_no"],
        transaction_type=TransactionType(data["transaction_type"]),
        account_category=AccountCategory(data["account_category"]),
        amount_hkd=float(data["amount_hkd"]),
        currency=data.get("currency", "HKD"),
        instruction_type=AssetInstructionType(data.get("instruction_type", AssetInstructionType.CASH.value)),
        market_value_hkd=data.get("market_value_hkd"),
        settlement_amount_hkd=data.get("settlement_amount_hkd"),
        has_debit_cash_or_stock_before_or_after=bool(data.get("has_debit_cash_or_stock_before_or_after", False)),
        is_margin_account_with_debit_balance=bool(data.get("is_margin_account_with_debit_balance", False)),
        beneficiary_name=data.get("beneficiary_name", ""),
        requested_by=data.get("requested_by", ""),
        purpose=data.get("purpose", ""),
        extra_context=data.get("extra_context", {}),
    )


def _parse_requirement(data: dict[str, Any]) -> ApprovalRequirement:
    return ApprovalRequirement(
        role_code=data["role_code"],
        display_name=data["display_name"],
        reason=data["reason"],
        mandatory=bool(data.get("mandatory", True)),
    )


def _parse_action(data: dict[str, Any]) -> ApprovalAction:
    return ApprovalAction(
        approver_role=data["approver_role"],
        approver_name=data["approver_name"],
        approver_email=data["approver_email"],
        decision=ApprovalDecision(data["decision"]),
        received_at=_parse_datetime(data["received_at"]),
        message_id=data["message_id"],
        comment=data.get("comment", ""),
        raw_content=data.get("raw_content", ""),
    )


def _parse_email(data: dict[str, Any]) -> EmailMessage:
    return EmailMessage(
        subject=data["subject"],
        body=data["body"],
        to=list(data.get("to", [])),
        cc=list(data.get("cc", [])),
        attachments=list(data.get("attachments", [])),
        message_id=data.get("message_id") or "",
    )


def parse_workflow_case(payload: dict[str, Any]) -> WorkflowCase:
    return WorkflowCase(
        case_id=payload["case_id"],
        transaction=_parse_transaction(payload["transaction"]),
        required_approvals=[_parse_requirement(item) for item in payload.get("required_approvals", [])],
        initial_email=_parse_email(payload["initial_email"]),
        approval_actions=[_parse_action(item) for item in payload.get("approval_actions", [])],
        next_step_email=_parse_email(payload["next_step_email"]) if payload.get("next_step_email") else None,
        created_at=_parse_datetime(payload["created_at"]),
    )


def dump_workflow_case(workflow_case: WorkflowCase) -> dict[str, Any]:
    return {
        "case_id": workflow_case.case_id,
        "transaction": asdict(workflow_case.transaction),
        "required_approvals": [asdict(item) for item in workflow_case.required_approvals],
        "initial_email": asdict(workflow_case.initial_email),
        "approval_actions": [asdict(item) for item in workflow_case.approval_actions],
        "next_step_email": asdict(workflow_case.next_step_email) if workflow_case.next_step_email else None,
        "created_at": workflow_case.created_at.isoformat(),
    }


class SqliteCaseRepository(CaseRepository):
    def __init__(self, db_path: str | Path = "automail_web.db") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
              case_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS templates (
              key TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              payload TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save_case(self, workflow_case: WorkflowCase) -> None:
        now = utc_now().isoformat()
        payload = dumps(dump_workflow_case(workflow_case))
        cursor = self._conn.cursor()
        existing = cursor.execute("SELECT created_at FROM cases WHERE case_id = ?", (workflow_case.case_id,)).fetchone()
        created_at = existing["created_at"] if existing else workflow_case.created_at.isoformat()
        cursor.execute(
            """
            INSERT INTO cases(case_id, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
            """,
            (workflow_case.case_id, payload, created_at, now),
        )
        self._conn.commit()

    def get_case(self, case_id: str) -> WorkflowCase:
        row = self._conn.execute("SELECT payload FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if not row:
            raise KeyError(case_id)
        return parse_workflow_case(loads(row["payload"]))

    def list_cases(self) -> list[WorkflowCase]:
        rows = self._conn.execute("SELECT payload FROM cases ORDER BY updated_at DESC").fetchall()
        return [parse_workflow_case(loads(row["payload"])) for row in rows]

    def list_case_meta(self) -> list[tuple[str, str, str]]:
        rows = self._conn.execute("SELECT case_id, created_at, updated_at FROM cases ORDER BY updated_at DESC").fetchall()
        return [(row["case_id"], row["created_at"], row["updated_at"]) for row in rows]

    def upsert_template(self, key: str, name: str, content: str) -> dict[str, Any]:
        now = utc_now().isoformat()
        payload = dumps(
            {
                "key": key,
                "name": name,
                "versions": [{"id": f"{key}:{now}", "content": content, "created_at": now}],
            }
        )
        cursor = self._conn.cursor()
        existing = cursor.execute("SELECT payload FROM templates WHERE key = ?", (key,)).fetchone()
        if existing:
            data = loads(existing["payload"])
            versions = list(data.get("versions", []))
            versions.insert(0, {"id": f"{key}:{now}", "content": content, "created_at": now})
            payload = dumps({"key": key, "name": name, "versions": versions[:50]})
        cursor.execute(
            """
            INSERT INTO templates(key, name, payload, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET name=excluded.name, payload=excluded.payload, updated_at=excluded.updated_at
            """,
            (key, name, payload, now),
        )
        self._conn.commit()
        return loads(payload)

    def get_template(self, key: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT payload FROM templates WHERE key = ?", (key,)).fetchone()
        return loads(row["payload"]) if row else None

    def list_templates(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT payload FROM templates ORDER BY updated_at DESC").fetchall()
        return [loads(row["payload"]) for row in rows]


def ensure_default_templates(repository: SqliteCaseRepository) -> None:
    if repository.get_template("initial_approval_email"):
        return
    repository.upsert_template(
        key="initial_approval_email",
        name="初始审批邮件",
        content=(
            "Case ID: {{caseId}}\n"
            "客户: {{transaction.client_name}} ({{transaction.account_no}})\n"
            "交易: {{transaction.transaction_type}} / {{transaction.instruction_type}}\n"
            "审批金额(HKD): {{effectiveAmountHkd}}\n"
            "所需审批: {{requiredApprovers}}\n\n"
            "请回复 APPROVED 或 REJECTED 并附上备注。"
        ),
    )
    repository.upsert_template(
        key="next_step_email",
        name="下一步操作邮件（Settlement）",
        content=(
            "Case ID: {{caseId}}\n"
            "客户: {{transaction.client_name}} ({{transaction.account_no}})\n"
            "已完成审批，烦请继续后续操作。\n\n"
            "审批摘要:\n{{approvalSummary}}\n\n"
            "附件:\n- 初始审批邮件\n- 全部审批回信\n- 附件清单"
        ),
    )
