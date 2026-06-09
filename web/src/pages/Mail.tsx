import { Link } from "react-router-dom";
import { MailOpen, ScrollText } from "lucide-react";

export default function Mail() {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-white/10 bg-ink-900/55 p-6 shadow-paper backdrop-blur">
        <div className="flex items-start justify-between gap-6">
          <div className="space-y-2">
            <h1 className="font-serif text-2xl text-ledger-100">邮件中心</h1>
            <p className="max-w-2xl text-sm leading-relaxed text-ledger-300">
              这里会展示 Outlook 的 To/CC 邮件列表、会话线程与附件信息，并支持把邮件关联到 Case。当前版本先把“流程
              Case + 模板管理”做成可用的 Web 工作台，Outlook 同步会在接入 Outlook COM / Microsoft Graph 后上线。
            </p>
          </div>
          <MailOpen className="h-6 w-6 text-ledger-300" />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-3xl border border-white/10 bg-ink-900/45 p-6 shadow-paper backdrop-blur">
          <div className="text-sm text-ledger-100">你希望在邮件中心看到的核心能力</div>
          <ul className="mt-3 space-y-2 text-sm text-ledger-300">
            <li>按 To / CC 自动分流：To 进入“待处理”，CC 进入“仅关注”</li>
            <li>按会话线程聚合：同一审批线程可展开所有回信并提取最新审批结果</li>
            <li>自动识别 APPROVED / REJECTED 关键字与审批人身份</li>
            <li>一键创建/关联 Case：把邮件变成可追踪的流程对象</li>
          </ul>
        </div>
        <div className="rounded-3xl border border-white/10 bg-ink-900/45 p-6 shadow-paper backdrop-blur">
          <div className="text-sm text-ledger-100">现在可以先做什么</div>
          <div className="mt-3 space-y-3 text-sm text-ledger-300">
            <div>1) 在“流程 Case”里创建演示 Case，体验审批进度与下一步草稿生成。</div>
            <div>2) 在“模板管理”里编辑模板，预览不同客户与金额下的渲染效果。</div>
            <div className="pt-2">
              <Link
                to="/cases"
                className="inline-flex items-center gap-2 rounded-2xl border border-accent-500/35 bg-accent-500/12 px-4 py-2 text-sm text-ledger-100 shadow-glow transition hover:bg-accent-500/18"
              >
                <ScrollText className="h-4 w-4" />
                去创建演示 Case
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

