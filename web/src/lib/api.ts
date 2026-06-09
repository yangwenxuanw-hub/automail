import type { TemplateRecord, WorkflowCase } from "@/lib/types";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function listCases(): Promise<WorkflowCase[]> {
  return requestJson("/api/cases");
}

export async function getCase(caseId: string): Promise<WorkflowCase> {
  return requestJson(`/api/cases/${caseId}`);
}

export async function createCase(payload: {
  transaction: {
    clientName: string;
    accountNo: string;
    transactionType: string;
    accountCategory: string;
    amountHkd: number;
    currency?: string;
    instructionType?: string;
    marketValueHkd?: number | null;
    settlementAmountHkd?: number | null;
    hasDebitCashOrStockBeforeOrAfter?: boolean;
    isMarginAccountWithDebitBalance?: boolean;
    beneficiaryName?: string;
    requestedBy?: string;
    purpose?: string;
  };
  cc?: string[];
}): Promise<WorkflowCase> {
  return requestJson("/api/cases", { method: "POST", body: JSON.stringify(payload) });
}

export async function refreshCase(caseId: string): Promise<WorkflowCase> {
  return requestJson(`/api/cases/${caseId}/refresh`, { method: "POST" });
}

export async function seedDemoApprovals(caseId: string): Promise<WorkflowCase> {
  return requestJson(`/api/cases/${caseId}/seed-demo-approvals`, { method: "POST" });
}

export async function listTemplates(): Promise<TemplateRecord[]> {
  return requestJson("/api/templates");
}

export async function getTemplate(key: string): Promise<TemplateRecord> {
  return requestJson(`/api/templates/${key}`);
}

export async function saveTemplate(key: string, payload: { name: string; content: string }): Promise<TemplateRecord> {
  return requestJson(`/api/templates/${key}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function previewTemplate(
  key: string,
  payload: { transaction: any; content?: string }
): Promise<{ rendered: string }> {
  return requestJson(`/api/templates/${key}/preview`, { method: "POST", body: JSON.stringify(payload) });
}

