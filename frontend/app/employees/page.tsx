"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson } from "@/lib/api";
import type { EmployeeSummary } from "@/lib/types";
export default function EmployeesPage(){
 const [employees,setEmployees]=useState<EmployeeSummary[]>([]);
 useEffect(()=>{apiJson<EmployeeSummary[]>("/api/employees").then(setEmployees)},[]);
 return <DashboardShell><header className="page-header"><div><p className="eyebrow">Agency directory</p><h1>AI employees</h1><p className="subtitle">Eight specialists. One coordinated delivery team.</p></div></header>
 <section className="directory-grid">{employees.map(e=><article className="employee-card" key={e.id}><div className="employee-top"><div className="avatar">{e.initials}</div><span className={`employee-status ${e.status}`}><i/> {e.status}</span></div><strong>{e.name}</strong><p>{e.title}</p><div className="employee-stats"><span><b>{e.completed_tasks}</b> completed</span><span><b>{e.pending_tasks}</b> pending</span></div>{e.current_assignment&&<p className="assignment-note">Working on: {e.current_assignment}</p>}<div className="employee-links"><Link className="text-button" href={`/employees/${e.id}`}>Profile</Link><Link className="text-button" href={`/chat?employeeId=${e.id}`}>Chat ↗</Link></div></article>)}</section></DashboardShell>
}
