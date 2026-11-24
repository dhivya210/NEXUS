"use client";
import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
type Automation = { key: string; name: string; description: string; enabled: boolean; mutable: boolean; last_status: string; last_run_at: string | null; detail: string };
export default function AutomationPage() {
  const [jobs, setJobs] = useState<Automation[]>([]);
  const [error, setError] = useState("");
  const load = () => fetch("/api/automation").then(async response => {
    if (!response.ok) throw new Error("Could not load automation settings.");
    setJobs(await response.json());
  }).catch(reason => setError(reason.message));
  useEffect(() => { load(); }, []);
  const toggle = async (job: Automation) => {
    const response = await fetch(`/api/automation/${job.key}`, { method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify({enabled:!job.enabled}) });
    const result = await response.json();
    if (!response.ok) { setError(result.detail || "Could not update automation."); return; }
    load();
  };
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">Operations</p><h1>Automation center</h1><p className="subtitle">Manage agency workflows and integration jobs.</p></div></header>
    {error&&<p className="form-error" role="alert">{error}</p>}
    <section className="panel table-panel"><table className="data-table"><thead><tr><th>Automation</th><th>Description</th><th>State</th><th>Last execution</th><th></th></tr></thead><tbody>{jobs.map(job=><tr key={job.key}><td><strong>{job.name}</strong></td><td>{job.description}</td><td><span className={`status ${job.enabled?"active":""}`}>{job.enabled?"Enabled":"Disabled"}</span></td><td>{job.last_run_at ? new Date(job.last_run_at).toLocaleString() : job.last_status}</td><td>{job.mutable&&<button className="text-button" onClick={()=>toggle(job)}>{job.enabled?"Disable":"Enable"}</button>}</td></tr>)}</tbody></table></section>
  </DashboardShell>;
}
