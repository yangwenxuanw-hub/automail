from __future__ import annotations

from dataclasses import replace
from textwrap import dedent
from uuid import uuid4

from .interfaces import AttachmentPackager, CaseRepository, EmailGateway, Notifier
from .models import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalRequirement,
    EmailMessage,
    TransactionRequest,
    TransactionType,
    WorkflowCase,
)
from .rules import ApprovalPolicyEngine


class ApprovalWorkflowService:
    def __init__(
        self,
        policy_engine: ApprovalPolicyEngine,
        email_gateway: EmailGateway,
        notifier: Notifier,
        repository: CaseRepository,
        packager: AttachmentPackager,
    ) -> None:
        self.policy_engine = policy_engine
        self.email_gateway = email_gateway
        self.notifier = notifier
        self.repository = repository
        self.packager = packager

    def start_case(self, request: TransactionRequest, approver_directory: dict[str, list[str]], cc: list[str] | None = None) -> WorkflowCase:
        case_id = uuid4().hex[:12]
        required = self.policy_engine.determine_requirements(request)
        initial_email = self._build_initial_email(case_id, request, required, approver_directory, cc or [])
        drafted = self.email_gateway.create_draft(initial_email)
        workflow_case = WorkflowCase(case_id=case_id, transaction=request, required_approvals=required, initial_email=drafted)
        self.repository.save_case(workflow_case)
        return workflow_case

    def refresh_approvals(self, case_id: str) -> WorkflowCase:
        workflow_case = self.repository.get_case(case_id)
        replies = self.email_gateway.collect_replies(workflow_case.initial_email.message_id)
        workflow_case = replace(workflow_case, approval_actions=self._merge_actions(workflow_case.approval_actions, replies))

        if self._has_rejection(workflow_case.approval_actions):
            self.notifier.notify(
                subject=f"[{workflow_case.case_id}] Approval rejected",
                message="One or more approvers rejected the case. Review the thread before any next-step action.",
            )
            self.repository.save_case(workflow_case)
            return workflow_case

        if workflow_case.all_required_approved():
            attachments = self.packager.build_attachment_bundle(workflow_case)
            next_step = self._build_next_step_email(workflow_case, attachments)
            next_step = self.email_gateway.create_draft(next_step)
            workflow_case = replace(workflow_case, next_step_email=next_step)
            self.notifier.notify(
                subject=f"[{workflow_case.case_id}] All approvals collected",
                message="All required approvals are in. Next-step email draft is ready with bundled attachments.",
            )

        self.repository.save_case(workflow_case)
        return workflow_case

    def register_manual_reply(self, case_id: str, action: ApprovalAction) -> WorkflowCase:
        workflow_case = self.repository.get_case(case_id)
        merged = self._merge_actions(workflow_case.approval_actions, [action])
        workflow_case = replace(workflow_case, approval_actions=merged)
        self.repository.save_case(workflow_case)
        return workflow_case

    def _build_initial_email(
        self,
        case_id: str,
        request: TransactionRequest,
        required: list[ApprovalRequirement],
        approver_directory: dict[str, list[str]],
        cc: list[str],
    ) -> EmailMessage:
        effective_amount = request.effective_amount_hkd()
        to = self._resolve_recipients(required, approver_directory)
        required_display = ", ".join(item.display_name for item in required)
        transaction_label = "Withdrawal" if request.transaction_type == TransactionType.WITHDRAWAL else "Deposit"

        body = dedent(
            f"""
            Approval request for client operation.

            Case ID: {case_id}
            Transaction: {transaction_label}
            Client Name: {request.client_name}
            Account No: {request.account_no}
            Beneficiary: {request.beneficiary_name or "N/A"}
            Instruction Type: {request.instruction_type.value}
            Amount ({request.currency}): {request.amount_hkd:,.2f}
            Effective Approval Amount (HKD): {effective_amount:,.2f}
            Requested By: {request.requested_by or "N/A"}
            Purpose: {request.purpose or "N/A"}
            Required Approvers: {required_display}

            Please reply with APPROVED or REJECTED together with your remarks.
            """
        ).strip()

        return EmailMessage(
            subject=f"[Approval Needed][{case_id}] {request.client_name} {transaction_label} {effective_amount:,.2f} HKD",
            body=body,
            to=to,
            cc=cc,
        )

    def _build_next_step_email(self, workflow_case: WorkflowCase, attachments: list[str]) -> EmailMessage:
        request = workflow_case.transaction
        decision_lines = [
            f"- {action.approver_role}: {action.decision.value.upper()} by {action.approver_name} at {action.received_at.isoformat()}"
            for action in workflow_case.approval_actions
        ]
        body = dedent(
            f"""
            All required approvals have been collected. Please proceed with the next operational step.

            Case ID: {workflow_case.case_id}
            Client Name: {request.client_name}
            Account No: {request.account_no}
            Transaction Type: {request.transaction_type.value}
            Effective Amount (HKD): {request.effective_amount_hkd():,.2f}

            Approval Summary:
            {chr(10).join(decision_lines)}

            Attached:
            - Initial approval email
            - All approval replies
            - Attachment manifest
            """
        ).strip()
        return EmailMessage(
            subject=f"[Next Step Ready][{workflow_case.case_id}] {request.client_name}",
            body=body,
            to=[request.requested_by] if request.requested_by else [],
            attachments=attachments,
        )

    def _resolve_recipients(self, required: list[ApprovalRequirement], approver_directory: dict[str, list[str]]) -> list[str]:
        recipients: list[str] = []
        for item in required:
            recipients.extend(approver_directory.get(item.role_code, []))
        return sorted(set(recipients))

    def _merge_actions(self, existing: list[ApprovalAction], incoming: list[ApprovalAction]) -> list[ApprovalAction]:
        latest_by_role = {action.approver_role: action for action in existing}
        for action in incoming:
            latest_by_role[action.approver_role] = action
        return sorted(latest_by_role.values(), key=lambda item: item.received_at)

    def _has_rejection(self, actions: list[ApprovalAction]) -> bool:
        return any(action.decision == ApprovalDecision.REJECTED for action in actions)
