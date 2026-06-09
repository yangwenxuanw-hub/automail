from __future__ import annotations

from dataclasses import dataclass

from .models import AccountCategory, ApprovalRequirement, TransactionRequest, TransactionType


CO_MAKER_CHECKER = [
    ApprovalRequirement("CO_MAKER", "CO Maker", "Low-tier threshold approval"),
    ApprovalRequirement("CHECKER", "Checker", "Low-tier threshold approval"),
]

HCO_HF = [
    ApprovalRequirement("HCO", "HCO", "Mid-tier threshold approval"),
    ApprovalRequirement("HF", "HF", "Mid-tier threshold approval"),
]

HCO_HF_RO = [
    ApprovalRequirement("HCO", "HCO", "High-tier threshold approval"),
    ApprovalRequirement("HF", "HF", "High-tier threshold approval"),
    ApprovalRequirement("RO_OR_SUPERVISOR", "RO or Supervisor", "High-tier threshold approval"),
]

RISK_MANAGEMENT = ApprovalRequirement(
    "RISK_MANAGEMENT",
    "Risk Management",
    "Additional risk approval is required for debit or margin scenarios",
)


@dataclass(frozen=True, slots=True)
class ThresholdRule:
    upper_bound_hkd: float | None
    requirements: list[ApprovalRequirement]

    def matches(self, amount_hkd: float) -> bool:
        return self.upper_bound_hkd is None or amount_hkd <= self.upper_bound_hkd


WITHDRAWAL_RULES = {
    AccountCategory.PERSONAL_OR_JOINT: [
        ThresholdRule(5_000_000, CO_MAKER_CHECKER),
        ThresholdRule(10_000_000, HCO_HF),
        ThresholdRule(None, HCO_HF_RO),
    ],
    AccountCategory.CORPORATE_OR_OTHER: [
        ThresholdRule(10_000_000, CO_MAKER_CHECKER),
        ThresholdRule(50_000_000, HCO_HF),
        ThresholdRule(None, HCO_HF_RO),
    ],
}

DEPOSIT_RULES = {
    AccountCategory.PERSONAL_OR_JOINT: [
        ThresholdRule(10_000_000, CO_MAKER_CHECKER),
        ThresholdRule(50_000_000, HCO_HF),
        ThresholdRule(None, HCO_HF_RO),
    ],
    AccountCategory.CORPORATE_OR_OTHER: [
        ThresholdRule(50_000_000, CO_MAKER_CHECKER),
        ThresholdRule(100_000_000, HCO_HF),
        ThresholdRule(None, HCO_HF_RO),
    ],
}


class ApprovalPolicyEngine:
    """Translates transaction data into approval requirements."""

    def determine_requirements(self, request: TransactionRequest) -> list[ApprovalRequirement]:
        rules = WITHDRAWAL_RULES if request.transaction_type == TransactionType.WITHDRAWAL else DEPOSIT_RULES
        effective_amount = request.effective_amount_hkd()
        selected: list[ApprovalRequirement] = []

        for rule in rules[request.account_category]:
            if rule.matches(effective_amount):
                selected = [ApprovalRequirement(item.role_code, item.display_name, item.reason, item.mandatory) for item in rule.requirements]
                break

        if request.transaction_type == TransactionType.WITHDRAWAL and (
            request.has_debit_cash_or_stock_before_or_after or request.is_margin_account_with_debit_balance
        ):
            selected.append(
                ApprovalRequirement(
                    RISK_MANAGEMENT.role_code,
                    RISK_MANAGEMENT.display_name,
                    RISK_MANAGEMENT.reason,
                    RISK_MANAGEMENT.mandatory,
                )
            )

        return selected
