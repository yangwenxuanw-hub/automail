from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable

from ..interfaces import AttachmentPackager, CaseRepository, EmailGateway, Notifier
from ..models import ApprovalAction, EmailMessage, WorkflowCase


class InMemoryEmailGateway(EmailGateway):
    def __init__(self, seed_replies: dict[str, list[ApprovalAction]] | None = None) -> None:
        self.drafts: list[EmailMessage] = []
        self.sent_messages: list[EmailMessage] = []
        self.seed_replies = seed_replies or {}

    def create_draft(self, email: EmailMessage) -> EmailMessage:
        self.drafts.append(email)
        return email

    def send(self, email: EmailMessage) -> EmailMessage:
        self.sent_messages.append(email)
        return email

    def collect_replies(self, thread_id: str) -> list[ApprovalAction]:
        return list(self.seed_replies.get(thread_id, []))


class ConsoleNotifier(Notifier):
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def notify(self, subject: str, message: str) -> None:
        self.events.append((subject, message))
        print(f"[NOTIFY] {subject}\n{message}\n")


class InMemoryCaseRepository(CaseRepository):
    def __init__(self) -> None:
        self._cases: dict[str, WorkflowCase] = {}

    def save_case(self, workflow_case: WorkflowCase) -> None:
        self._cases[workflow_case.case_id] = replace(workflow_case)

    def get_case(self, case_id: str) -> WorkflowCase:
        return self._cases[case_id]

    def list_cases(self) -> list[WorkflowCase]:
        return list(self._cases.values())


class LocalFileAttachmentPackager(AttachmentPackager):
    def __init__(self, output_dir: str | Path = "outbox") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_attachment_bundle(self, workflow_case: WorkflowCase) -> list[str]:
        base_dir = self.output_dir / workflow_case.case_id
        base_dir.mkdir(parents=True, exist_ok=True)

        generated_files: list[Path] = []
        initial_file = base_dir / "initial_email.txt"
        initial_file.write_text(
            f"Subject: {workflow_case.initial_email.subject}\n\n{workflow_case.initial_email.body}",
            encoding="utf-8",
        )
        generated_files.append(initial_file)

        for index, action in enumerate(workflow_case.approval_actions, start=1):
            reply_file = base_dir / f"approval_reply_{index}_{action.approver_role.lower()}.txt"
            reply_file.write_text(
                "\n".join(
                    [
                        f"Approver Role: {action.approver_role}",
                        f"Approver Name: {action.approver_name}",
                        f"Approver Email: {action.approver_email}",
                        f"Decision: {action.decision.value}",
                        f"Received At: {action.received_at.isoformat()}",
                        f"Comment: {action.comment}",
                        "",
                        action.raw_content,
                    ]
                ),
                encoding="utf-8",
            )
            generated_files.append(reply_file)

        manifest = base_dir / "attachment_manifest.txt"
        manifest.write_text("\n".join(str(path) for path in generated_files), encoding="utf-8")
        generated_files.append(manifest)
        return [str(path) for path in generated_files]


def seed_reply_map(thread_id: str, actions: Iterable[ApprovalAction]) -> dict[str, list[ApprovalAction]]:
    return {thread_id: list(actions)}
