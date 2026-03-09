# Product Process Discussion — Notes (working draft)

**Date:** 2026-02-13 (Fri)

**Time:** 15:00–16:20 (80 mins)

**Location / Link:** Zoom (internal) + Conf Room B3

**Organizer:** Annie (PMO)

**Facilitator:** Leo (Lead PM)

**Note-taker:** Annie

---

## Attendees
- Leo — Lead PM
- Annie — PMO / Ops
- Mia — Product Manager (Growth)
- Sam — Engineering Manager (FE)
- Rohan — Engineering Manager (BE)
- Kelly — Design Lead
- Jing — Data Analyst
- Nina — QA Lead
- Tom — Customer Support Lead

---

## Why we met (context)
We’ve been shipping, but the process is getting noisy:
- too many last-minute changes
- “status” lives in 3–4 places
- QA gets pulled in late
- analytics instrumentation often comes after release

Leo: “We don’t need a heavy process. We need a *predictable* one.”

**Goal today:** agree on a lightweight end-to-end flow + definitions of done, and pick 2–3 changes we can pilot next sprint.

---

## 1) Quick snapshot of current workflow (“as-is”)
This is what we *think* we do:
1. Idea in chat / doc → PM writes something quick
2. Design starts (sometimes w/ incomplete AC)
3. Eng starts based on screenshots + a few bullets
4. QA enters close to code complete
5. Release happens when “it looks ok”
6. Metrics / dashboards get created later (or never)

Tools currently involved:
- Requirements: Notion + random Google Docs
- Tasks: Jira (sometimes) + Feishu sheets (sometimes)
- Design: Figma
- Comms: Slack/Feishu groups
- Release tracking: Jira + release channel

**Big issue:** there is no “single source of truth”, so people use whatever is fastest in the moment.

---

## 2) Data points we surfaced (rough but directionally true)
Jing brought some numbers (last 8 weeks, Growth squad):
- Avg cycle time (PRD approved → release): **19.6 days**
- Median cycle time: **16 days**
- P90 cycle time: **34 days**
- Rework after dev start (tickets reopened / major scope change): **~28%**
- Bugs found after release (sev2+ within 7 days): **avg 3.1 / release**
- Instrumentation missing on first release: **~40% of features** (events added 1–2 weeks later)

Sam: “The cycle time isn’t terrible, it’s the variance. We can’t plan.”

Tom (Support): top complaint themes since Jan:
- “I can’t find X anymore” (UI changes not announced)
- “This flow is confusing” (copy + edge cases)
- “Bug in onboarding steps” (QA late + device coverage)

---

## 3) Pain points (captured live)
### a) Requirements quality / clarity
- PRDs vary a lot (some are great, some are 1 page with no AC)
- Acceptance criteria often missing edge cases
- “We’ll decide later” becomes “we decided in a DM”

Kelly: “Design reviews become requirement debates.”

### b) Handoffs are implicit
- Design → Eng handoff not explicit (no checklist)
- Eng → QA handoff not explicit (QA gets a Jira link + ‘pls test’)

Nina: “QA needs at least 2 days lead time for test plan and devices.”

### c) Scope churn
- Stakeholders ask for “small tweaks” late
- No agreed rule for what changes are allowed after dev start

Rohan: “We spend more time negotiating changes than building.”

### d) Analytics late / inconsistent
- Event naming not consistent
- Some features ship without a metric definition

Jing: “If we can’t measure it, we can’t learn, and we keep debating opinions.”

---

## 4) What “good” looks like (principles we agreed)
Not trying to copy a big-company process. Minimal rules:
1. **One source of truth** per feature: a single “Feature Page” (Notion template) that links out.
2. **Clear stage gates** with lightweight DoD, mostly checklists.
3. **Metrics before build** (at least 1–2 primary metrics + guardrails).
4. **Earlier QA + analytics** (pull them into PRD review).
5. **Change control**: after Dev Start, only changes that meet a simple rule.

Leo: “If a change adds >0.5 day work or affects tracking/UX, it’s not a ‘small tweak’.”

---

## 5) Proposed “to-be” flow (v0.1, pilot-ready)
### Stage 0 — Intake (1–2 days)
**Owner:** PM

