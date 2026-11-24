# Delivery workflow

1. The Boss submits a client brief.
2. NEXUS creates the project and requirements/design/development/QA/DevOps/security tasks.
3. Project plan approval changes the project from planning to active.
4. Dependency links gate execution: frontend/backend work follows analysis and design; QA follows both implementations; deployment follows QA.
5. Each assigned employee executes with its role prompt and authorized task context.
6. The backend validates structured output, stores execution logs and deliverables, updates progress, and records the handover.
7. QA and security results remain separate recorded findings; deployment status is not inferred from task completion.

Execution fails clearly when the AI provider is not configured. Project completion is rejected until every task has a persisted deliverable.
