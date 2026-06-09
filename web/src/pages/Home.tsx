import { Link } from "react-router-dom";
import { ArrowRight, BadgeCheck, Clock3, ScrollText } from "lucide-react";

import { listCases } from "@/lib/api";
import type { WorkflowCase } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect, useMemo, useState } from "react";

function StatusPill({ status }: { status: WorkflowCase["status"] }) {
  const style =
    status === "approved"
      ? "bg-mint-500/15 text-mint-500 border-mint-500/30"
      : status === "rejected"
        ? "bg-risk-500/15 text-risk-500 border-risk-500/30"
        : "bg-accent-500/10 text-accent-500 border-accent-500/25";

  const label = status === "approved" ? "已通过" : status === "rejected" ? "已拒绝" : "待审批";

  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs", style)}>{label}</span>;
}

export default function Home() {
  const [cases, setCases] = useState<WorkflowCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    listCases()
      .then((data) => {
        if (!mounted) return;
        setCases(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const stats = useMemo(() => {
    const pending = cases.filter((item) => item.status === "pending").length;
    const approved = cases.filter((item) => item.status === "approved").length;
    const rejected = cases.filter((item) => item.status === "rejected").length;
    return { pending, approved, rejected, total: cases.length };
  }, [cases]);

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-white/10 bg-ink-900/55 p-6 shadow-paper backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-xl space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-ledger-200">
              <span className="h-1.5 w-1.5 rounded-full bg-accent-500" />
              审批邮件工作台（演示）
            </div>
            <h1 className="font-serif text-2xl tracking-wide text-ledger-100">从邮件线程里把流程“拎出来”</h1>
            <p className="text-sm leading-relaxed text-ledger-300">
              先用 Web 工作台把 Case、模板和审批状态跑通；Outlook 会话同步将在接入 Outlook COM / Microsoft Graph 后启用。
            </p>
          </div>
          <Link
            to="/cases"
            className="group inline-flex items-center gap-2 rounded-2xl border border-accent-500/35 bg-accent-500/12 px-4 py-2 text-sm text-ledger-100 shadow-glow transition hover:bg-accent-500/18"
          >
            进入 Case 列表
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-ink-900/40 p-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="text-xs text-ledger-300">待审批</div>
            <Clock3 className="h-4 w-4 text-accent-500/80" />
          </div>
          <div className="mt-2 font-serif text-2xl text-ledger-100">{stats.pending}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-ink-900/40 p-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="text-xs text-ledger-300">已通过</div>
            <BadgeCheck className="h-4 w-4 text-mint-500/80" />
          </div>
          <div className="mt-2 font-serif text-2xl text-ledger-100">{stats.approved}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-ink-900/40 p-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="text-xs text-ledger-300">已拒绝</div>
            <BadgeCheck className="h-4 w-4 text-risk-500/80" />
          </div>
          <div className="mt-2 font-serif text-2xl text-ledger-100">{stats.rejected}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-ink-900/40 p-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="text-xs text-ledger-300">总 Case</div>
            <ScrollText className="h-4 w-4 text-ledger-300" />
          </div>
          <div className="mt-2 font-serif text-2xl text-ledger-100">{stats.total}</div>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-ink-900/50 p-6 shadow-paper backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="font-serif text-lg text-ledger-100">最近 Case</div>
            <div className="mt-1 text-xs text-ledger-300">按更新时间排序，点击进入详情</div>
          </div>
          <Link to="/cases" className="text-xs text-ledger-200 underline decoration-white/20 underline-offset-4 hover:text-ledger-100">
            查看全部
          </Link>
        </div>
        <div className="mt-4 space-y-2">
          {loading ? (
            <div className="grid gap-2">
              {Array.from({ length: 3 }).map((_, idx) => (
                <div key={idx} className="h-14 animate-pulse rounded-2xl bg-white/5" />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-risk-500/30 bg-risk-500/10 p-4 text-sm text-risk-500">{error}</div>
          ) : cases.length === 0 ? (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-ledger-300">
              还没有 Case。去“流程 Case”里创建一个演示 Case。
            </div>
          ) : (
            cases.slice(0, 5).map((item) => (
              <Link
                key={item.caseId}
                to={`/cases/${item.caseId}`}
                className="group flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/4 px-4 py-3 transition hover:border-white/15 hover:bg-white/6"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm text-ledger-100">
                    {item.transaction.client_name} · {item.transaction.transaction_type.toUpperCase()} · {item.transaction.amount_hkd.toLocaleString()} HKD
                  </div>
                  <div className="mt-1 truncate text-xs text-ledger-300">
                    {item.caseId} · {item.transaction.account_no} · {item.transaction.instruction_type}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusPill status={item.status} />
                  <ArrowRight className="h-4 w-4 text-ledger-400 transition group-hover:translate-x-0.5 group-hover:text-ledger-200" />
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
