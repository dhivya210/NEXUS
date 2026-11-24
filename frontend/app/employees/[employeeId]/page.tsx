import { Suspense } from "react";
import EmployeeProfileClient from "@/components/employee-profile-client";

export default function EmployeeProfilePage() {
  return <Suspense fallback={<div className="auth-loading">Loading employee…</div>}><EmployeeProfileClient /></Suspense>;
}
