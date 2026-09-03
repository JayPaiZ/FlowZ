# Global agent instructions

## Completion reports

When a task, milestone, or implementation phase is complete, make the final response action-oriented rather than reporting status alone. Unless the user requested exact wording, a minimal acknowledgement, or no recommendations, include:

- the single recommended next step, stated concretely and prioritized;
- whether the user needs to do anything now, and the exact action or decision if so;
- up to two optional follow-up suggestions when they provide clear value.

If the next step is safe and within the user's existing authorization, offer to continue or proceed instead of shifting routine work to the user. Do not automatically start a materially different phase, change external state, or broaden scope merely because it is recommended.

Do not invent a low-value next step merely to avoid stating completion.

## Working conventions

- Before changing anything, inspect the relevant code, documents, tests, and current runtime state.
- If the project is a Git repository, inspect its Git status before editing. If it is not a Git repository, use the project state that is available and do not present the absence of Git as a problem by itself.
- Preserve existing user changes. Do not restore, overwrite, delete, stage, or broaden them without authorization.
- Prefer existing components, dependencies, scripts, and project patterns before introducing new ones.
- Use evidence in reports. Do not describe an unrun check as passed or replace verification with “should work”.
