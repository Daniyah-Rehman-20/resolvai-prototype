"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ArrowLeftRight,
  Sparkles,
  ShieldCheck,
  Flag,
  BookOpen,
  Activity,
  ChartNoAxesCombined,
  Settings,
  Search,
  Bell,
  ChevronDown,
  Menu,
  X,
  CircleHelp,
  ArrowUpRight,
} from "lucide-react";
import type { AppData } from "@/lib/types";
import { getWorkspace } from "@/lib/api";
import { Busy } from "@/components/common/ui";
const Context = createContext<{
  data: AppData;
  refresh: () => Promise<void>;
  notify: (message: string) => void;
} | null>(null);
export function useWorkspace() {
  const ctx = useContext(Context);
  if (!ctx) throw new Error("Workspace provider missing");
  return ctx;
}
const nav = [
  ["Dashboard", "/dashboard", LayoutDashboard],
  ["Transactions", "/transactions", ArrowLeftRight],
  ["AI Investigator", "/investigator", Sparkles],
  ["Approval Queue", "/approvals", ShieldCheck],
  ["Disputes", "/disputes", Flag],
  ["Knowledge Base", "/knowledge", BookOpen],
  ["Agent Activity", "/agents", Activity],
  ["Analytics", "/analytics", ChartNoAxesCombined],
  ["Settings", "/settings", Settings],
] as const;
export function Workspace({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [mobile, setMobile] = useState(false);
  const [notifications, setNotifications] = useState(false);
  const [profile, setProfile] = useState(false);
  const [search, setSearch] = useState("");
  const router = useRouter();
  const path = usePathname();
  async function refresh() {
    const next = await getWorkspace();
    setData(next);
    document.documentElement.dataset.theme = next.settings.theme;
  }
  useEffect(() => {
    getWorkspace()
      .then((next) => {
        setData(next);
        document.documentElement.dataset.theme = next.settings.theme;
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    function dismiss(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobile(false);
        setNotifications(false);
        setProfile(false);
      }
    }
    window.addEventListener("keydown", dismiss);
    if (mobile) {
      document.body.style.overflow = "hidden";
      document.querySelector<HTMLButtonElement>(".mobile-close")?.focus();
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", dismiss);
    };
  }, [mobile]);
  const pending =
    data?.approvals.filter((a) => a.status === "PENDING").length ?? 0;
  function searchSubmit(e: FormEvent) {
    e.preventDefault();
    router.push(`/transactions?q=${encodeURIComponent(search.trim())}`);
    setSearch("");
  }
  const links = (
    <>
      <Link
        href="/dashboard"
        className="brand"
        onClick={() => setMobile(false)}
      >
        <span className="brand-symbol">
          <ArrowLeftRight size={23} />
        </span>
        <span>
          PayResolve<span className="brand-ai"> AI</span>
          <small>PAYMENT OPERATIONS</small>
        </span>
      </Link>
      <div className="workspace-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        {nav.map(([name, href, Icon], i) => (
          <Link
            key={href}
            href={href}
            aria-current={
              path === href ||
              (href === "/transactions" && path.startsWith("/transactions/"))
                ? "page"
                : undefined
            }
            onClick={() => setMobile(false)}
          >
            <Icon size={19} />
            <span>{name}</span>
            {i === 3 && pending > 0 && (
              <span className="nav-count">{pending}</span>
            )}
          </Link>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="safe-box">
          <ShieldCheck size={20} />
          <strong>Human control. Always.</strong>
          <p>Every proposed payment action stays in your hands.</p>
        </div>
        <Link
          href="/knowledge"
          className="support-link"
          onClick={() => setMobile(false)}
        >
          <CircleHelp size={17} /> Policies & guidance
          <ArrowUpRight size={14} />
        </Link>
        <div className="workspace-id">
          <span className="avatar">DR</span>
          <div>
            <strong>Daniyah&apos;s workspace</strong>
            <small>Demo operations team</small>
          </div>
        </div>
      </div>
    </>
  );
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">{links}</aside>
      {mobile && (
        <div className="mobile-overlay" onClick={() => setMobile(false)}>
          <aside
            className="sidebar mobile-sidebar"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="mobile-close icon-button"
              onClick={() => setMobile(false)}
              aria-label="Close navigation"
            >
              <X />
            </button>
            {links}
          </aside>
        </div>
      )}
      <div className="app-body" inert={mobile}>
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMobile(true)}
          >
            <Menu />
          </button>
          <form className="global-search" onSubmit={searchSubmit}>
            <Search size={18} />
            <input
              aria-label="Search all transactions"
              placeholder="Search transactions, orders, customers…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <kbd>↵</kbd>
          </form>
          <div className="topbar-right">
            <span className="environment">
              <span />
              Demo environment
            </span>
            <div className="popover-anchor">
              <button
                className="icon-button"
                aria-label="Notifications"
                aria-expanded={notifications}
                onClick={() => {
                  setNotifications(!notifications);
                  setProfile(false);
                }}
              >
                <Bell size={19} />
                {pending > 0 && data?.settings.notifications && (
                  <span className="notification-dot" />
                )}
              </button>
              {notifications && (
                <div className="popover">
                  <strong>Notifications</strong>
                  <p>
                    {data?.settings.notifications
                      ? `${pending} approvals need a human review.`
                      : "Notifications are paused in Settings."}
                  </p>
                  <Link
                    href="/approvals"
                    onClick={() => setNotifications(false)}
                  >
                    Open approval queue →
                  </Link>
                </div>
              )}
            </div>
            <div className="popover-anchor">
              <button
                className="profile-button"
                aria-expanded={profile}
                onClick={() => {
                  setProfile(!profile);
                  setNotifications(false);
                }}
              >
                <span className="avatar">DR</span>
                <span>Daniyah R.</span>
                <ChevronDown size={14} />
              </button>
              {profile && (
                <div className="popover">
                  <strong>Demo reviewer</strong>
                  <p>Local workspace · no sign-in required</p>
                  <Link href="/settings" onClick={() => setProfile(false)}>
                    Workspace settings →
                  </Link>
                </div>
              )}
            </div>
          </div>
        </header>
        <main id="main" className="main-content">
          {error ? (
            <div className="error-box">
              <h1>Unable to load workspace</h1>
              <p>{error}</p>
              <button
                className="button"
                onClick={() => window.location.reload()}
              >
                Retry
              </button>
            </div>
          ) : !data ? (
            <Busy />
          ) : (
            <Context.Provider value={{ data, refresh, notify: setToast }}>
              {children}
            </Context.Provider>
          )}
        </main>
        <footer className="footer">
          <span>PayResolve AI · Fictional demo data</span>
          <span>No real payments or external AI calls · INR · IST</span>
        </footer>
      </div>
      {toast && (
        <div className="toast" role="status">
          <ShieldCheck size={19} />
          {toast}
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </>
  );
}
