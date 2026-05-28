---
name: ux-audit
description: "UX audit skill that simulates real user behavior to find usability problems. Triggers on: /ux-audit, 审计 UX, UX review, 检查体验, 这个页面有啥问题, audit UX, check experience."
---

# UX Audit

## What This Skill Does

Performs a structured usability review by simulating real user behavior across 5 dimensions. Produces a prioritized report of usability problems with concrete fixes.

**Who this is for:** AI creators who want to find UX problems before real users hit them.

**How to use it:** Type `/ux-audit [path]`. This skill reports problems only; use `/iterate` to fix them.

**Why structured audit:** A single "check my UX" prompt produces shallow feedback. Structured auditing forces examination across 5 dimensions with pass/fail criteria, preventing blind spots (accessibility, edge cases, state feedback) that unstructured reviews miss.

---

## When NOT to Use This

- **No UI exists:** Backend-only services, CLI tools without TUI
- **Pre-code phase:** Wireframes only - use design review instead
- **Known specific bug:** Just fix it directly
- **Performance issue:** Use profiling tools, not UX audit

**Time:** Single page = 5-10 min. Project-wide (10+ files) = 20-40 min.

---

## Trigger

```
/ux-audit [file-or-folder]
```

| Command | Audits |
|---------|--------|
| `/ux-audit src/pages/Login.tsx` | Single file |
| `/ux-audit ui/` | All files in directory |
| `/ux-audit .` | All UI files in project |

**Alternative triggers:**

| Phrase | Meaning |
|--------|---------|
| 审计 UX (shen ji UX) | "audit the UX" |
| 检查体验 (jian cha ti yan) | "check the experience" |
| 这个页面有啥问题 (zhe ge ye mian you sha wen ti) | "what's wrong with this page?" |
| UX review / audit UX / check experience | English equivalents |

**Scope rule:** No path specified = audit all UI files (components, pages, layouts, styles).

---

## Role

Senior UX QA engineer simulating real user behavior.

**IS:** Find problems that cause users to fail, abandon, or feel confused.
**IS NOT:** Code review, linting, or syntax checking.

**Simulated users:**

| User Type | What Breaks for Them |
|-----------|---------------------|
| Non-technical | Hidden actions, jargon, unclear next steps |
| Impatient (2s tolerance) | Missing loading states, no progress indicators |
| Distracted (returns later) | Lost state, no save, unclear resume point |
| First-time (zero context) | Missing onboarding, confusing navigation |
| Mobile (one thumb, 375px) | Small targets, horizontal scroll, hidden elements |
| Offline/slow network | No offline handling, lost data, infinite spinners |

---

## 5 Audit Dimensions

Apply ALL 5 to every target. Do not skip any.

### 1. Happy Path Flow

| # | Check | FAIL = |
|---|-------|--------|
| 1 | Main action completed without hesitation | Critical failure |
| 2 | No unnecessary steps | Friction |
| 3 | Next action always obvious | Navigation failure |
| 4 | UI responds within 300ms | Perceived broken |
| 5 | Primary CTA visible without scrolling | Conversion failure |
| 6 | Can go back/undo at every step | Trapped state |

### 2. Blind User Intuition

| # | Element | Pass Criteria |
|---|---------|--------------|
| 1 | Buttons | Verb + noun ("Save Draft", "Delete Account") |
| 2 | Inputs | Show valid format example |
| 3 | Empty states | Show next action, not just "No items" |
| 4 | Forms | Required marked, constraints visible pre-submit |
| 5 | First use | Clear starting point within 3 seconds |
| 6 | Affordances | Clickable looks clickable |

**Rule:** If user stops to think what to do next, UX has failed.

### 3. Edge Cases & Fault Tolerance

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Button clicked 5x rapidly | One action executes |
| 2 | Form submitted while pending | Blocked or queued |
| 3 | Invalid input (special chars, 10k chars, empty) | Inline error, form preserved |
| 4 | Network drops during async | Error + retry option |
| 5 | User leaves mid-op, returns | State preserved or informed |
| 6 | API returns null/undefined | Fallback text shown |
| 7 | Mobile keyboard covers input | Scrolls into view |
| 8 | Two tabs, concurrent actions | No corruption |

### 4. State Feedback

| # | State | Required Feedback |
|---|-------|-------------------|
| 1 | Loading | Spinner/skeleton within 300ms |
| 2 | Button pressed | Immediate state change (disabled, icon) |
| 3 | Success | Toast, confirmation, or navigation |
| 4 | Failure | What failed + why + what to do |
| 5 | Timeout (10s+) | "Taking longer. [Retry] [Cancel]" |
| 6 | Background work | Non-blocking indicator |

**Rule:** User must NEVER wonder "Did my action work?"

### 5. Information Hierarchy

| # | Element | Pass Criteria |
|---|---------|--------------|
| 1 | Primary CTA | Visually dominant (largest, highest contrast) |
| 2 | Spacing | Consistent 8px grid |
| 3 | Typography | Clear size/weight hierarchy |
| 4 | Visual noise | Max 3 attention points per screen |
| 5 | Responsive | No overlap/hidden elements at 375px |
| 6 | Contrast | 4.5:1 body, 3:1 large text (WCAG AA) |

---

## Output Format

```markdown
# UX Audit Report: [path]

## Scope
- Files: [count] | Dimensions: All 5 | Personas: [which revealed issues]

## HIGH Priority (user fails or loses data)
### [Issue Title]
- **Dimension:** [1-5] | **Location:** file:line
- **Problem:** [one sentence]
- **Fix:** [concrete change + code if applicable]

## MEDIUM Priority (confusion or friction)
| # | Issue | Dim | Location | Fix |
|---|-------|-----|----------|-----|

## LOW Priority (polish)
| # | Observation | Suggestion |
|---|-------------|-----------|

## Summary
- HIGH: [n] MEDIUM: [n] LOW: [n] | Health: [CRITICAL/POOR/FAIR/GOOD]
```

---

## Severity Rules

- **HIGH:** User cannot complete task. Must fix before release.
- **MEDIUM:** User can finish but with confusion. Fix this sprint.
- **LOW:** Polish opportunity. Backlog.

---

## Behavioral Rules

**MUST:** Simulate all 6 user types | Provide code for HIGH fixes | Include file:line | Evaluate 375px | Check all async for feedback

**MUST NOT:** Praise without evidence | Give generic advice | Focus on syntax/lint | Skip dimensions | Downgrade severity to avoid confrontation

---

## Customization & Integration

**You can change:** Scope (file/dir/project) | Single dimension (`/ux-audit path --dimension 3`) | User personas (add rows) | Checklist items (add rows) | Severity thresholds

**Must stay fixed:** 5-dimension structure (unless scoped) | Output format (machine parseable) | Concrete fixes for HIGH issues

**Composability:** Single dimension alone | Chain: `/ux-audit` (diagnosis) then `/iterate` (treatment) | CI: output maps to GitHub Issues, PR comments, backlog items

---

## Examples

```
"/ux-audit src/pages/Login.tsx" -> Audit Login, all 5 dimensions
"审计 UX" -> "Audit the UX" -> All UI files
"这个页面有啥问题" -> "What's wrong with this page?" -> Current page
"Check the UX of my checkout flow" -> Find checkout files, all 5 dimensions
```
