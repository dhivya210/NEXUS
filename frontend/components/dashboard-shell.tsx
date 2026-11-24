"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity, Bell, ChevronDown, FolderKanban, LayoutDashboard, Plug,
  Settings, Sparkles, Users, Workflow, BarChart3, MessageSquare, Search
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const workspace = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Client projects", href: "/projects", icon: FolderKanban },
  { label: "Task board", href: "/tasks", icon: Workflow },
  { label: "AI employees", href: "/employees", icon: Users },
  { label: "Reports", href: "/reports", icon: BarChart3 },
  { label: "Team chat", href: "/chat", icon: MessageSquare },
];
const manage = [
  { label: "Integrations", href: "/integrations", icon: Plug },
  { label: "Automation", href: "/automation", icon: Activity },
  { label: "Settings", href: "/settings", icon: Settings },
];

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [verified, setVerified] = useState(false);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  useEffect(() => {
    Promise.all([fetch("/api/auth/me"), fetch("/api/health")]).then(([session, health]) => {
      if (!session.ok) { router.replace("/login"); return; }
      setVerified(true);
      setApiConnected(health.ok);
    }).catch(() => router.replace("/login"));
  }, [router]);
  const signOut = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  };
  const navItem = (item: { label: string; href: string; icon: LucideIcon }) => {
    const Icon = item.icon;
    const active = pathname === item.href;
    return <Link className={`nav-item ${active ? "active" : ""}`} href={item.href} key={item.href}><Icon size={17} /><span>{item.label}</span></Link>;
  };
  if (!verified) return <div className="auth-loading">Verifying workspace session…</div>;
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Sparkles size={16} /></div><span>nexus</span></div>
        <button className="agency-switcher"><div className="agency-icon">N</div><div><strong>NEXUS Agency</strong><span>Command workspace</span></div><ChevronDown size={14} /></button>
        <nav>
          <p className="nav-label">Workspace</p>
          {workspace.map(navItem)}
          <p className="nav-label manage-label">Manage</p>
          {manage.map(navItem)}
        </nav>
        <div className="sidebar-footer">
          <button className="avatar boss-avatar" onClick={signOut} aria-label="Sign out">BS</button>
          <div><strong>Boss</strong><span>Administrator</span></div>
          <ChevronDown size={14} />
        </div>
      </aside>
      <main className="main-area">
        <div className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{pathname === "/" ? "Overview" : pathname.slice(1).replace("-", " ")}</strong></div>
          <div className="top-actions">
            <button className={`cloud-status ${apiConnected===false?"disconnected":""}`}><i /> {apiConnected===null?"Checking backend":apiConnected?"Backend connected":"Backend unavailable"}</button>
            <button className="icon-button" aria-label="Search"><Search size={16} /></button>
            <button className="icon-button" aria-label="Notifications"><Bell size={16} /><span className="notification-dot" /></button>
          </div>
        </div>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
