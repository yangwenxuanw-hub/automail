from __future__ import annotations

import os
from typing import Any

from ..interfaces import EmailGateway
from ..models import ApprovalAction, EmailMessage


class OutlookComGateway(EmailGateway):
    def __init__(self) -> None:
        import win32com.client  # type: ignore

        self._win32 = win32com.client
        self._outlook = self._win32.Dispatch("Outlook.Application")
        self._namespace = self._outlook.GetNamespace("MAPI")

    def create_draft(self, email: EmailMessage) -> EmailMessage:
        item = self._outlook.CreateItem(0)
        item.Subject = email.subject
        item.Body = email.body
        item.To = "; ".join(email.to)
        item.CC = "; ".join(email.cc)

        if email.attachments:
            for path in email.attachments:
                if os.path.exists(path):
                    item.Attachments.Add(os.path.abspath(path))

        item.Save()

        message_id = ""
        try:
            message_id = str(item.EntryID)
        except Exception:
            message_id = email.message_id

        return EmailMessage(
            subject=email.subject,
            body=email.body,
            to=email.to,
            cc=email.cc,
            attachments=email.attachments,
            message_id=message_id,
        )

    def send(self, email: EmailMessage) -> EmailMessage:
        item = self._outlook.CreateItem(0)
        item.Subject = email.subject
        item.Body = email.body
        item.To = "; ".join(email.to)
        item.CC = "; ".join(email.cc)

        if email.attachments:
            for path in email.attachments:
                if os.path.exists(path):
                    item.Attachments.Add(os.path.abspath(path))

        item.Send()

        message_id = ""
        try:
            message_id = str(item.EntryID)
        except Exception:
            message_id = email.message_id

        return EmailMessage(
            subject=email.subject,
            body=email.body,
            to=email.to,
            cc=email.cc,
            attachments=email.attachments,
            message_id=message_id,
        )

    def collect_replies(self, thread_id: str) -> list[ApprovalAction]:
        raise NotImplementedError
