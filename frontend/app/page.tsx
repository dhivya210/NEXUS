"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Check, CircleAlert, Clock3, Plus, Sparkles } from "lucide-react";
import DashboardShell from "@/components/dashboard-shell";
import Link from "next/link";
import { apiJson } from "@/lib/api";
import type { ActivityEntry, EmployeeSummary, ProjectSummary, TaskSummary } from "@/lib/types";

export default function Home() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [employees, setEmployees] = useState<EmployeeSummary[]>([]);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiJson<ProjectSummary[]>("/api/projects"),
      apiJson<EmployeeSummary[]>("/api/employees"),
      apiJson<TaskSummary[]>("/api/tasks"),
      apiJson<ActivityEntry[]>("/api/activity"),
    ]).then(([p, e, t, a]) => {
      setProjects(p); setEmployees(e); setTasks(t); setActivity(a);
    }).catch(() => setError("Could not load command-center data.")).finally(() => setLoading(false));
  }, []);

  const completed = tasks.filter(t => t.status === "completed").length;
  const inProgress = tasks.filter(t => t.status === "in_progress").length;
  const blocked = tasks.filter(t => t.status === "blocked").length;
  const metrics = [
    { label: "Total tasks", value: tasks.length, icon: Clock3, color: "text-slate-300" },
    { label: "In progress", value: inProgress, icon: ArrowUpRight, color: "text-violet-300" },
    { label: "Completed", value: completed, icon: Check, color: "text-mint" },
    { label: "Needs attention", value: blocked, icon: CircleAlert, color: "text-amber-300" },
  ];

  return (
    <DashboardShell>
      <header className="page-header">
        <div>
          <p className="eyebrow">Workspace overview</p>
          <h1>Command center</h1>
          <p className="subtitle">Your team, your projects. Everything in one place.</p>
        </div>
        <Link className="primary-button" href="/projects"><Plus size={17} /> New project</Link>
      </header>

      <section className="metric-grid">
        {metrics.map(({ label, value, icon: Icon, color }) => (
          <article className="metric-card" key={label}>
            <div className="metric-icon"><Icon size={17} className={color} /></div>
            <div><span>{label}</span><strong>{loading ? "—" : value}</strong></div>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <article className="panel projects-panel">
          <div className="panel-header">
            <div><p className="eyebrow">Live delivery</p><h2>Active projects</h2></div>
            <Link className="text-button" href="/projects">View all <ArrowUpRight size={14} /></Link>
          </div>
          <div className="project-list">{error&&<p className="form-error">{error}</p>}
            {projects.map(project => (
              <div className="project-row" key={project.id}>
                <div className="project-mark">{project.project_key?.slice(-3)}</div>
                <div className="project-main">
                  <div className="row-title"><strong>{project.name}</strong><span className={`status ${project.status}`}>{project.status}</span></div>
                  <p>{project.client} · {project.project_key}</p>
                  <div className="progress-track"><div style={{ width: `${project.progress}%` }} /></div>
                </div>
                <div className="project-progress"><strong>{project.progress}%</strong><span>progress</span></div>
              </div>
            ))}
            {!loading && projects.length === 0 && <p className="empty-state">No projects yet.</p>}
          </div>
        </article>

        <article className="panel activity-panel">
          <div className="panel-header"><div><p className="eyebrow">Agency feed</p><h2>Recent activity</h2></div></div>
          <div className="activity-list">
            {activity.slice(0, 5).map((item, index) => (
              <div className="activity-item" key={item.id}>
                <span className={`activity-dot dot-${index % 3}`}><Sparkles size={12} /></span>
                <div><strong>{item.title}</strong><p>{item.detail}</p></div>
              </div>
            ))}
            {!loading && activity.length === 0 && <p className="empty-state">No activity recorded.</p>}
          </div>
        </article>
      </section>

      <section className="panel employee-panel">
        <div className="panel-header">
          <div><p className="eyebrow">Specialists</p><h2>Your AI employees</h2></div>
          <Link className="text-button" href="/employees">View directory <ArrowUpRight size={14} /></Link>
        </div>
        <div className="employee-grid">
          {employees.slice(0, 8).map(employee => (
            <article className="employee-card" key={employee.id}>
              <div className="employee-top">
                <div className="avatar">{employee.initials}</div>
                <span className={`employee-status ${employee.status}`}><i /> {employee.status}</span>
              </div>
              <strong>{employee.name}</strong>
              <p>{employee.title}</p>
              <div className="employee-stats">
                <span><b>{employee.completed_tasks}</b> completed</span>
                <span><b>{employee.pending_tasks}</b> pending</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </DashboardShell>
  );
}
