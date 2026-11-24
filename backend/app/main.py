from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from .core.auth import require_session
from .database import engine, Base
from . import models
from .database import SessionLocal
from .agents import EMPLOYEES
from .api import auth, projects, tasks, employees, reports, integrations, activity, ai, settings, automation, team
from .services.scheduler import start_scheduler, stop_scheduler

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="NEXUS Autonomous IT Agency", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
protected = [Depends(require_session)]
app.include_router(projects.router, prefix="/api/projects", tags=["projects"], dependencies=protected)
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"], dependencies=protected)
app.include_router(employees.router, prefix="/api/employees", tags=["employees"], dependencies=protected)
app.include_router(reports.router, prefix="/api/reports", tags=["reports"], dependencies=protected)
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"], dependencies=protected)
app.include_router(activity.router, prefix="/api/activity", tags=["activity"], dependencies=protected)
app.include_router(ai.router, prefix="/api/ai", tags=["ai"], dependencies=protected)
app.include_router(settings.router, prefix="/api/settings", tags=["settings"], dependencies=protected)
app.include_router(automation.router, prefix="/api/automation", tags=["automation"], dependencies=protected)
app.include_router(team.router, prefix="/api/team", tags=["team"], dependencies=protected)


def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.Employee).count() == 0:
            for profile in EMPLOYEES:
                db.add(models.Employee(
                    employee_key=profile["key"], name=profile["name"], title=profile["title"],
                    initials=profile["initials"], description=profile["description"],
                    responsibilities=profile["responsibilities"], system_prompt=profile["prompt"],
                    status="idle"
                ))
            db.commit()

        if db.query(models.Project).count() == 0:
            client = models.Client(name="Riga Student Union", email="projects@studentunion.lv", company="Riga Student Union")
            db.add(client)
            db.flush()
            project = models.Project(
                project_key="NEX-SAMPLE", name="University Events Portal (sample)",
                description="Sample university event discovery, registration, and administration project.",
                status=models.ProjectStatus.active, priority="high", progress=0, client_id=client.id
            )
            db.add(project)
            db.flush()
            seed_tasks = [
                ("Requirements analysis", "Analyze event workflows, audiences, risks, and acceptance criteria.", "sophia", "queued"),
                ("Experience design", "Create responsive event discovery and registration layouts.", "oliver", "queued"),
                ("Frontend implementation", "Build event cards, registration flows, and dashboard views.", "ethan", "queued"),
                ("Backend and database", "Implement events, users, registrations, and secure APIs.", "noah", "queued"),
                ("QA test suite", "Verify registration, filtering, and authentication flows.", "emma", "queued"),
                ("Deployment setup", "Prepare Docker and hosting configuration.", "liam", "queued"),
                ("Security and code review", "Review authentication and application security.", "isabella", "queued"),
            ]
            for index, (title, description, employee_key, status) in enumerate(seed_tasks):
                employee = db.query(models.Employee).filter(models.Employee.employee_key == employee_key).first()
                task = models.Task(
                    task_key=f"NEX-SAMPLE-T{index + 1:02}", title=title, description=description,
                    status=models.TaskStatus(status), priority="high" if index < 2 else "medium",
                    project_id=project.id, employee_id=employee.id
                )
                db.add(task)
                db.flush()
                if employee_key == "ethan":
                    requirements = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == "NEX-SAMPLE-T01").first()
                    design = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == "NEX-SAMPLE-T02").first()
                    db.add(models.TaskDependency(task_id=task.id, depends_on_id=requirements.id))
                    db.add(models.TaskDependency(task_id=task.id, depends_on_id=design.id))
                elif employee_key == "noah":
                    requirements = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == "NEX-SAMPLE-T01").first()
                    db.add(models.TaskDependency(task_id=task.id, depends_on_id=requirements.id))
                elif employee_key == "emma":
                    for task_key in ("NEX-SAMPLE-T03", "NEX-SAMPLE-T04"):
                        prerequisite = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == task_key).first()
                        db.add(models.TaskDependency(task_id=task.id, depends_on_id=prerequisite.id))
                elif employee_key == "liam":
                    prerequisite = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == "NEX-SAMPLE-T05").first()
                    db.add(models.TaskDependency(task_id=task.id, depends_on_id=prerequisite.id))
                elif employee_key == "isabella":
                    for task_key in ("NEX-SAMPLE-T03", "NEX-SAMPLE-T04"):
                        prerequisite = db.query(models.Task).filter(models.Task.project_id == project.id, models.Task.task_key == task_key).first()
                        db.add(models.TaskDependency(task_id=task.id, depends_on_id=prerequisite.id))
            db.add(models.ActivityLog(type="project_created", title="Project created: University Events Portal",
                                      detail="Riga Student Union submitted a new client project.", project_id=project.id))
            db.commit()
    finally:
        db.close()


seed_database()


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "connected"}
