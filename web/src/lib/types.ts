export type ApprovalDecision = "pending" | "approved" | "rejected";

export type TransactionType = "withdrawal" | "deposit";
export type AccountCategory = "personal_or_joint" | "corporate_or_other";
export type AssetInstructionType = "cash" | "si_fop_dvp";

export interface TransactionRequest {
  client_name: string;
  account_no: string;
  transaction_type: TransactionType;
  account_category: AccountCategory;
  amount_hkd: number;
  currency: string;
  instruction_type: AssetInstructionType;
  market_value_hkd?: number | null;
  settlement_amount_hkd?: number | null;
  has_debit_cash_or_stock_before_or_after: boolean;
  is_margin_account_with_debit_balance: boolean;
  beneficiary_name: string;
  requested_by: string;
  purpose: string;
  extra_context: Record<string, unknown>;
}

export interface ApprovalRequirement {
  role_code: string;
  display_name: string;
  reason: string;
  mandatory: boolean;
}

export interface ApprovalAction {
  approverRole: string;
  approverName: string;
  approverEmail: string;
  decision: ApprovalDecision;
  receivedAt: string;
  messageId: string;
  comment?: string;
  rawContent?: string;
}

export type WorkflowCaseStatus = "pending" | "approved" | "rejected";

export interface WorkflowCase {
  caseId: string;
  transaction: TransactionRequest;
  requiredApprovals: ApprovalRequirement[];
  approvalActions: ApprovalAction[];
  initialEmailSubject: string;
  initialEmailBody: string;
  nextStepEmailSubject?: string | null;
  nextStepEmailBody?: string | null;
  createdAt: string;
  updatedAt: string;
  status: WorkflowCaseStatus;
}

export interface TemplateVersion {
  id: string;
  content: string;
  created_at: string;
}

export interface TemplateRecord {
  key: string;
  name: string;
  versions: TemplateVersion[];
}
