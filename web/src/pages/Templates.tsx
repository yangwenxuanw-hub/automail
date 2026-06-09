import { useEffect, useMemo, useState } from "react";
import { Save, Sparkles } from "lucide-react";

import type { TemplateRecord } from "@/lib/types";
import { cn } from "@/lib/utils";
import { getTemplate, listTemplates, previewTemplate, saveTemplate } from "@/lib/api";

const sampleTransaction = {
  clientName: "ABC Capital Client",
  accountNo: "AC-778899",
  transactionType: "withdrawal",
  accountCategory: "corporate_or_other",
  amountHkd: 12_500_000,
  currency: "HKD",
  instructionType: "si_fop_dvp",
  marketValueHkd: 13_000_000,
  settlementAmountHkd: 12_400_000,
  hasDebitCashOrStockBeforeOrAfter: true,
  isMarginAccountWithDebitBalance: false,
  beneficiaryName: "ABC Capital Client",
  requestedBy: "ops.requester@company.com",
  purpose: "Client securities withdrawal",
};

export default function Templates() {
  const [templates, setTemplates] = useState<TemplateRecord[]>([]);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [active, setActive] = useState<TemplateRecord | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<string>("");
  const [busyPreview, setBusyPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadList = () => {
    listTemplates()
      .then((data) => {
        setTemplates(data);
        if (!activeKey && data.length > 0) setActiveKey(data[0].key);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  };

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    if (!activeKey) return;
    getTemplate(activeKey)
      .then((data) => {
        setActive(data);
        setContent(data.versions?.[0]?.content ?? "");
        setError(null);
        setPreview("");
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [activeKey]);

  const variableHints = useMemo(
    () => [
      "{{caseId}}",
      "{{transaction.client_name}}",
      "{{transaction.account_no}}",
      "{{transaction.transaction_type}}",
      "{{transaction.instruction_type}}",
      "{{effectiveAmountHkd}}",
      "{{requiredApprovers}}",
      "{{approvalSummary}}",
    ],
    []
  );

  const runPreview = async () => {
    if (!activeKey) return;
    setBusyPreview(true);
    try {
      const res = await previewTemplate(activeKey, { transaction: sampleTransaction, content });
      setPreview(res.rendered);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyPreview(false);
    }
  };

  const doSave = async () => {
    if (!activeKey || !active) return;
    setSaving(true);
    try {
      const saved = await saveTemplate(activeKey, { name: active.name, content });
      setActive(saved);
      setTemplates((prev) => prev.map((item) => (item.key === saved.key ? saved : item)));
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
      <aside className="rounded-3xl border border-white/10 bg-ink-900/55 p-5 shadow-paper backdrop-blur">
        <div className="font-serif text-lg text-ledger-100">模板管理</div>
        <div className="mt-1 text-xs text-ledger-300">编辑并保存各环节邮件模板；右侧可预览渲染效果</div>
        <div className="mt-5 space-y-2">
          {templates.map((tpl) => (
            <button
              key={tpl.key}
              type="button"
              onClick={() => setActiveKey(tpl.key)}
              className={cn(
                "w-full rounded-2xl border px-4 py-3 text-left transition",
                activeKey === tpl.key
                  ? "border-accent-500/35 bg-accent-500/10 text-ledger-100"
                  : "border-white/10 bg-white/5 text-ledger-200 hover:bg-white/8"
              )}
            >
              <div className="text-sm">{tpl.name}</div>
              <div className="mt-1 text-xs text-ledger-400">{tpl.key}</div>
            </button>
          ))}
        </div>
      </aside>

      <section className="space-y-6">
        {error ? <div className="rounded-3xl border border-risk-500/30 bg-risk-500/10 p-5 text-sm text-risk-500">{error}</div> : null}

        <div className="rounded-3xl border border-white/10 bg-ink-900/55 p-6 shadow-paper backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="font-serif text-lg text-ledger-100">{active?.name ?? "选择一个模板"}</div>
              <div className="mt-1 text-xs text-ledger-300">支持变量：{variableHints.join(" / ")}</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={runPreview}
                disabled={!activeKey || busyPreview}
                className={cn(
                  "inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-ledger-200 transition hover:bg-white/10",
                  busyPreview && "cursor-not-allowed opacity-60"
                )}
              >
                <Sparkles className="h-4 w-4" />
                预览渲染
              </button>
              <button
                type="button"
                onClick={doSave}
                disabled={!activeKey || saving}
                className={cn(
                  "inline-flex items-center gap-2 rounded-2xl border border-accent-500/35 bg-accent-500/12 px-4 py-2 text-sm text-ledger-100 shadow-glow transition hover:bg-accent-500/18",
                  saving && "cursor-not-allowed opacity-60"
                )}
              >
                <Save className="h-4 w-4" />
                保存版本
              </button>
            </div>
          </div>

          <div className="mt-5 grid gap-6 xl:grid-cols-2">
            <div className="space-y-2">
              <div className="text-xs text-ledger-300">模板内容</div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="h-[420px] w-full resize-none rounded-2xl border border-white/10 bg-black/25 p-4 text-xs leading-relaxed text-ledger-100 outline-none placeholder:text-ledger-500 focus:border-accent-500/40"
              />
            </div>
            <div className="space-y-2">
              <div className="text-xs text-ledger-300">渲染预览（样例交易）</div>
              <div className="h-[420px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs leading-relaxed text-ledger-200">
                {preview ? <pre className="whitespace-pre-wrap font-sans">{preview}</pre> : <div className="text-ledger-400">点击“预览渲染”生成预览。</div>}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

