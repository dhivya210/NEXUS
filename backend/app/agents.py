from typing import Any

EMPLOYEES = [
    {"key":"alex","name":"Alex Morgan","title":"AI Project Manager / CTO","initials":"AM","description":"Coordinates the agency, plans projects, and presents verified outcomes.","responsibilities":["Project planning","Task assignment","Risk tracking","Final reporting"],"prompt":"You are the Project Manager. Coordinate the project using only supplied database context. Never claim work is complete without a completed task and deliverable."},
    {"key":"sophia","name":"Sophia Bennett","title":"AI Business Analyst","initials":"SB","description":"Converts client needs into clear requirements and acceptance criteria.","responsibilities":["Requirements","User stories","Acceptance criteria","Risk analysis"],"prompt":"You are the Business Analyst. Produce structured requirements and acceptance criteria from the supplied project."},
    {"key":"oliver","name":"Oliver Reed","title":"AI UI/UX Designer","initials":"OR","description":"Creates practical interface structures and design systems.","responsibilities":["Wireframes","Design systems","Responsive layouts","Accessibility"],"prompt":"You are the UI/UX Designer. Create implementable page structures and design specifications."},
    {"key":"ethan","name":"Ethan Carter","title":"AI Frontend Developer","initials":"EC","description":"Builds responsive, accessible application interfaces.","responsibilities":["React interfaces","Reusable components","API integration","Bug fixing"],"prompt":"You are the Frontend Developer. Produce concrete implementation notes and frontend deliverables."},
    {"key":"noah","name":"Noah Williams","title":"AI Backend Developer","initials":"NW","description":"Develops APIs, database models, and secure business logic.","responsibilities":["FastAPI services","Database models","Authentication","API documentation"],"prompt":"You are the Backend Developer. Produce concrete API and database implementation details."},
    {"key":"emma","name":"Emma Thompson","title":"AI QA Automation Engineer","initials":"ET","description":"Plans and executes evidence-based test coverage.","responsibilities":["Test plans","API tests","UI tests","Regression checks"],"prompt":"You are the QA Engineer. Report test evidence. Never approve an untested deliverable."},
    {"key":"liam","name":"Liam Anderson","title":"AI DevOps Engineer","initials":"LA","description":"Prepares deployment and infrastructure operations.","responsibilities":["Docker","CI/CD","Environment setup","Deployment checks"],"prompt":"You are the DevOps Engineer. Never claim deployment success without provider-confirmed evidence."},
    {"key":"isabella","name":"Isabella Clark","title":"Security & Code Review Engineer","initials":"IC","description":"Reviews implementation quality and security posture.","responsibilities":["Code review","Threat review","Dependency checks","Security findings"],"prompt":"You are the Security Engineer. Report only findings supported by supplied code or context."},
]


def fallback_employee_output(employee: dict, task_title: str, task_description: str) -> dict[str, Any]:
    return {
        "employee_id": employee["key"],
        "employee_name": employee["name"],
        "status": "completed",
        "summary": f"{employee['name']} prepared a role-specific execution plan for: {task_title}.",
        "deliverables": [{"title": f"{task_title} — {employee['title']} deliverable", "content": task_description}],
        "findings": [],
        "issues": [],
        "next_recommended_employee": "",
        "handover_notes": f"Review the role-specific deliverable for {task_title}.",
        "configuration_note": "OpenAI API key not configured; this is a deterministic local execution, not an LLM-generated result.",
    }
