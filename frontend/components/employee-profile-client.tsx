"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { EmployeePerformance, EmployeeProfile } from "@/lib/types";

export default function EmployeeProfileClient() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [profile,setProfile]=useState<EmployeeProfile|null>(null);
  const [performance,setPerformance]=useState<EmployeePerformance|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{
    let cancelled=false;
    Promise.all([
      apiJson<EmployeeProfile>(`/api/employees/${employeeId}`),
      apiJson<EmployeePerformance>(`/api/employees/${employeeId}/performance`),
    ]).then(([employee,report])=>{
      if(!cancelled){setProfile(employee);setPerformance(report)}
    }).catch(reason=>{if(!cancelled)setError(errorMessage(reason,"Could not load employee profile."))});
    return()=>{cancelled=true};
  },[employeeId]);
  if(!profile||!performance)return <DashboardShell><p className="subtitle">{error||"Loading employee…"}</p></DashboardShell>;
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">AI employee profile</p><h1>{profile.name}</h1><p className="subtitle">{profile.title}</p></div><Link className="primary-button" href={`/chat?employeeId=${profile.id}`}>Open chat</Link></header>
    <section className="project-detail-grid"><article className="panel"><div className="panel-header"><div><p className="eyebrow">Role overview</p><h2>{profile.title}</h2></div><span className={`employee-status ${profile.status}`}><i/>{profile.status}</span></div><div className="modal-body"><p>{profile.description}</p><p className="detail-label">Responsibilities</p>{profile.responsibilities.map(item=><p key={item}>· {item}</p>)}<p className="detail-label">Role prompt</p><p>{profile.system_prompt}</p></div></article>
    <article className="panel"><div className="panel-header"><div><p className="eyebrow">Performance</p><h2>{performance.completed} completed</h2></div></div><div className="modal-body"><p>Assigned: {performance.assigned}</p><p>Pending: {performance.pending}</p><p>Blocked: {performance.blocked}</p><p>Completion rate: {performance.completion_rate===null?"No task history":`${performance.completion_rate}%`}</p><p>Average duration: {performance.average_completion_hours===null?"No duration history":`${performance.average_completion_hours} hours`}</p></div></article></section>
    <section className="panel employee-task-panel"><div className="panel-header"><div><p className="eyebrow">Work history</p><h2>Assignments</h2></div></div>{profile.tasks.map(task=><div className="task-detail-row" key={task.id}><span>{task.task_key} · {task.title}</span><span className={`status ${task.status}`}>{task.status.replace("_"," ")}</span></div>)}{profile.tasks.length===0&&<p className="empty-state">No assignments yet.</p>}</section>
  </DashboardShell>;
}
