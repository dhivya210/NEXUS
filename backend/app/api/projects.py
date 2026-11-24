from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..services.google_sheets import background_sync_tasks

router = APIRouter()


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).order_by(models.Project.created_at.desc()).all()
    return [{
        "id": p.id, "project_key": p.project_key, "name": p.name, "description": p.description,
        "status": p.status.value, "priority": p.priority, "progress": p.progress,
        "deadline": p.deadline, "client": p.client.name if p.client else "", "created_at": p.created_at,
        "task_count": len(p.tasks), "completed_tasks": sum(t.status == models.TaskStatus.completed for t in p.tasks)
    } for p in projects]


@router.post("")
def create_project(payload: schemas.ProjectCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    client = models.Client(name=payload.client_name, email=payload.client_email, company=payload.client_name)
    db.add(client)
    db.flush()
    project_key = f"NEX-{uuid4().hex[:6].upper()}"
    project = models.Project(
        project_key=project_key, name=payload.name, description=payload.description,
        priority=payload.priority, deadline=payload.deadline, client_id=client.id
    )
    db.add(project)
    db.flush()
    workflow = [
        ("Analyze project requirements", "Business requirement document and acceptance criteria", "sophia"),
        ("Create UI/UX specifications", "Wireframes, design system, and responsive layouts", "oliver"),
        ("Implement frontend experience", "Responsive UI components and API integration", "ethan"),
        ("Implement backend services", "Data models, APIs, and authentication", "noah"),
        ("Execute QA test plan", "Functional and integration test evidence", "emma"),
        ("Prepare deployment", "Container, environment, and deployment documentation", "liam"),
        ("Perform security review", "Code review and vulnerability findings", "isabella"),
    ]
    task_by_role = {}
    created_tasks = []
    for index, (title, description, employee_key) in enumerate(workflow):
        employee = db.query(models.Employee).filter(models.Employee.employee_key == employee_key).first()
        task = models.Task(task_key=f"{project_key}-T{index+1:02}", title=title, description=description,
                           project_id=project.id, employee_id=employee.id if employee else None,
                           priority="high" if index < 2 else "medium",
                           status=models.TaskStatus.queued)
        db.add(task)
        db.flush()
        task_by_role[employee_key] = task
        created_tasks.append((employee_key, task))
    dependencies = {
        "ethan": ["sophia", "oliver"],
        "noah": ["sophia"],
        "emma": ["ethan", "noah"],
        "liam": ["emma"],
        "isabella": ["ethan", "noah"],
    }
    for role, prerequisites in dependencies.items():
        for prerequisite in prerequisites:
            db.add(models.TaskDependency(task_id=task_by_role[role].id, depends_on_id=task_by_role[prerequisite].id))
    db.add(models.ActivityLog(type="project_created", title=f"Project created: {project.name}",
                              detail=f"Client project {project.project_key} entered planning with seven specialist tasks.", project_id=project.id))
    db.commit()
    db.refresh(project)
    background_tasks.add_task(background_sync_tasks)
    return {"id": project.id, "project_key": project.project_key, "name": project.name, "status": project.status.value}


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return {
        "id": p.id, "project_key": p.project_key, "name": p.name, "description": p.description,
        "status": p.status.value, "priority": p.priority, "progress": p.progress, "deadline": p.deadline,
        "client": {"name": p.client.name, "email": p.client.email} if p.client else None,
        "tasks": [{"id": t.id, "task_key": t.task_key, "title": t.title, "status": t.status.value,
                   "employee": t.employee.name if t.employee else None} for t in p.tasks],
        "deliverables": [{"id": d.id, "title": d.title, "kind": d.kind, "created_at": d.created_at}
                         for t in p.tasks for d in t.deliverables],
        "created_at": p.created_at
    }


@router.patch("/{project_id}")
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    p = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "status":
            try:
                value = models.ProjectStatus(value)
            except ValueError as exc:
                raise HTTPException(422, "Invalid project status") from exc
            if value == models.ProjectStatus.completed and any(
                task.status != models.TaskStatus.completed or not task.deliverables for task in p.tasks
            ):
                raise HTTPException(409, "A project requires completed tasks with deliverables before final delivery.")
        setattr(p, key, value)
    db.commit()
    return {"id": p.id, "status": p.status.value, "progress": p.progress}


@router.post("/{project_id}/approve-plan")
def approve_plan(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status != models.ProjectStatus.planning:
        raise HTTPException(409, "Only projects in planning can be approved.")
    project.status = models.ProjectStatus.active
    db.add(models.ActivityLog(type="plan_approved", title=f"Plan approved: {project.name}",
                             detail="Project plan approved and the workflow is active.", project_id=project.id))
    db.commit()
    return {"id": project.id, "status": project.status.value}


@router.post("/{project_id}/qa/run")
def run_project_integrity_checks(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    checks = [
        ("Tasks have assigned employees", [
            task for task in project.tasks if task.employee_id is None
        ]),
        ("Completed tasks have deliverables", [
            task for task in project.tasks
            if task.status == models.TaskStatus.completed and not task.deliverables
        ]),
        ("Task dependencies are within this project", [
            db.get(models.Task, link.task_id)
            for link in db.query(models.TaskDependency).all()
            if db.get(models.Task, link.task_id)
            and db.get(models.Task, link.task_id).project_id == project.id
            and (
                not db.get(models.Task, link.depends_on_id)
                or db.get(models.Task, link.depends_on_id).project_id != project.id
            )
        ]),
    ]
    results = []
    for title, failures in checks:
        case = db.query(models.TestCase).filter(
            models.TestCase.project_id == project_id, models.TestCase.title == title
        ).first()
        if not case:
            case = models.TestCase(
                project_id=project_id,
                title=title,
                steps="Run a backend project-ledger integrity check.",
                expected_result="No database records violate this condition.",
            )
            db.add(case)
            db.flush()
        status = "passed" if not failures else "failed"
        actual = "No violations found." if not failures else f"{len(failures)} violation(s) found."
        execution = models.TestExecution(test_case_id=case.id, actual_result=actual, status=status)
        db.add(execution)
        results.append({"test_case_id": case.id, "title": title, "status": status, "actual_result": actual})
        if failures:
            db.add(models.BugReport(
                project_id=project_id,
                title=f"Integrity check failed: {title}",
                description=actual,
                severity="high",
                status="open",
            ))
    passed = all(result["status"] == "passed" for result in results)
    db.add(models.ActivityLog(type="qa_integrity_check", title=f"Project integrity checks: {project.name}",
                              detail=f"{sum(result['status'] == 'passed' for result in results)} of {len(results)} checks passed.",
                              project_id=project_id))
    db.commit()
    return {"project_id": project.id, "status": "passed" if passed else "failed", "checks": results,
            "scope": "Database workflow integrity only; this does not represent product UI or API testing."}
