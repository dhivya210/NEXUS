"use client";
import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { ChatRecord, EmployeeSummary, TeamChatMessage } from "@/lib/types";

type Message = { sender: string; message: string };
export default function ChatPage() {
  const [employees,setEmployees]=useState<EmployeeSummary[]>([]);
  const [selected,setSelected]=useState<EmployeeSummary|null>(null);
  const [messages,setMessages]=useState<Message[]>([]);
  const [input,setInput]=useState("");
  const [mode,setMode]=useState<"direct"|"team">("direct");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  useEffect(()=>{apiJson<EmployeeSummary[]>("/api/employees").then(list=>{
    setEmployees(list);
    const employeeId=new URLSearchParams(window.location.search).get("employeeId");
    const requested=list.find(employee=>String(employee.id)===employeeId);
    setSelected(requested||list.find(employee=>employee.employee_key==="alex")||list[0]||null);
  }).catch(reason=>setError(errorMessage(reason,"Could not load employees.")))},[]);
  useEffect(()=>{
    if(mode==="team"){
      apiJson<TeamChatMessage[]>("/api/team/messages").then(history=>{
        setMessages(history.map(item=>({sender:`${item.sender} → ${item.receiver}`,message:item.message})));
      }).catch(reason=>setError(errorMessage(reason,"Could not load team messages.")));
      return;
    }
    if(!selected)return;
    apiJson<ChatRecord[]>(`/api/employees/${selected.id}/chat`).then(history=>{
      setMessages(history.map(item=>({sender:item.sender,message:item.message})));
    }).catch(reason=>setError(errorMessage(reason,"Could not load conversation history.")));
  },[selected,mode]);
  const send=async()=>{
    if(!input.trim()||!selected||busy)return;
    const text=input.trim();setInput("");setError("");setBusy(true);
    try{
      const isManager=selected?.employee_key==="alex";
      const endpoint=mode==="team"?"/api/team/messages":isManager?"/api/ai/project-manager/chat":`/api/employees/${selected.id}/chat`;
      if(mode==="team"){
        await apiJson<TeamChatMessage>(endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
        const history=await apiJson<TeamChatMessage[]>("/api/team/messages");
        setMessages(history.map(item=>({sender:`${item.sender} → ${item.receiver}`,message:item.message})));
      }else{
        await apiJson<{reply:string}>(endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
        const history=await apiJson<ChatRecord[]>(`/api/employees/${selected!.id}/chat`);
        setMessages(history.map(item=>({sender:item.sender,message:item.message})));
      }
    }catch(reason){
      setError(errorMessage(reason,"Message could not be sent."));
      setMessages(current=>[...current,{sender:"Boss",message:text}]);
    }finally{setBusy(false)}
  };
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">Communication</p><h1>Team chat</h1><p className="subtitle">Persistent conversations and project handovers.</p></div><div className="report-actions"><button className={`secondary-button ${mode==="direct"?"selected":""}`} onClick={()=>setMode("direct")}>Employees</button><button className={`secondary-button ${mode==="team"?"selected":""}`} onClick={()=>setMode("team")}>Team room</button></div></header>
    {error&&<p className="form-error" role="alert">{error}</p>}
    <section className="chat-layout"><aside className="chat-list">{mode==="team"?<div className="chat-list-item"><div className="avatar">T</div><div><strong>Agency team</strong><br/><small>Shared handovers</small></div></div>:employees.map(employee=><button key={employee.id} className={`chat-list-item ${selected?.id===employee.id?"selected":""}`} onClick={()=>setSelected(employee)}><div className="avatar">{employee.initials}</div><div><strong>{employee.name}</strong><br/><small>{employee.title}</small></div></button>)}</aside>
      <div className="chat-window"><div className="chat-messages">{messages.length===0&&<p className="empty-state">Start a conversation. Direct AI responses use current agency records; team room messages and handovers are persisted.</p>}{messages.map((message,index)=><div className={`chat-bubble ${message.sender==="Boss"?"boss":""}`} key={index}><small>{message.sender}</small><p>{message.message}</p></div>)}</div>
        <div className="chat-input"><input value={input} onChange={event=>setInput(event.target.value)} onKeyDown={event=>event.key==="Enter"&&send()} placeholder={mode==="team"?"Message the team…":`Message ${selected?.name||"employee"}…`}/><button className="primary-button" disabled={busy||(mode==="direct"&&!selected)} onClick={send}>{busy?"…":"Send"}</button></div>
      </div>
    </section>
  </DashboardShell>;
}
