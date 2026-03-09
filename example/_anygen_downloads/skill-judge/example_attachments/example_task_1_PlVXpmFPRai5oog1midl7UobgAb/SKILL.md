# example-skill

## Overview
**Goal:** Help users complete a specific workflow efficiently and reliably.

This skill provides a clear, repeatable workflow that:
- collects the minimum required context,
- executes the workflow with verifiable steps,
- produces a clean deliverable in the workspace.

## When to Use
Use this skill when:
- User asks to perform the target workflow directly.
- User says: "use the skill" or "follow the skill".
- User requests a repeatable, step-by-step process related to the skill's domain.

Do **not** use this skill when:
- The user only wants a quick factual answer (no workflow needed).
- The task requires privileged access (accounts, credentials) that the user has not provided.

## Inputs (What the user should provide)
At minimum:
- **Objective:** What outcome they want (one sentence).

If applicable:
- **Scope constraints:** timeframe, regions, formats, success criteria.
- **Source constraints:** required URLs, internal docs, or “official sources only”.
- **Artifacts:** any existing files under `/home/user/workspace/upload/` to use as inputs.

If key inputs are missing, ask **one concise clarification question** (or use a form) before execution.

## Outputs (Deliverables)
Primary output:
- A workflow deliverable saved under `/home/user/workspace/` (format depends on the domain).

Always include:
- Clear filenames.
- A short summary of what was produced and where it is saved.

## Tools & Resources
This skill may use:
- **File I/O:** `sandbox_read_file`, `sandbox_write_file`
- **Shell scripting:** `sandbox_exec_command`
- **Web research:** `search_web`, `get_web_page_contents`

Optional (only if needed by the specific workflow):
- Browser automation: `browser_activate` (for JS-heavy sites)

## Workflow (Step-by-step)
1. **Confirm objective and constraints**
   - Restate the objective in one sentence.
   - Identify missing inputs (if any). If blocked, ask exactly one critical question.

2. **Collect required materials**
   - If sources are needed, use `search_web` with neutral queries.
   - For each key source, fetch full content with `get_web_page_contents`.
   - Prefer primary/official sources when facts or numbers matter.

3. **Process and validate**
   - Extract only relevant information.
   - Cross-check important claims across multiple sources.
   - If data is inconsistent, explicitly note uncertainty and cite differences.

4. **Execute the core workflow**
   - Use shell scripting for automation or batch tasks.
   - Use file I/O to read inputs and write outputs.
   - Keep steps deterministic and reproducible.

5. **Produce deliverable(s)**
   - Write final outputs to `/home/user/workspace/`.
   - Ensure filenames are descriptive and stable.

6. **Quality check**
   - Confirm the deliverable opens and contains the expected sections/data.
   - Verify links/citations (if any) are present and correct.

## Quality Checklist (Acceptance Criteria)
- [ ] Objective is clearly stated and matches user intent.
- [ ] Missing information was requested only when truly blocking.
- [ ] Sources (if used) are authoritative and retrievable.
- [ ] Output is saved to `/home/user/workspace/` with a clear name.
- [ ] Steps are reproducible; no hidden assumptions.
- [ ] Any uncertainty is explicitly labeled.

## Examples
### Example 1: Research-backed workflow output
**User:** “Follow the skill to compile a summary of recent policy changes on X.”

**Skill behavior:**
- Search official policy pages and credible reporting.
- Fetch the full text of 3–5 sources.
- Extract key dates, changes, and impacts.
- Write `Policy_Changes_X_Summary.md` to the workspace.

### Example 2: File-driven workflow
**User:** “Use the skill to clean and merge these CSV files.”

**Skill behavior:**
- Read CSV files from `/home/user/workspace/upload/`.
- Run a scripted merge/cleaning pipeline.
- Write `merged_clean.csv` and a short `README.md` describing the transformations.

## Edge Cases & Failure Handling
- **Paywalled / blocked pages:** fall back to alternative sources; if user-provided URL is required, attempt browser automation before asking the user.
- **Ambiguous objective:** ask one targeted clarification question.
- **Large outputs:** write to files instead of chat; provide a concise summary.
- **Tool errors:** diagnose from error messages, try an alternative approach, and avoid repeating the same failing command.
