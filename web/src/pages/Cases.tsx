import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Plus, RefreshCcw, Search } from "lucide-react";

import type { WorkflowCase } from "@/lib/types";
import { cn } from "@/lib/utils";
import { createCase, listCases } from "@/lib/api";

function StatusDot({ status }: { status: WorkflowCase["status"] }) {
  const cls =
    status === "approved"
      ? "bg-mint-500"
      : status === "rejected"
        ? "bg-risk-500"
        : "bg-accent-500";
  return <span className={cn("h-2.5 w-2.5 rounded-full", cls)} />;
}

export default function Cases() {
  const [items, setItems] = useState<WorkflowCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setLoading(true);
    listCases()
      .then((data) => {
        setItems(data);
        setError(null);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => {
      const t = item.transaction;
      return (
        item.caseId.toLowerCase().includes(q) ||
        t.client_name.toLowerCase().includes(q) ||
        t.account_no.toLowerCase().includes(q) ||
        t.transaction_type.toLowerCase().includes(q)
      );
    });
  }, [items, query]);

  const createDemoCase = async () => {
    setCreating(true);
    try {
      const created = await createCase({
        transaction: {
          clientName: "ABC Capital Client",
          accountNo: "AC-778899",
          transactionType: "withdrawal",
          accountCategory: "corporate_or_other",
          amountHkd: 12_500_000,
          instructionType: "si_fop_dvp",
          marketValueHkd: 13_000_000,
          settlementAmountHkd: 12_400_000,
          hasDebitCashOrStockBeforeOrAfter: true,
          beneficiaryName: "ABC Capital Client",
          requestedBy: "ops.requester@company.com",
          purpose: "Client securities withdrawal",
        },
        cc: ["ops.control@company.com"],
      });
      setItems((prev) => [created, ...prev]);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-white/10 bg-ink-900/55 p-6 shadow-paper backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="space-y-2">
            <h1 className="font-serif text-2xl text-ledger-100">流程 Case</h1>
            <p className="max-w-2xl text-sm text-ledger-300">
              这里展示由工作流引擎生成与维护的 Case。当前为演示模式：点击创建演示 Case，然后在详情页刷新审批或一键补齐审批回信。
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={load}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-ledger-200 transition hover:bg-white/10"
            >
              <RefreshCcw className="h-4 w-4" />
              刷新
            </button>
            <button
              type="button"
              onClick={createDemoCase}
              disabled={creating}
              className={cn(
                "inline-flex items-center gap-2 rounded-2xl border border-accent-500/35 bg-accent-500/12 px-4 py-2 text-sm text-ledger-100 shadow-glow transition hover:bg-accent-500/18",
                creating && "cursor-not-allowed opacity-60"
              )}
            >
              <Plus className="h-4 w-4" />
              创建演示 Case
            </button>
          </div>
        </div>
        <div className="mt-5 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
          <Search className="h-4 w-4 text-ledger-300" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索 caseId / 客户 / 账号 / 交易类型"
            className="w-full bg-transparent text-sm text-ledger-100 outline-none placeholder:text-ledger-400"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid gap-3">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div key={idx} className="h-16 animate-pulse rounded-3xl bg-white/5" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-3xl border border-risk-500/30 bg-risk-500/10 p-5 text-sm text-risk-500">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-ledger-300">
          没有匹配的 Case。你可以先创建一个演示 Case。
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((item) => (
            <Link
              key={item.caseId}
              to={`/cases/${item.caseId}`}
              className="group flex items-center justify-between gap-4 rounded-3xl border border-white/10 bg-ink-900/40 px-5 py-4 shadow-paper/40 backdrop-blur transition hover:border-white/15 hover:bg-ink-900/55"
            >
              <div className="flex min-w-0 items-start gap-3">
                <StatusDot status={item.status} />
                <div className="min-w-0">
                  <div className="truncate text-sm text-ledger-100">
                    {item.transaction.client_name} · {item.transaction.transaction_type.toUpperCase()} ·{" "}
                    {item.transaction.amount_hkd.toLocaleString()} HKD
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ledger-300">
                    <span>{item.caseId}</span>
                    <span className="text-ledger-400">•</span>
                    <span>{item.transaction.account_no}</span>
                    <span className="text-ledger-400">•</span>
                    <span>{item.transaction.instruction_type}</span>
                  </div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-ledger-400 transition group-hover:translate-x-0.5 group-hover:text-ledger-200" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

