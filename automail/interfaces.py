from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ApprovalAction, EmailMessage, WorkflowCase


class EmailGateway(ABC):
    """Abstract Outlook/Graph adapter."""

    @abstractmethod
    def create_draft(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError

    @abstractmethod
    def send(self, email: EmailMessage) -> EmailMessage:
        raise NotImplementedError

    @abstractmethod
    def collect_replies(self, thread_id: str) -> list[ApprovalAction]:
        raise NotImplementedError


class Notifier(ABC):
    @abstractmethod
    def notify(self, subject: str, message: str) -> None:
        raise NotImplementedError


class CaseRepository(ABC):
    @abstractmethod
    def save_case(self, workflow_case: WorkflowCase) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_case(self, case_id: str) -> WorkflowCase:
        raise NotImplementedError

    @abstractmethod
    def list_cases(self) -> list[WorkflowCase]:
        raise NotImplementedError


class AttachmentPackager(ABC):
    @abstractmethod
    def build_attachment_bundle(self, workflow_case: WorkflowCase) -> list[str]:
        raise NotImplementedError
