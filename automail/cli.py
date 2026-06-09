from __future__ import annotations

import argparse
from datetime import timedelta

from .adapters.memory import (
    ConsoleNotifier,
    InMemoryCaseRepository,
    InMemoryEmailGateway,
    LocalFileAttachmentPackager,
    seed_reply_map,
)
from .models import (
    AccountCategory,
    ApprovalAction,
    ApprovalDecision,
    AssetInstructionType,
    TransactionRequest,
    TransactionType,
    utc_now,
)
from .rules import ApprovalPolicyEngine
from .services import ApprovalWorkflowService


APPROVER_DIRECTORY = {
    "CO_MAKER": ["co-maker@company.com"],
    "CHECKER": ["checker@company.com"],
    "HCO": ["hco@company.com"],
    "HF": ["hf@company.com"],
    "RO_OR_SUPERVISOR": ["ro@company.com"],
    "RISK_MANAGEMENT": ["risk@company.com"],
}


def build_demo_request() -> TransactionRequest:
    return TransactionRequest(
        client_name="ABC Capital Client",
        account_no="AC-778899",
        transaction_type=TransactionType.WITHDRAWAL,
        account_category=AccountCategory.CORPORATE_OR_OTHER,
        amount_hkd=12_500_000,
        instruction_type=AssetInstructionType.SI_FOP_DVP,
        market_value_hkd=13_000_000,
        settlement_amount_hkd=12_400_000,
        has_debit_cash_or_stock_before_or_after=True,
        beneficiary_name="ABC Capital Client",
        requested_by="ops.requester@company.com",
        purpose="Client securities withdrawal",
    )


def build_demo_replies() -> list[ApprovalAction]:
    base_time = utc_now()
    return [
        ApprovalAction(
            approver_role="HCO",
            approver_name="Helen Chan",
            approver_email="hco@company.com",
            decision=ApprovalDecision.APPROVED,
            received_at=base_time + timedelta(minutes=3),
            comment="Approved.",
            raw_content="APPROVED - threshold confirmed.",
        ),
        ApprovalAction(
            approver_role="HF",
            approver_name="Henry Fong",
            approver_email="hf@company.com",
            decision=ApprovalDecision.APPROVED,
            received_at=base_time + timedelta(minutes=5),
            comment="Approved.",
            raw_content="APPROVED - proceed.",
        ),
        ApprovalAction(
            approver_role="RISK_MANAGEMENT",
            approver_name="Rachel Tam",
            approver_email="risk@company.com",
            decision=ApprovalDecision.APPROVED,
            received_at=base_time + timedelta(minutes=9),
            comment="Risk review completed.",
            raw_content="APPROVED - debit scenario reviewed.",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an approval workflow demo.")
    parser.add_argument("--demo", action="store_true", help="Run the built-in approval workflow demo.")
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        return

    notifier = ConsoleNotifier()
    repository = InMemoryCaseRepository()
    email_gateway = InMemoryEmailGateway()
    packager = LocalFileAttachmentPackager(output_dir="outbox")
    service = ApprovalWorkflowService(
        policy_engine=ApprovalPolicyEngine(),
        email_gateway=email_gateway,
        notifier=notifier,
        repository=repository,
        packager=packager,
    )

    request = build_demo_request()
    workflow_case = service.start_case(request=request, approver_directory=APPROVER_DIRECTORY, cc=["ops.control@company.com"])
    print(f"Case created: {workflow_case.case_id}")
    print(f"Initial draft subject: {workflow_case.initial_email.subject}")
    print(f"Recipients: {', '.join(workflow_case.initial_email.to)}")

    email_gateway.seed_replies = seed_reply_map(workflow_case.initial_email.message_id, build_demo_replies())
    refreshed = service.refresh_approvals(workflow_case.case_id)

    print(f"Approvals collected: {len(refreshed.approval_actions)}")
    if refreshed.next_step_email:
        print(f"Next-step draft subject: {refreshed.next_step_email.subject}")
        print("Attachments:")
        for path in refreshed.next_step_email.attachments:
            print(f" - {path}")


if __name__ == "__main__":
    main()