**DoD checklist:**
- Problem statement (who + what pain)
- Why now (data or support signal)
- Success metrics (draft)
- Non-goals
- Rough scope + constraints

Output: **Feature Page** created.

### Stage 1 — PRD + Review (2–4 days)
**Owner:** PM

**Required reviewers:** Design lead + Eng manager + QA + Data

**DoD checklist:**
- User stories + acceptance criteria (edge cases included)
- API / tech considerations captured (even if “TBD”)
- Tracking plan: events + properties + dashboard owner
- Rollout strategy (100% / staged / experiment)
- Dependencies listed with owners

Decision point: **“Dev Start”** only after PRD sign-off.

### Stage 2 — Design (3–7 days depending)
**Owner:** Design

**DoD checklist:**
- Figma link + specs + states/edge cases
- Copy reviewed (CS + PM)
- Eng feasibility reviewed

### Stage 3 — Build (5–10 days typical)
**Owner:** Eng

**DoD checklist:**
- Jira breakdown + estimates
- Tracking implemented (events QA-ready)
- Feature flag / config plan

### Stage 4 — QA + UAT (2–5 days)
**Owner:** QA

**DoD checklist:**
- Test plan exists
- Device matrix defined
- Sev1/Sev2 closed
- UAT sign-off (PM + Design)

### Stage 5 — Release + Monitor (day 0 → day 7)
**Owner:** PM + Data

**DoD checklist:**
- Release note posted in release channel
- Dashboard live (primary metrics + guardrails)
- Watch window defined (who watches what)

### Stage 6 — Post-Release Review (30 mins)
**When:** within 7–10 days

**DoD checklist:**
- What happened vs expected
- What we learned
- Follow-ups created (bugs, iteration, rollback if needed)

---

## 6) The “change rule” (simple)
After **Dev Start**:
- If change impacts UX flow, tracking, or adds **>0.5 engineer-day**, it requires a quick **Change Review** (15 mins) with: PM + Eng + Design + QA.
- Otherwise PM can approve and just update the Feature Page + Jira.

Everyone agreed this is mainly to prevent silent scope creep.

---

## 7) Decisions (made today)
1. **We will pilot the Feature Page template** starting next sprint (Growth squad only).
   - Rationale: reduce scattered context and “where is the latest?”

2. **QA + Data become required reviewers at PRD stage.**
   - Rationale: pull risk discovery earlier.

3. **We adopt the change rule after Dev Start** (0.5 engineer-day threshold).
   - Rationale: stop late scope churn from derailing plans.

4. **We will track 3 process metrics** weekly for the pilot:
   - Cycle time (PRD sign-off → release)
   - Rework rate (tickets reopened / scope changes)
   - Instrumentation completeness at release

---

## 8) Open questions
- Do we keep Notion as the “Feature Page” home, or move to Feishu Docs to match other teams?
  - Owner: Annie to check constraints + permissions

- What is the minimum acceptable acceptance-criteria format?
  - Owner: Leo to propose a short AC template

- For experiments: do we require a standard analysis plan before launch?
  - Owner: Jing to draft a lightweight experiment checklist

---

## 9) Risks / dependencies
- Risk: adding stage gates could feel slow if we over-review.
  - Mitigation: review windows capped (24h SLA), async by default.

- Dependency: analytics dashboard ownership unclear for some features.
  - Mitigation: each Feature Page must name a dashboard owner.

- Risk: if teams keep writing PRDs in random docs, Feature Page won’t work.
  - Mitigation: PMO (Annie) will enforce template in sprint kickoff.

---

## 10) Action items (next 7 days)
1. **Annie** — Create and share the Notion Feature Page template + example (Due: Feb 17)
2. **Leo** — Define PRD DoD checklist (1 page max) (Due: Feb 17)
3. **Nina** — Provide QA lead-time + device matrix default for Growth squad (Due: Feb 18)
4. **Jing** — Draft tracking naming conventions + “instrumentation complete” definition (Due: Feb 18)
5. **Sam + Rohan** — Propose how to enforce the change rule in Jira workflow (Due: Feb 19)

---

## Next meeting
**Date/Time:** 2026-02-20 15:00

**Focus:** review the template + agree on pilot feature for first run

**Pre-reads:**
- Feature Page template (link TBD)
- PRD DoD checklist draft
