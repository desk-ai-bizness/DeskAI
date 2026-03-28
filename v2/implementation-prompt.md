You are working inside this project repository and must implement one task at a time based on the task file I provide.

Before doing anything else, read these files in this order:

1. `./docs/ai-context-rules.md`
2. `./docs/mvp-business-rules.md`
3. `./docs/mvp-technical-specs.md`
4. The specific task file I assign
5. `./tasks/@task-manager.md`

Your job is to fully implement the assigned task in the codebase, following all business rules, technical specs, architecture constraints, and clean code expectations defined in those files.

Core instructions:

- Always follow the guidance in `./docs/ai-context-rules.md`.
- Treat `./docs/mvp-business-rules.md` as the source of truth for business behavior and product boundaries.
- Treat `./docs/mvp-technical-specs.md` as the source of truth for architecture, stack, infrastructure, and system design decisions.
- Respect the assigned task file as the execution scope for this implementation.
- Do not invent product behavior that is not documented.
- Keep solutions explicit, maintainable, testable, and aligned with Hexagonal Architecture and separation of concerns.
- Keep business logic out of the frontend.
- Keep the frontend backend-driven wherever practical.
- Code, comments, and documentation must be written in English.
- User-facing product content must remain in Brazilian Portuguese (`pt-BR`) where applicable.
- Treat consultation and user data as sensitive.

Execution requirements:

- Implement the task completely end to end, not just partially.
- Make all necessary code, configuration, infrastructure, schema, test, and documentation changes required by the task.
- If the task reveals missing but necessary supporting work inside its scope, include it.
- If something is ambiguous or blocked by an undecided requirement, clearly document the blocker and proceed with the safest compliant implementation possible.
- Do not go outside the task scope unless it is required to make the task work correctly.

Task tracking requirements:

- Always update `./tasks/@task-manager.md` after your work.
- When you start, mark the task appropriately in the task manager.
- When you finish, update status, progress, recent changes, blockers, and any milestone movement if relevant.
- If you discover a cross-task issue, add it to the `Open Issues` section in the task manager.

Output requirements:

- Briefly summarize what you implemented.
- List the files changed.
- Mention any assumptions made.
- Mention any blockers or follow-up work.
- Confirm that `./tasks/@task-manager.md` was updated.

I will now give you the specific task file to implement.
