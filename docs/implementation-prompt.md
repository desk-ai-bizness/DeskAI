You are working inside this project repository and must implement one task at a time based on the task file I provide.

The repository root, together with `./docs` and `./tasks`, is the current planning and implementation source of truth for this project. If older notes elsewhere in the repository conflict with these files, prefer the root `README.md`, `./docs`, and `./tasks`.

Before doing anything else, read these files in this order:

1. `docs/mvp-business-rules.md`
2. `docs/mvp-technical-specs.md`
3. `docs/ai-context-rules.md`
4. The specific task file I assign
5. `tasks/@task-manager.md`

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
- AI prompts, transcript-oriented generation instructions, and product-facing copy must remain in Brazilian Portuguese (`pt-BR`) where applicable.
- User-facing product content must remain in Brazilian Portuguese (`pt-BR`) where applicable.
- Treat consultation and user data as sensitive.
- Never log raw medical content, PII, CPF, or unnecessary patient-identifiable data.
- Preserve the rule: report what was said, never interpret what it means.

Execution requirements:

- Implement the task completely end to end, not just partially.
- Make all necessary code, configuration, infrastructure, schema, test, and documentation changes required by the task.
- If the task reveals missing but necessary supporting work inside its scope, include it.
- If something is ambiguous or blocked by an undecided requirement, clearly document the blocker and proceed with the safest compliant implementation possible.
- Do not go outside the task scope unless it is required to make the task work correctly.
- For AI-processing work, enforce schema-validated outputs, evidence traceability, and incomplete-state handling instead of fabricated content.
- Keep timestamps and confidence metadata when the selected provider or pipeline makes them available.

Task tracking requirements:

- Always update `./tasks/@task-manager.md` after your work.
- When you start, mark the task appropriately in the task manager.
- When you finish, update status, progress, recent changes, blockers, and any milestone movement if relevant.
- If you discover a cross-task issue, add it to the `Open Issues` section in the task manager.

Commit convention:

- Use conventional commit style when proposing or creating commits.
- Examples: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`

Output requirements:

- Briefly summarize what you implemented.
- List the files changed.
- Mention any assumptions made.
- Mention any blockers or follow-up work.
- Confirm that `./tasks/@task-manager.md` was updated.

I will now give you the specific task file to implement.
