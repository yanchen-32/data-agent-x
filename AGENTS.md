# DataAgentX Repository Guidance

## Project documents

Treat the following files as the durable source of truth for the project:

- `docs/PROJECT_CHARTER.md` defines why DataAgentX exists, its technical boundaries, priorities, non-goals, evaluation philosophy, and success criteria.
- `docs/ROADMAP.md` tracks milestone-level progress. Do not add daily schedules, study plans, or chat task lists.
- `docs/ARCHITECTURE.md` describes the system that is implemented now. Do not use it as a speculative future-state design document.

## Maintenance rules

- Keep the charter stable. Change it only when the project's positioning or technical boundaries genuinely change.
- Update roadmap checkboxes only when the repository contains enough implementation or evidence to support the new status.
- Update the architecture document in the same change when implementation decisions make it inaccurate.
- Keep plans and aspirations in the roadmap; keep verified current behavior in the architecture document.
- Record durable project facts and technical decisions in the repository. Do not store chat prompts, conversational history, or day-by-day personal schedules here.
- Preserve the explicit non-goals. Do not add infrastructure or technology solely to increase the size of the stack.
- Do not claim benchmark, reliability, retrieval, memory, or gateway results without reproducible evidence.
