import os
from pathlib import Path
from tempfile import gettempdir

os.environ["DATABASE_URL"] = f"sqlite:///{Path(gettempdir()) / 'nexus_api_tests.db'}"
os.environ["NEXUS_ADMIN_EMAIL"] = "boss@example.test"
os.environ["NEXUS_ADMIN_PASSWORD"] = "test-only-password"
os.environ["NEXUS_SECRET_KEY"] = "test-signing-key-with-at-least-32-characters"
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def sign_in():
    response = client.post(
        "/api/auth/login",
        json={"email": "boss@example.test", "password": "test-only-password"},
    )
    assert response.status_code == 200


def test_health_is_public():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_requires_login():
    unauthenticated = TestClient(app)
    assert unauthenticated.get("/api/employees").status_code == 401


def test_login_and_eight_employee_profiles():
    sign_in()
    response = client.get("/api/employees")
    assert response.status_code == 200
    assert len(response.json()) == 8
    assert client.get("/api/auth/me").json()["email"] == "boss@example.test"


def test_project_creation_creates_workflow_and_dependencies():
    sign_in()
    response = client.post(
        "/api/projects",
        json={"name": "Test portal", "description": "A test project request.", "client_name": "Test Client"},
    )
    assert response.status_code == 200
    project_id = response.json()["id"]
    project = client.get(f"/api/projects/{project_id}").json()
    assert len(project["tasks"]) == 7
    frontend_task = next(task for task in project["tasks"] if task["title"] == "Implement frontend experience")
    dependencies = client.get(f"/api/tasks/{frontend_task['id']}").json()["dependencies"]
    assert len(dependencies) == 2
    assert client.post(f"/api/projects/{project_id}/approve-plan").json()["status"] == "active"
    qa = client.post(f"/api/projects/{project_id}/qa/run")
    assert qa.status_code == 200
    assert qa.json()["status"] == "passed"
    assert "does not represent product UI" in qa.json()["scope"]


def test_ai_execution_requires_configuration_and_does_not_fake_completion():
    sign_in()
    project = client.post(
        "/api/projects",
        json={"name": "AI config test", "description": "Verify AI provider configuration.", "client_name": "Test"},
    ).json()
    tasks = client.get(f"/api/tasks?project_id={project['id']}").json()
    requirements = next(task for task in tasks if task["title"] == "Analyze project requirements")
    assert client.post(f"/api/tasks/{requirements['id']}/execute").status_code == 503
    persisted = client.get(f"/api/tasks/{requirements['id']}").json()
    assert persisted["status"] == "queued"
    assert persisted["deliverables"] == []


def test_completed_status_requires_deliverable():
    sign_in()
    tasks = client.get("/api/tasks").json()
    task = next(item for item in tasks if item["status"] == "queued")
    response = client.patch(f"/api/tasks/{task['id']}", params={"status": "completed"})
    assert response.status_code == 409


def test_employee_chat_does_not_fake_unconfigured_ai():
    sign_in()
    response = client.post("/api/employees/1/chat", json={"message": "What are you working on?"})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_integration_failures_are_reported_not_marked_successful():
    sign_in()
    sheets = client.post("/api/integrations/google-sheets/sync")
    email = client.post("/api/reports/email/send", json={"recipient": "boss@example.com"})
    assert sheets.status_code == 503
    assert email.status_code == 503
