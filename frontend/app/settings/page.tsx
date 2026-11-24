"use client";
import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";

type Settings = { agency_name: string; daily_report_recipient: string; daily_report_enabled: boolean; daily_report_time: string; timezone: string };

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({ agency_name: "NEXUS", daily_report_recipient: "", daily_report_enabled: false, daily_report_time: "09:00", timezone: "Europe/Riga" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { fetch("/api/settings").then(async response => {
    if (!response.ok) throw new Error("Could not load workspace settings.");
    setSettings(await response.json());
  }).catch(reason => setError(reason.message)); }, []);
  const save = async () => {
    setError(""); setMessage("");
    try {
      const response = await fetch("/api/settings", { method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify(settings) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Could not save settings.");
      setSettings(result); setMessage("Settings saved.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save settings."); }
  };
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">Workspace</p><h1>Settings</h1><p className="subtitle">Agency profile and scheduled report preferences.</p></div></header>
    <section className="panel form-panel">
      <div className="field"><label htmlFor="agency">Agency name</label><input id="agency" value={settings.agency_name} onChange={event=>setSettings({...settings,agency_name:event.target.value})}/></div>
      <div className="field"><label htmlFor="recipient">Daily report recipient</label><input id="recipient" type="email" value={settings.daily_report_recipient} onChange={event=>setSettings({...settings,daily_report_recipient:event.target.value})} placeholder="boss@company.com"/></div>
      <div className="field"><label htmlFor="timezone">Time zone</label><select id="timezone" value={settings.timezone} onChange={event=>setSettings({...settings,timezone:event.target.value})}><option>Europe/Riga</option><option>UTC</option><option>Europe/London</option><option>America/New_York</option></select></div>
      <div className="field"><label htmlFor="report-time">Report time</label><input id="report-time" type="time" value={settings.daily_report_time} onChange={event=>setSettings({...settings,daily_report_time:event.target.value})}/></div>
      <label className="toggle-row"><input type="checkbox" checked={settings.daily_report_enabled} onChange={event=>setSettings({...settings,daily_report_enabled:event.target.checked})}/> Enable daily email report</label>
      {message&&<p className="success-message">{message}</p>}{error&&<p className="form-error" role="alert">{error}</p>}
      <button className="primary-button" onClick={save}>Save settings</button>
    </section></DashboardShell>;
}
