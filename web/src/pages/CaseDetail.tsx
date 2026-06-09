import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BadgeCheck, RefreshCcw, Sparkles } from "lucide-react";

import type { WorkflowCase } from "@/lib/types";
import { cn } from "@/lib/utils";
import { getCase, refreshCase, seedDemoApprovals } from "@/lib/api";

function DecisionPill({ decision }: { decision: string }) {
  const style =
    decision === "approved"
      ? "bg-mint-500/15 text-mint-500 border-mint-500/30"
      : decision === "rejected"
        ? "bg-risk-500/15 text-risk-500 border-risk-500/30"
        : "bg-accent-500/10 text-accent-500 border-accent-500/25";
  const label = decision === "approved" ? "APPROVED" : decision === "rejected" ? "REJECTED" : "PENDING";
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[11px]", style)}>{label}</span>;
}

export default function CaseDetail() {
  const params = useParams();
  const caseId = params.id ?? "";
  const [item, setItem] = useState<WorkflowCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<null | "refresh" | "seed">(null);

  const load = () => {
    setLoading(true);
    getCase(caseId)
      .then((data) => {
        setItem(data);
        setError(null);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!caseId) return;
    load();
  }, [caseId]);

  const requiredByRole = useMemo(() => {
    if (!item) return [];
    return item.requiredApprovals.map((req) => {
      const action = item.approvalActions
        .slice()
        .reverse()
        .find((a) => a.approverRole === req.role_code);
      return { req, action };
    });
  }, [item]);

  const doRefresh = async () => {
    setBusy("refresh");
    try {
      const updated = await refreshCase(caseId);
      setItem(updated);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  };

  const doSeed = async () => {
    setBusy("seed");
    try {
      const updated = await seedDemoApprovals(caseId);
      setItem(updated);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return <div className="h-64 animate-pulse rounded-3xl bg-white/5" />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/cases" className="inline-flex items-center gap-2 text-sm text-ledger-200 hover:text-ledger-100">
          <ArrowLeft className="h-4 w-4" />
          返回 Case 列表
        </Link>
        <div className="rounded-3xl border border-risk-500/30 bg-risk-500/10 p-5 text-sm text-risk-500">{error}</div>
      </div>
    );
  }

  if (!item) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link to="/cases" className="inline-flex items-center gap-2 text-sm text-ledger-200 hover:text-ledger-100">
          <ArrowLeft className="h-4 w-4" />
          返回 Case 列表
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={doRefresh}
            disabled={busy !== null}
            className={cn(
              "inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-ledger-200 transition hover:bg-white/10",
              busy !== null && "cursor-not-allowed opacity-60"
            )}
          >
            <RefreshCcw className="h-4 w-4" />
            刷新审批
          </button>
          <button
            type="button"
            onClick={doSeed}
            disabled={busy !== null}
            className={cn(
              "inline-flex items-center gap-2 rounded-2xl border border-accent-500/35 bg-accent-500/12 px-4 py-2 text-sm text-ledger-100 shadow-glow transition hover:bg-accent-500/18",
              busy !== null && "cursor-not-allowed opacity-60"
            )}
          >
            <Sparkles className="h-4 w-4" />
            演示：补齐审批回信
          </button>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-ink-900/55 p-6 shadow-paper backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="space-y-2">
            <div className="text-xs text-ledger-300">Case ID</div>
            <div className="font-serif text-2xl text-ledger-100">{item.caseId}</div>
            <div className="text-sm text-ledger-300">
              {item.transaction.client_name} · {item.transaction.transaction_type.toUpperCase()} ·{" "}
              {item.transaction.amount_hkd.toLocaleString()} HKD · {item.transaction.account_no}
            </div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-ledger-300">
            <div className="flex items-center justify-between gap-3">
              <div className="text-ledger-200">状态</div>
              <DecisionPill decision={item.status} />
            </div>
            <div className="mt-2 flex items-center justify-between gap-3">
              <div>更新时间</div>
              <div className="text-ledger-200">{new Date(item.updatedAt).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-3xl border border-white/10 bg-ink-900/45 p-6 shadow-paper backdrop-blur">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="font-serif text-lg text-ledger-100">审批进度</div>
              <div className="mt-1 text-xs text-ledger-300">按规则生成的必需审批角色与最新回信</div>
            </div>
            <BadgeCheck className="h-5 w-5 text-ledger-300" />
          </div>
          <div className="mt-4 space-y-3">
            {requiredByRole.map(({ req, action }) => (
              <div key={req.role_code} className="rounded-2xl border border-white/10 bg-white/4 px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm text-ledger-100">
                      {req.display_name} <span className="text-xs text-ledger-400">({req.role_code})</span>
                    </div>
                    <div className="mt-1 text-xs text-ledger-300">{req.reason}</div>
                  </div>
                  <DecisionPill decision={action?.decision ?? "pending"} />
                </div>
                {action ? (
                  <div className="mt-3 grid gap-1 text-xs text-ledger-300">
                    <div className="text-ledger-200">{action.approverName}</div>
                    <div>{new Date(action.receivedAt).toLocaleString()}</div>
                    {action.rawContent ? <div className="rounded-xl bg-black/30 p-3 font-mono text-[11px] text-ledger-200">{action.rawContent}</div> : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-3xl border border-white/10 bg-ink-900/45 p-6 shadow-paper backdrop-blur">
            <div className="font-serif text-lg text-ledger-100">初始审批邮件草稿</div>
            <div className="mt-2 rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-ledger-200">
              <div className="font-medium text-ledger-100">{item.initialEmailSubject}</div>
              <pre className="mt-3 whitespace-pre-wrap font-sans text-xs leading-relaxed text-ledger-200">{item.initialEmailBody}</pre>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-ink-900/45 p-6 shadow-paper backdrop-blur">
            <div className="font-serif text-lg text-ledger-100">下一步邮件草稿</div>
            {item.nextStepEmailSubject ? (
              <div className="mt-2 rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-ledger-200">
                <div className="font-medium text-ledger-100">{item.nextStepEmailSubject}</div>
                <pre className="mt-3 whitespace-pre-wrap font-sans text-xs leading-relaxed text-ledger-200">{item.nextStepEmailBody}</pre>
              </div>
            ) : (
              <div className="mt-2 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-ledger-300">
                还未生成。等全部必需审批通过后，刷新审批会自动生成下一步草稿与附件包。
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

