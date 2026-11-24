"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { ProjectDetail, ProjectQaResult } from "@/lib/types";

export default function ProjectDetailClient() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project,setProject]=useState<ProjectDetail|null>(null);
  const [error,setError]=useState("");
  const [qaResult,setQaResult]=useState<ProjectQaResult|null>(null);
  const load=useCallback(async()=>{
    try { setProject(await apiJson<ProjectDetail>(`/api/projects/${projectId}`)); }
    catch(reason) { setError(errorMessage(reason,"Could not load project.")); }
  },[projectId]);
  useEffect(()=>{
    let cancelled=false;
    apiJson<ProjectDetail>(`/api/projects/${projectId}`).then(data=>{if(!cancelled)setProject(data)}).catch(reason=>{if(!cancelled)setError(errorMessage(reason,"Could not load project."))});
    return()=>{cancelled=true};
  },[projectId]);
  const act=async(path:string,body?:object)=>{
    setError("");
    try {
      await apiJson<{status:string}>(`/api/projects/${projectId}${path?`/${path}`:""}`,{method:body?"PATCH":"POST",headers:body?{"Content-Type":"application/json"}:undefined,body:body?JSON.stringify(body):undefined});
      await load();
    } catch(reason) { setError(errorMessage(reason,"Project update failed.")); }
  };
  const runQa=async()=>{
    setError("");setQaResult(null);
    try { setQaResult(await apiJson<ProjectQaResult>(`/api/projects/${projectId}/qa/run`,{method:"POST"})); }
    catch(reason) { setError(errorMessage(reason,"Integrity checks failed to run.")); }
  };
  if(!project)return <DashboardShell><p className="subtitle">{error||"Loading project…"}</p></DashboardShell>;
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">{project.project_key} · {project.client?.name}</p><h1>{project.name}</h1><p className="subtitle">{project.description}</p></div><div className="report-actions">{project.status==="planning"&&<button className="primary-button" onClick={()=>act("approve-plan")}>Approve plan</button>}{project.status==="active"&&<button className="secondary-button" onClick={()=>act("",{status:"paused"})}>Pause project</button>}{project.status==="paused"&&<button className="primary-button" onClick={()=>act("",{status:"active"})}>Resume project</button>}</div></header>
    {error&&<p className="form-error">{error}</p>}<section className="project-detail-grid"><article className="panel"><div className="panel-header"><div><p className="eyebrow">Delivery plan</p><h2>{project.tasks.length} specialist tasks</h2></div><span className={`status ${project.status}`}>{project.status}</span></div>{project.tasks.map(task=><div className="task-detail-row" key={task.id}><div><strong>{task.task_key}</strong> · {task.title}<br/><small>{task.employee||"Unassigned"}</small></div><span className={`status ${task.status}`}>{task.status.replace("_"," ")}</span></div>)}</article>
    <article className="panel"><div className="panel-header"><div><p className="eyebrow">Project pulse</p><h2>{project.progress}% complete</h2></div></div><div className="modal-body"><p className="detail-label">Client</p><p>{project.client?.name}</p><p className="detail-label">Priority</p><p>{project.priority}</p><p className="detail-label">Created</p><p>{new Date(project.created_at).toLocaleString()}</p><div className="progress-track"><div style={{width:`${project.progress}%`}}/></div><p className="detail-label">Deliverables</p>{project.deliverables.length?project.deliverables.map(item=><p key={item.id}>{item.title}</p>):<p className="empty-state">No deliverables submitted yet.</p>}<button className="secondary-button" onClick={()=>void runQa()}>Run workflow integrity checks</button>{qaResult&&<div className="qa-results"><p className="detail-label">Check result: {qaResult.status}</p><small>{qaResult.scope}</small>{qaResult.checks.map(check=><p key={check.test_case_id}>{check.title}: {check.status}</p>)}</div>}</div></article></section><p className="subtitle" style={{marginTop:16}}><Link className="project-link" href="/projects">← Back to projects</Link></p>
  </DashboardShell>;
}
