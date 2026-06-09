from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .adapters.memory import InMemoryEmailGateway, LocalFileAttachmentPackager
from .models import (
    AccountCategory,
    ApprovalAction,
    ApprovalDecision,
    AssetInstructionType,
    TransactionRequest,
    TransactionType,
    utc_now,
)
from .persistence import SqliteCaseRepository, ensure_default_templates
from .rules import ApprovalPolicyEngine
from .services import ApprovalWorkflowService
from .template_engine import render_template


APPROVER_DIRECTORY: dict[str, list[str]] = {
    "CO_MAKER": ["co-maker@company.com"],
    "CHECKER": ["checker@company.com"],
    "HCO": ["hco@company.com"],
    "HF": ["hf@company.com"],
    "RO_OR_SUPERVISOR": ["ro@company.com"],
    "RISK_MANAGEMENT": ["risk@company.com"],
}


class TransactionRequestPayload(BaseModel):
    clientName: str
    accountNo: str
    transactionType: str
    accountCategory: str
    amountHkd: float
    currency: str = "HKD"
    instructionType: str = "cash"
    marketValueHkd: float | None = None
    settlementAmountHkd: float | None = None
    hasDebitCashOrStockBeforeOrAfter: bool = False
    isMarginAccountWithDebitBalance: bool = False
    beneficiaryName: str = ""
    requestedBy: str = ""
    purpose: str = ""
    extraContext: dict[str, Any] = Field(default_factory=dict)


class CreateCasePayload(BaseModel):
    transaction: TransactionRequestPayload
    cc: list[str] = Field(default_factory=list)
    approverDirectory: dict[str, list[str]] | None = None


class ManualActionPayload(BaseModel):
    approverRole: str
    approverName: str
    approverEmail: str
    decision: str
    receivedAt: str | None = None
    comment: str = ""
    rawContent: str = ""


class TemplateUpsertPayload(BaseModel):
    name: str
    content: str


class TemplatePreviewPayload(BaseModel):
    transaction: TransactionRequestPayload
    content: str | None = None


def _to_transaction(payload: TransactionRequestPayload) -> TransactionRequest:
    return TransactionRequest(
        client_name=payload.clientName,
        account_no=payload.accountNo,
        transaction_type=TransactionType(payload.transactionType),
        account_category=AccountCategory(payload.accountCategory),
        amount_hkd=payload.amountHkd,
        currency=payload.currency,
        instruction_type=AssetInstructionType(payload.instructionType),
        market_value_hkd=payload.marketValueHkd,
        settlement_amount_hkd=payload.settlementAmountHkd,
        has_debit_cash_or_stock_before_or_after=payload.hasDebitCashOrStockBeforeOrAfter,
        is_margin_account_with_debit_balance=payload.isMarginAccountWithDebitBalance,
        beneficiary_name=payload.beneficiaryName,
        requested_by=payload.requestedBy,
        purpose=payload.purpose,
        extra_context=payload.extraContext,
    )


def _case_status(workflow_case) -> str:
    if any(action.decision == ApprovalDecision.REJECTED for action in workflow_case.approval_actions):
        return "rejected"
    if workflow_case.all_required_approved():
        return "approved"
    return "pending"


def _case_view(workflow_case, updated_at: str) -> dict[str, Any]:
    return {
        "caseId": workflow_case.case_id,
        "transaction": asdict(workflow_case.transaction),
        "requiredApprovals": [asdict(item) for item in workflow_case.required_approvals],
        "approvalActions": [
            {
                "approverRole": item.approver_role,
                "approverName": item.approver_name,
                "approverEmail": item.approver_email,
                "decision": item.decision.value,
                "receivedAt": item.received_at.isoformat(),
                "messageId": item.message_id,
                "comment": item.comment,
                "rawContent": item.raw_content,
            }
            for item in workflow_case.approval_actions
        ],
        "initialEmailSubject": workflow_case.initial_email.subject,
        "initialEmailBody": workflow_case.initial_email.body,
        "nextStepEmailSubject": workflow_case.next_step_email.subject if workflow_case.next_step_email else None,
        "nextStepEmailBody": workflow_case.next_step_email.body if workflow_case.next_step_email else None,
        "createdAt": workflow_case.created_at.isoformat(),
        "updatedAt": updated_at,
        "status": _case_status(workflow_case),
    }


class SilentNotifier:
    def notify(self, subject: str, message: str) -> None:
        return


repository = SqliteCaseRepository()
ensure_default_templates(repository)
email_gateway = InMemoryEmailGateway()
packager = LocalFileAttachmentPackager(output_dir="outbox")
service = ApprovalWorkflowService(
    policy_engine=ApprovalPolicyEngine(),
    email_gateway=email_gateway,
    notifier=SilentNotifier(),
    repository=repository,
    packager=packager,
)

