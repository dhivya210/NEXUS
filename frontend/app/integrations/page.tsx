"use client";
import { useCallback, useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import { apiJson, errorMessage } from "@/lib/api";
import type { IntegrationInfo } from "@/lib/types";

export default function IntegrationsPage() {
  const [items, setItems] = useState<IntegrationInfo[]>([]);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  const load = useCallback(() => apiJson<IntegrationInfo[]>("/api/integrations").then(setItems).catch(reason => setError(errorMessage(reason,"Could not load integrations."))),[]);
  useEffect(() => { void load(); }, [load]);
  const sync = async () => {
    setSyncing(true); setError(""); setSyncMessage("");
    try {
      const result = await apiJson<{synchronized:number;inserted:number;updated:number}>("/api/integrations/google-sheets/sync", { method:"POST" });
      setSyncMessage(`Synchronized ${result.synchronized} tasks (${result.inserted} new, ${result.updated} updated).`);
      await load();
    } catch (reason) { setError(errorMessage(reason,"Google Sheets sync failed.")); }
    finally { setSyncing(false); }
  };
  return <DashboardShell><header className="page-header"><div><p className="eyebrow">Connected services</p><h1>Integrations</h1><p className="subtitle">External services and credential health.</p></div></header>
    {error&&<p className="form-error" role="alert">{error}</p>}{syncMessage&&<p className="success-message">{syncMessage}</p>}
    <section className="integrations-grid">{items.map(item=><article className="integration-card" key={item.type}><div className="avatar">{item.name.slice(0,2)}</div><h3>{item.name}</h3><p>{item.description}</p><span className={`integration-state ${item.connected?"connected":""}`}>{item.connected?"Connected":item.configured?"Configured · not verified":"Not configured"}</span><p>{item.error||"Credentials are present; provider connection is verified on first operation."}</p>{item.type==="google_sheets"&&<button className="secondary-button" disabled={syncing} onClick={sync}>{syncing?"Syncing…":"Sync tasks now"}</button>}</article>)}</section>
  </DashboardShell>;
}
