"use client";

import { useCallback, useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { TaskDetail, TaskStatus, TaskSummary } from "@/lib/types";

const columns: { status: TaskStatus; label: string }[] = [
  { status: "queued", label: "Queued" },
  { status: "in_progress", label: "In progress" },
  { status: "blocked", label: "Blocked" },
  { status: "completed", label: "Completed" },
];

type TaskDrawer = TaskDetail | { loading: true };

export default function TasksPage() {
  const [tasks,setTasks]=useState<TaskSummary[]>([]);
  const [selected,setSelected]=useState<TaskDrawer|null>(null);
  const [error,setError]=useState("");
  const load=useCallback(async()=>{
    try { setTasks(await apiJson<TaskSummary[]>("/api/tasks")); }
    catch(reason) { setError(errorMessage(reason,"Could not load tasks.")); }
  },[]);
  useEffect(()=>{
    let cancelled=false;
    const refresh=()=>apiJson<TaskSummary[]>("/api/tasks").then(data=>{if(!cancelled)setTasks(data)}).catch(reason=>{if(!cancelled)setError(errorMessage(reason,"Could not load tasks."))});
    void refresh();
    const timer=setInterval(()=>void refresh(),5000);
    return ()=>{cancelled=true;clearInterval(timer)};
  },[]);
  const execute=async(id:number)=>{
    setError("");
    try { await apiJson<{status:string}>(`/api/tasks/${id}/execute`,{method:"POST"}); await load(); }
    catch(reason) { setError(errorMessage(reason,"Task execution failed.")); }
  };
  const loadDetail=async(id:number)=>{
    setSelected({loading:true});
    try { setSelected(await apiJson<TaskDetail>(`/api/tasks/${id}`)); }
    catch(reason) { setSelected(null);setError(errorMessage(reason,"Could not load task.")); }
  };
  return <DashboardShell>
    <header className="page-header"><div><p className="eyebrow">Live workflow</p><h1>Task board</h1><p className="subtitle">Execution status across the entire agency.</p></div></header>
    {error&&<p className="form-error" role="alert">{error}</p>}
    <section className="board-columns">{columns.map(column=>{
      const items=tasks.filter(task=>task.status===column.status);
      return <div className="board-column" key={column.status}>
        <div className="column-head"><h3>{column.label}</h3><span className="count-pill">{items.length}</span></div>
        {items.map(task=><article className="task-card" key={task.id} onClick={()=>void loadDetail(task.id)}>
          <small>{task.task_key} · {task.project_key}</small><h4>{task.title}</h4>
          <div className="task-meta"><span>{task.employee||"Unassigned"}</span>
            {column.status==="queued"&&<button className="text-button" onClick={event=>{event.stopPropagation();void execute(task.id)}}>Execute</button>}
          </div>
          {task.dependencies?.length ? <small>Depends on {task.dependencies.map(dependency=>dependency.task_key).join(", ")}</small> : null}
        </article>)}
      </div>;
    })}</section>
    {selected&&<div className="drawer-backdrop" onClick={()=>setSelected(null)}>
      <aside className="task-drawer" onClick={event=>event.stopPropagation()}>
        <button className="drawer-close" onClick={()=>setSelected(null)}>Close</button>
        {"loading" in selected ? <p>Loading task…</p> : <div className="drawer-content">
          <p className="eyebrow">{selected.task_key} · {selected.project}</p><h2>{selected.title}</h2>
          <span className={`status ${selected.status}`}>{selected.status.replace("_"," ")}</span>
          <p className="detail-label">Description</p><p>{selected.description}</p>
          <p className="detail-label">Assigned employee</p><p>{selected.employee||"Unassigned"}</p>
          <p className="detail-label">Dependencies</p>{selected.dependencies.length?selected.dependencies.map(dependency=><p key={dependency.id}>{dependency.task_key} · {dependency.status}</p>):<p>None</p>}
          <p className="detail-label">Deliverables</p>{selected.deliverables.length?selected.deliverables.map((item,index)=><pre className="deliverable-card" key={`${item.title}-${index}`}><strong>{item.title}</strong>{"\n"}{item.content}</pre>):<p>No deliverables submitted.</p>}
          <p className="detail-label">Execution log</p>{selected.executions.map(execution=><p key={execution.id}>{execution.status}: {execution.summary||execution.error_detail}</p>)}
        </div>}
      </aside>
    </div>}
  </DashboardShell>;
}
