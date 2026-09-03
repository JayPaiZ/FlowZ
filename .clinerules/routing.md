# Workflow routing

When working in a repository that uses this workflow:

1. Read the repository `AGENTS.md` and any applicable project-layer documents before changing files.
2. Apply `.clinerules/workflows/document-workflow-v0.1.md` to triage the request as Quick, Standard, or Full and to select optional capabilities only when needed.
3. If the request is more than a lightweight edit, locate or create a `.workflow/tasks/*.md` task and use the task's acceptance criteria as the working target.
4. Use the project's documented context-selection command when a task exists. Treat its order as the context selection contract.
5. Move task state with the project's task-state mechanism; do not claim completion from an agent message alone. Verification may be automated evidence or explicit human confirmation.
6. At completion, check for durable knowledge and update the appropriate `.workflow/project/` document only when the lesson is useful beyond this task.

This routing is additive. Continue to use any skills, plugins, MCP servers, procedures, or tools installed or selected by the developer. This file does not restrict them.
