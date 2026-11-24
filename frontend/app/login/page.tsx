"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Sign in failed.");
      router.replace("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not reach the NEXUS server.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-page"><form className="panel login-card" onSubmit={submit}>
    <div className="brand login-brand"><div className="brand-mark"><Sparkles size={16}/></div><span>nexus</span></div>
    <p className="eyebrow">Boss workspace</p><h1>Welcome back</h1><p className="subtitle">Sign in to your agency command center.</p>
    <div className="field"><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="username" required value={email} onChange={event=>setEmail(event.target.value)}/></div>
    <div className="field"><label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" required value={password} onChange={event=>setPassword(event.target.value)}/></div>
    {error&&<p className="form-error" role="alert">{error}</p>}
    <button className="primary-button login-submit" disabled={busy}>{busy?"Signing in…":"Sign in"}</button>
    <p className="login-note">Configure <code>NEXUS_ADMIN_EMAIL</code>, <code>NEXUS_ADMIN_PASSWORD</code>, and <code>NEXUS_SECRET_KEY</code> in your backend environment.</p>
  </form></main>;
}
