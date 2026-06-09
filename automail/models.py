from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class TransactionType(str, Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"


class AccountCategory(str, Enum):
    PERSONAL_OR_JOINT = "personal_or_joint"
    CORPORATE_OR_OTHER = "corporate_or_other"


class AssetInstructionType(str, Enum):
    CASH = "cash"
    SI_FOP_DVP = "si_fop_dvp"


class ApprovalDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(slots=True)
class TransactionRequest:
    client_name: str
    account_no: str
    transaction_type: TransactionType
    account_category: AccountCategory
    amount_hkd: float
    currency: str = "HKD"
    instruction_type: AssetInstructionType = AssetInstructionType.CASH
    market_value_hkd: float | None = None
    settlement_amount_hkd: float | None = None
    has_debit_cash_or_stock_before_or_after: bool = False
    is_margin_account_with_debit_balance: bool = False
    beneficiary_name: str = ""
    requested_by: str = ""
    purpose: str = ""
    extra_context: dict[str, Any] = field(default_factory=dict)

    def effective_amount_hkd(self) -> float:
        if self.instruction_type == AssetInstructionType.SI_FOP_DVP:
            candidates = [value for value in (self.market_value_hkd, self.settlement_amount_hkd, self.amount_hkd) if value is not None]
            return max(candidates) if candidates else self.amount_hkd
        return self.amount_hkd


@dataclass(slots=True)
class ApprovalRequirement:
    role_code: str
    display_name: str
    reason: str
    mandatory: bool = True


@dataclass(slots=True)
class ApprovalAction:
    approver_role: str
    approver_name: str
    approver_email: str
    decision: ApprovalDecision
    received_at: datetime = field(default_factory=utc_now)
    message_id: str = field(default_factory=lambda: uuid4().hex)
    comment: str = ""
    raw_content: str = ""


@dataclass(slots=True)
class EmailMessage:
    subject: str
    body: str
    to: list[str]
    cc: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    message_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(slots=True)
class WorkflowCase:
    case_id: str
    transaction: TransactionRequest
    required_approvals: list[ApprovalRequirement]
    initial_email: EmailMessage
    approval_actions: list[ApprovalAction] = field(default_factory=list)
    next_step_email: EmailMessage | None = None
    created_at: datetime = field(default_factory=utc_now)

    def approval_status_by_role(self) -> dict[str, ApprovalDecision]:
        latest: dict[str, ApprovalDecision] = {}
        for action in self.approval_actions:
            latest[action.approver_role] = action.decision
        return latest

    def all_required_approved(self) -> bool:
        status_by_role = self.approval_status_by_role()
        return all(status_by_role.get(requirement.role_code) == ApprovalDecision.APPROVED for requirement in self.required_approvals if requirement.mandatory)
