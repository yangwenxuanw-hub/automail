from __future__ import annotations

from ..interfaces import EmailGateway
from ..models import ApprovalAction, EmailMessage


class OutlookComGatewayStub(EmailGateway):
    """
    Placeholder for a future Windows-only Outlook COM adapter.

    Expected future responsibilities:
    - Create draft emails in a local Outlook profile.
    - Read conversation threads and normalize replies into ApprovalAction.
    - Save attachments as .msg or .eml files.
    """

    def create_draft(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError("Implement with win32com on a Windows host with Outlook installed.")

    def send(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError("Implement with win32com on a Windows host with Outlook installed.")

    def collect_replies(self, thread_id: str) -> list[ApprovalAction]:
        raise NotImplementedError("Implement with Outlook conversation APIs.")


class MicrosoftGraphGatewayStub(EmailGateway):
    """
    Placeholder for a future Microsoft Graph adapter.

    Expected future responsibilities:
    - Send mails via /sendMail or create drafts in a shared mailbox.
    - Poll or subscribe to mailbox replies via webhook/subscription.
    - Download replies and attachments by message id.
    """

    def create_draft(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError("Implement with Microsoft Graph create draft API.")

    def send(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError("Implement with Microsoft Graph sendMail API.")

    def collect_replies(self, thread_id: str) -> list[ApprovalAction]:
        raise NotImplementedError("Implement with Microsoft Graph message query or webhook.")
