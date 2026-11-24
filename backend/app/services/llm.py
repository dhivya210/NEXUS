import json
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from ..agents import EMPLOYEES

class DeliverableOutput(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class AgentWorkOutput(BaseModel):
    summary: str = Field(min_length=1)
    deliverables: list[DeliverableOutput] = Field(min_length=1)
    findings: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    next_recommended_employee: str = ""
    handover_notes: str = ""


async def _completion(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI execution is not configured. Set OPENAI_API_KEY and restart the backend.",
        )
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                },
            )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="AI provider timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider returned HTTP {exc.response.status_code}. Check the configured model and API key.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the AI provider.") from exc
    try:
        body = response.json()
        return body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc


async def execute_employee_task(employee: Any, task: Any, project: Any) -> dict[str, Any]:
    system_prompt = (
        f"{employee.system_prompt}\n"
        f"Your assigned professional role is {employee.title}. "
        "You may only produce a deliverable for the assigned task. Never claim tests, deployment, "
        "or code changes actually happened unless evidence is included in task context. "
        "Return a JSON object with summary (string), deliverables (non-empty array of {title, content}), "
        "findings (string array), issues (string array), next_recommended_employee (string), "
        "and handover_notes (string)."
    )
    user_prompt = json.dumps({
        "task": {"id": task.task_key, "title": task.title, "description": task.description},
        "project": {"key": project.project_key, "name": project.name, "requirements": project.description},
        "authorized_context": task.input_context or {},
    })
    content = await _completion(system_prompt, user_prompt)
    try:
        result = AgentWorkOutput.model_validate_json(content)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="AI response did not match the required deliverable format.") from exc
    valid_employee_keys = {profile["key"] for profile in EMPLOYEES}
    if result.next_recommended_employee and result.next_recommended_employee not in valid_employee_keys:
        raise HTTPException(status_code=502, detail="AI response referenced an unknown next employee.")
    return {
        "employee_id": employee.employee_key,
        "employee_name": employee.name,
        "task_id": task.task_key,
        "status": "completed",
        **result.model_dump(),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def chat_with_employee(employee: Any, message: str, context: dict[str, Any], history: list[dict[str, str]]) -> str:
    system_prompt = (
        f"{employee.system_prompt}\n"
        f"You are speaking as {employee.name}, {employee.title}. "
        "Answer based only on the supplied current database context and recent conversation. "
        "Clearly state when the context does not contain an answer. Never invent work, outcomes, test results, or deployments."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Current database context: {json.dumps(context)}"},
    ]
    messages.extend(history[-12:])
    messages.append({"role": "user", "content": message})
    raw = await _completion_messages(messages)
    return raw.strip()


async def _completion_messages(messages: list[dict[str, str]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="AI chat is not configured. Set OPENAI_API_KEY and restart the backend.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages, "temperature": 0.3},
            )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="AI provider timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider returned HTTP {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to the AI provider.") from exc
    try:
        return response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc
