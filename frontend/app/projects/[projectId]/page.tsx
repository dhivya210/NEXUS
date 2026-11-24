import { Suspense } from "react";
import ProjectDetailClient from "@/components/project-detail-client";

export default function ProjectDetailPage() {
  return <Suspense fallback={<div className="auth-loading">Loading project…</div>}><ProjectDetailClient /></Suspense>;
}
