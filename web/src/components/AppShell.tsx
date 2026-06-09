import { NavLink } from "react-router-dom";
import { LayoutGrid, Mail, PanelsTopLeft, ScrollText } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/useTheme";

const navItems = [
  { to: "/", label: "总览", icon: LayoutGrid },
  { to: "/mail", label: "邮件中心", icon: Mail },
  { to: "/cases", label: "流程 Case", icon: ScrollText },
  { to: "/templates", label: "模板管理", icon: PanelsTopLeft },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-[1400px] gap-6 px-5 py-6">
        <aside className="hidden w-64 shrink-0 lg:block">
          <div className="sticky top-6 space-y-4">
            <div className="rounded-2xl border border-white/10 bg-ink-900/55 px-4 py-4 shadow-paper backdrop-blur">
              <div className="flex items-baseline justify-between gap-3">
                <div>
                  <div className="font-serif text-lg tracking-wide text-ledger-100">AutoMail</div>
                  <div className="text-xs text-ledger-300">审批邮件工作台</div>
                </div>
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-ledger-200 transition hover:bg-white/10"
                >
                  {isDark ? "暗色" : "亮色"}
                </button>
              </div>
              <div className="mt-4 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />
              <nav className="mt-4 grid gap-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      cn(
                        "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-ledger-200 transition",
                        "hover:bg-white/7 hover:text-ledger-100",
                        isActive && "bg-white/10 text-ledger-100 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.12)]"
                      )
                    }
                    end={item.to === "/"}
                  >
                    <item.icon className="h-4 w-4 text-ledger-300 transition group-hover:text-ledger-100" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </nav>
            </div>
            <div className="rounded-2xl border border-white/10 bg-ink-900/35 px-4 py-4 text-xs text-ledger-300 backdrop-blur">
              <div className="font-medium text-ledger-200">阶段说明</div>
              <div className="mt-2 leading-relaxed">
                目前邮件中心为演示模式：Case 与模板可用，Outlook 会话同步将在接入 Outlook COM / Graph 后启用。
              </div>
            </div>
          </div>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
