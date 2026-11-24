"use client";
import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { AgencyReport, CompletionTrend, EmailHistoryEntry, EmployeeReport } from "@/lib/types";

export default function ReportsPage() {
  const [report, setReport] = useState<AgencyReport|null>(null);
  const [employees, setEmployees] = useState<EmployeeReport[]>([]);
  const [trends, setTrends] = useState<CompletionTrend[]>([]);
  const [emailHistory, setEmailHistory] = useState<EmailHistoryEntry[]>([]);
  const [recipient, setRecipient] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const [agency,staff,completion,email]=await Promise.all([
      apiJson<AgencyReport>("/api/reports/agency"),
      apiJson<EmployeeReport[]>("/api/reports/employees"),
      apiJson<CompletionTrend[]>("/api/reports/trends"),
      apiJson<EmailHistoryEntry[]>("/api/reports/email/history"),
    ]);
    setReport(agency);setEmployees(staff);setTrends(completion);setEmailHistory(email);
  },[]);
  useEffect(()=>{
    let cancelled=false;
    Promise.all([
      apiJson<AgencyReport>("/api/reports/agency"),
      apiJson<EmployeeReport[]>("/api/reports/employees"),
      apiJson<CompletionTrend[]>("/api/reports/trends"),
      apiJson<EmailHistoryEntry[]>("/api/reports/email/history"),
    ]).then(([agency,staff,completion,email])=>{
      if(!cancelled){setReport(agency);setEmployees(staff);setTrends(completion);setEmailHistory(email)}
    }).catch(reason=>{if(!cancelled)setError(errorMessage(reason,"Could not load analytics."))});
    return()=>{cancelled=true};
  },[]);
  const distribution = report ? Object.entries(report.status_distribution).map(([name,value])=>({name,value:Number(value)})) : [];
  const sendReport = async () => {
    setError(""); setMessage("");
    try {
      const result=await apiJson<{recipient:string}>("/api/reports/email/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({recipient:recipient||null})});
      setMessage(`Report accepted by SMTP for ${result.recipient}.`);load();
    } catch(reason) { setError(errorMessage(reason,"Email send failed.")); }
  };
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">Database analytics</p><h1>Reports & insights</h1><p className="subtitle">Verified performance from recorded tasks, tests, and deployments.</p></div><div className="report-actions"><a className="secondary-button" href="/api/reports/export">Export CSV</a><button className="secondary-button" onClick={()=>window.print()}>Print / Save PDF</button></div></header>
    {error&&<p className="form-error" role="alert">{error}</p>}{message&&<p className="success-message">{message}</p>}
    {report&&<section className="metric-grid"><div className="metric-card"><div><span>Completed today</span><strong>{report.completed_today}</strong></div></div><div className="metric-card"><div><span>Total completed</span><strong>{report.completed_tasks}</strong></div></div><div className="metric-card"><div><span>Projects delivered</span><strong>{report.delivered_projects}</strong></div></div><div className="metric-card"><div><span>Blocked tasks</span><strong>{report.blocked}</strong></div></div></section>}
    {report&&<section className="charts-grid"><article className="panel chart-panel"><div className="panel-header"><div><p className="eyebrow">Task ledger</p><h2>Tasks by status</h2></div></div><div className="chart-body"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={distribution} dataKey="value" nameKey="name" innerRadius={58} outerRadius={88} paddingAngle={4}>{distribution.map((entry,index)=><Cell key={entry.name} fill={["#53ddb0","#a98af5","#f2b94b","#6b7773","#424a47"][index%5]}/>)}</Pie><Tooltip contentStyle={{background:"#151818",border:"1px solid #252929"}}/></PieChart></ResponsiveContainer></div><div className="chart-legend">{distribution.map((entry,index)=><span key={entry.name}><i style={{background:["#53ddb0","#a98af5","#f2b94b","#6b7773","#424a47"][index%5]}}/>{entry.name} <b>{entry.value}</b></span>)}</div></article>
    <article className="panel chart-panel"><div className="panel-header"><div><p className="eyebrow">Delivery velocity</p><h2>Completed tasks over time</h2></div></div><div className="chart-body wide"><ResponsiveContainer width="100%" height="100%"><BarChart data={trends}><CartesianGrid stroke="#252929" vertical={false}/><XAxis dataKey="date" tick={{fill:"#919999",fontSize:8}}/><YAxis allowDecimals={false} tick={{fill:"#919999",fontSize:9}}/><Tooltip contentStyle={{background:"#151818",border:"1px solid #252929"}}/><Bar dataKey="completed" fill="#53ddb0" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div></article></section>}
    {report&&<p className="analytics-note">QA pass rate: {report.qa_pass_rate===null?"No test executions recorded":`${report.qa_pass_rate}% (${report.qa_tests_executed} runs)`} · Deployment success: {report.deployment_success_rate===null?"No deployments recorded":`${report.deployment_success_rate}%`} · Average completion: {report.average_completion_hours===null?"No duration data":`${report.average_completion_hours} hours`}</p>}
    <section className="panel table-panel"><div className="panel-header"><div><p className="eyebrow">People</p><h2>Employee performance</h2></div></div><table className="data-table"><thead><tr><th>Employee</th><th>Assigned</th><th>Completed</th><th>Pending</th><th>Blocked</th></tr></thead><tbody>{employees.map(e=><tr key={e.id}><td><strong>{e.name}</strong><br/><small>{e.title}</small></td><td>{e.assigned}</td><td>{e.completed}</td><td>{e.pending}</td><td>{e.blocked}</td></tr>)}</tbody></table></section>
    <section className="panel form-panel report-email"><div className="panel-header"><div><p className="eyebrow">Daily reporting</p><h2>Send agency report</h2></div></div><div className="modal-body"><div className="field"><label htmlFor="report-recipient">Recipient email (optional if configured in settings)</label><input id="report-recipient" type="email" value={recipient} onChange={e=>setRecipient(e.target.value)}/></div><button className="primary-button" onClick={sendReport}>Send report</button></div></section>
    <section className="panel table-panel email-history"><div className="panel-header"><div><p className="eyebrow">Delivery log</p><h2>Email history</h2></div></div><table className="data-table"><thead><tr><th>Time</th><th>Recipient</th><th>Subject</th><th>Status</th></tr></thead><tbody>{emailHistory.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.recipient||"—"}</td><td>{row.subject}</td><td>{row.status}</td></tr>)}{emailHistory.length===0&&<tr><td colSpan={4}>No reports have been sent.</td></tr>}</tbody></table></section>
  </DashboardShell>;
}
