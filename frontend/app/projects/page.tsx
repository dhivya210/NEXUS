"use client";
import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import DashboardShell from "@/components/dashboard-shell";
import Link from "next/link";
import { apiJson, errorMessage } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";
export default function ProjectsPage(){
 const [projects,setProjects]=useState<ProjectSummary[]>([]);
 const [open,setOpen]=useState(false);
 const [name,setName]=useState("");
 const [description,setDescription]=useState("");
 const [client,setClient]=useState("");
 const [error,setError]=useState("");
 const load=useCallback(async()=>{try{setProjects(await apiJson<ProjectSummary[]>("/api/projects"))}catch(reason){setError(errorMessage(reason,"Could not load projects."))}},[]);
 useEffect(()=>{
   let cancelled=false;
   apiJson<ProjectSummary[]>("/api/projects").then(data=>{if(!cancelled)setProjects(data)}).catch(reason=>{if(!cancelled)setError(errorMessage(reason,"Could not load projects."))});
   return()=>{cancelled=true};
 },[]);
 const createProject=async()=>{
   if(!name.trim()||!description.trim()||!client.trim())return;
   setError("");
   try {
     await apiJson<{id:number}>("/api/projects",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,description,client_name:client,priority:"medium"})});
     setOpen(false);setName("");setDescription("");setClient("");await load();
   } catch(reason){setError(errorMessage(reason,"Could not create project."))}
 };
 return <DashboardShell><header className="page-header"><div><p className="eyebrow">Client delivery</p><h1>Projects</h1><p className="subtitle">Plan, monitor, and deliver client software.</p></div><button className="primary-button" onClick={()=>setOpen(true)}><Plus size={17}/> New project</button></header>
 {open&&<div className="modal-backdrop"><section className="panel form-panel modal"><div className="panel-header"><div><p className="eyebrow">New client request</p><h2>Create project</h2></div><button className="text-button" onClick={()=>setOpen(false)}>Close</button></div><div className="modal-body"><div className="field"><label>Project name</label><input value={name} onChange={e=>setName(e.target.value)} placeholder="University event platform"/></div><div className="field"><label>Client name</label><input value={client} onChange={e=>setClient(e.target.value)} placeholder="Riga Student Union"/></div><div className="field"><label>Requirements</label><textarea value={description} onChange={e=>setDescription(e.target.value)} placeholder="Describe the product, users, and core workflows."/></div>{error&&<p className="form-error">{error}</p>}<button className="primary-button" onClick={createProject}>Create project</button></div></section></div>}
 <section className="panel table-panel"><div className="panel-header"><div><p className="eyebrow">Portfolio</p><h2>All projects</h2></div></div>
 <table className="data-table"><thead><tr><th>Project</th><th>Client</th><th>Priority</th><th>Tasks</th><th>Progress</th><th>Status</th></tr></thead><tbody>{projects.map(p=><tr key={p.id}><td><Link className="project-link" href={`/projects/${p.id}`}><strong>{p.name}</strong></Link><br/><small>{p.project_key}</small></td><td>{p.client}</td><td>{p.priority}</td><td>{p.completed_tasks}/{p.task_count}</td><td>{p.progress}%</td><td><span className={`status ${p.status}`}>{p.status}</span></td></tr>)}</tbody></table></section></DashboardShell>
}