app = FastAPI(title="AutoMail Web API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/cases")
def list_cases() -> list[dict[str, Any]]:
    cases = repository.list_cases()
    meta = {case_id: updated_at for case_id, _, updated_at in repository.list_case_meta()}
    return [_case_view(item, meta.get(item.case_id, item.created_at.isoformat())) for item in cases]


@app.post("/api/cases")
def create_case(payload: CreateCasePayload) -> dict[str, Any]:
    transaction = _to_transaction(payload.transaction)
    approver_directory = payload.approverDirectory or APPROVER_DIRECTORY
    workflow_case = service.start_case(request=transaction, approver_directory=approver_directory, cc=payload.cc)
    meta = {case_id: updated_at for case_id, _, updated_at in repository.list_case_meta()}
    return _case_view(workflow_case, meta.get(workflow_case.case_id, workflow_case.created_at.isoformat()))


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    try:
        workflow_case = repository.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    meta = {cid: updated_at for cid, _, updated_at in repository.list_case_meta()}
    return _case_view(workflow_case, meta.get(case_id, workflow_case.created_at.isoformat()))


@app.post("/api/cases/{case_id}/refresh")
def refresh_case(case_id: str) -> dict[str, Any]:
    try:
        workflow_case = service.refresh_approvals(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    meta = {cid: updated_at for cid, _, updated_at in repository.list_case_meta()}
    return _case_view(workflow_case, meta.get(case_id, workflow_case.created_at.isoformat()))


@app.post("/api/cases/{case_id}/actions")
def add_manual_action(case_id: str, payload: ManualActionPayload) -> dict[str, Any]:
    received_at = utc_now() if payload.receivedAt is None else datetime.fromisoformat(payload.receivedAt)
    action = ApprovalAction(
        approver_role=payload.approverRole,
        approver_name=payload.approverName,
        approver_email=payload.approverEmail,
        decision=ApprovalDecision(payload.decision),
        received_at=received_at,
        comment=payload.comment,
        raw_content=payload.rawContent,
    )
    try:
        workflow_case = service.register_manual_reply(case_id, action)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    meta = {cid: updated_at for cid, _, updated_at in repository.list_case_meta()}
    return _case_view(workflow_case, meta.get(case_id, workflow_case.created_at.isoformat()))


@app.post("/api/cases/{case_id}/seed-demo-approvals")
def seed_demo_approvals(case_id: str) -> dict[str, Any]:
    try:
        workflow_case = repository.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    base_time = utc_now()
    actions: list[ApprovalAction] = []
    for index, requirement in enumerate(workflow_case.required_approvals, start=1):
        role = requirement.role_code
        actions.append(
            ApprovalAction(
                approver_role=role,
                approver_name=requirement.display_name,
                approver_email=(APPROVER_DIRECTORY.get(role, ["unknown@company.com"])[0]),
                decision=ApprovalDecision.APPROVED,
                received_at=base_time + timedelta(minutes=index * 2),
                comment="Approved.",
                raw_content="APPROVED",
            )
        )

    email_gateway.seed_replies = {workflow_case.initial_email.message_id: actions}
    refreshed = service.refresh_approvals(case_id)
    meta = {cid: updated_at for cid, _, updated_at in repository.list_case_meta()}
    return _case_view(refreshed, meta.get(case_id, refreshed.created_at.isoformat()))


@app.get("/api/templates")
def list_templates() -> list[dict[str, Any]]:
    return repository.list_templates()


@app.get("/api/templates/{key}")
def get_template(key: str) -> dict[str, Any]:
    record = repository.get_template(key)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    return record


@app.put("/api/templates/{key}")
def upsert_template(key: str, payload: TemplateUpsertPayload) -> dict[str, Any]:
    return repository.upsert_template(key=key, name=payload.name, content=payload.content)


@app.post("/api/templates/{key}/preview")
def preview_template(key: str, payload: TemplatePreviewPayload) -> dict[str, Any]:
    record = repository.get_template(key)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    content = payload.content if payload.content is not None else (record.get("versions") or [{}])[0].get("content", "")
    tx = _to_transaction(payload.transaction)
    effective_amount = tx.effective_amount_hkd()
    required = ApprovalPolicyEngine().determine_requirements(tx)
    rendered = render_template(
        content,
        {
            "caseId": "PREVIEW",
            "transaction": tx,
            "effectiveAmountHkd": f"{effective_amount:,.2f}",
            "requiredApprovers": ", ".join(item.display_name for item in required),
            "approvalSummary": "\n".join(f"- {item.display_name}: APPROVED" for item in required),
        },
    )
    return {"rendered": rendered}


def main() -> None:
    import uvicorn

    uvicorn.run("automail.web_api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
