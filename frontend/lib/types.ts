export type TaskStatus = "queued" | "in_progress" | "blocked" | "completed" | "cancelled";
export type ProjectStatus = "planning" | "active" | "paused" | "completed" | "cancelled";

export interface EmployeeSummary {
  id: number;
  employee_key: string;
  name: string;
  title: string;
  initials: string;
  description: string;
  status: string;
  responsibilities: string[];
  completed_tasks: number;
  pending_tasks: number;
  blocked_tasks: number;
  current_assignment?: string | null;
}

export interface EmployeeTask {
  id: number;
  task_key: string;
  title: string;
  status: TaskStatus;
}

export interface EmployeeProfile extends EmployeeSummary {
  system_prompt: string;
  tasks: EmployeeTask[];
}

export interface EmployeeReport {
  id: number;
  name: string;
  title: string;
  assigned: number;
  completed: number;
  pending: number;
  blocked: number;
}

export interface EmployeePerformance {
  employee_id: number;
  name: string;
  assigned: number;
  completed: number;
  pending: number;
  blocked: number;
  average_completion_hours: number | null;
  completion_rate: number | null;
  tasks: { task_key: string; title: string; status: TaskStatus }[];
}

export interface ProjectSummary {
  id: number;
  project_key: string;
  name: string;
  description: string;
  status: ProjectStatus;
  priority: string;
  progress: number;
  deadline: string | null;
  client: string;
  created_at: string;
  task_count: number;
  completed_tasks: number;
}

export interface ProjectTask {
  id: number;
  task_key: string;
  title: string;
  status: TaskStatus;
  employee: string | null;
}

export interface ProjectDetail extends Omit<ProjectSummary, "client" | "task_count" | "completed_tasks"> {
  client: { name: string; email: string } | null;
  tasks: ProjectTask[];
  deliverables: { id: number; title: string; kind: string; created_at: string }[];
}

export interface ProjectQaResult {
  project_id: number;
  status: string;
  scope: string;
  checks: { test_case_id: number; title: string; status: string; actual_result: string }[];
}

export interface TaskSummary {
  id: number;
  task_key: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: string;
  project: string;
  project_key: string;
  employee: string | null;
  employee_id: number | null;
  started_at: string | null;
  completed_at: string | null;
  error_detail: string | null;
  dependencies?: { id: number; task_key: string; title: string; status: TaskStatus }[];
}

export interface TaskDetail {
  id: number;
  task_key: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: string;
  project: string;
  employee: string | null;
  error_detail: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  input_context: Record<string, unknown>;
  dependencies: { id: number; task_key: string; status: TaskStatus }[];
  deliverables: { title: string; content: string; created_at: string }[];
  executions: {
    id: number;
    status: string;
    summary: string;
    error_detail: string | null;
    started_at: string;
    completed_at: string | null;
  }[];
}

export interface ActivityEntry {
  id: number;
  type: string;
  title: string;
  detail: string;
  created_at: string;
}

export interface AgencyReport {
  total_tasks: number;
  completed_tasks: number;
  completed_today: number;
  in_progress: number;
  blocked: number;
  projects: number;
  delivered_projects: number;
  status_distribution: Record<string, number>;
  employee_distribution: { name: string; completed: number; active: number }[];
  average_completion_hours: number | null;
  qa_pass_rate: number | null;
  qa_tests_executed: number;
  deployment_success_rate: number | null;
  deployments_recorded: number;
}

export interface CompletionTrend {
  date: string;
  completed: number;
}

export interface EmailHistoryEntry {
  id: number;
  recipient: string;
  subject: string;
  status: string;
  detail: string;
  created_at: string;
}

export interface IntegrationInfo {
  name: string;
  type: string;
  configured: boolean;
  connected: boolean;
  description: string;
  last_sync: string | null;
  error: string;
}

export interface ChatRecord {
  sender: string;
  message: string;
}

export interface TeamChatMessage extends ChatRecord {
  id: number;
  receiver: string;
  project_id: number | null;
  task_id: number | null;
  created_at: string;
}

export interface ApiError {
  detail?: string | { message?: string };
}
