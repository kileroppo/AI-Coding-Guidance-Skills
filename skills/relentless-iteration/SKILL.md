---
name: relentless-iteration
description: "Multi-round critical iteration combining code hardening AND real-user UX stress-testing. Triggers on: /iterate, 迭代, 挑刺, 优化循环, iterate, polish, keep improving, harden this, stress test, find problems, iterate until done."
---

# Relentless Iteration

## What This Skill Does

This skill runs repeated rounds of critical analysis on your code and UI. Each round, the AI adopts a different user persona (e.g., first-time user, impatient commuter, accessibility user), walks through your system, identifies real problems, implements fixes, and verifies them with tests. The cycle repeats until the system is robust and delightful.

**Who this is for:** AI creators and developers who want their product stress-tested from multiple real-world perspectives, not just linted or code-reviewed.

**How to use it:** Type `/iterate` in your AI assistant chat. The AI will begin multi-round improvement automatically. See the Trigger section below for options.

---

## Trigger

**Primary command:**

```
/iterate [rounds] [scope] [strictness]
```

**Examples with exact behavior:**

| Command | Rounds | Scope | Strictness |
|---------|--------|-------|------------|
| `/iterate` | 10 | full-stack (frontend + backend + infra) | maximum |
| `/iterate 20` | 20 | full-stack | maximum |
| `/iterate ui` | 10 | UI/UX files only (components, pages, styles) | maximum |
| `/iterate backend` | 10 | Backend only (API, database, services) | maximum |
| `/iterate mild` | 10 | full-stack | reduced (skip cosmetic issues, focus on critical bugs only) |
| `/iterate 5 ui` | 5 | UI/UX only | maximum |

**Alternative trigger phrases (Chinese + English):**

| Phrase | Language | Meaning | Equivalent Command |
|--------|----------|---------|-------------------|
| 迭代 (die dai) | Chinese | "iterate" | `/iterate` |
| 挑刺 (tiao ci) | Chinese | "find faults/nitpick" | `/iterate` with maximum strictness |
| 优化循环 (you hua xun huan) | Chinese | "optimization loop" | `/iterate` |
| polish | English | refine quality | `/iterate` |
| keep iterating | English | continue rounds | `/iterate` |
| keep improving | English | continue rounds | `/iterate` |
| harden this | English | focus on robustness | `/iterate backend` |
| stress test | English | find breaking points | `/iterate` with maximum strictness |
| find problems | English | diagnostic focus | `/iterate` |

**Activation rule:** This skill activates when the user message contains ANY of the above phrases, OR when the user explicitly requests repeated rounds of improvement on existing code.

---

## Parameters

| Parameter | Default | Allowed Values | Description |
|-----------|---------|----------------|-------------|
| Rounds | 10 | 1-100 (integer) | Number of improvement cycles to execute |
| Scope | full-stack | `full-stack`, `ui`, `backend`, `frontend`, `infra` | Which parts of the codebase to examine |
| Strictness | maximum | `maximum`, `mild` | `maximum` = report all issues. `mild` = skip cosmetic, focus on critical/high only |

---

## Process

Execute the following steps in exact order. Do not skip steps. Do not reorder.

### Step 1: Establish Baseline (run once before Round 1)

Complete ALL of the following before starting any round:

1. **Run the full test suite.** Record these exact values: total test count, pass count, fail count, coverage percentage.
2. **Read entry point files.** Identify: main config files, app entry points, route definitions, and primary modules.
3. **List claimed capabilities.** Read the README or docs. Write down every feature the project claims to have.
4. **Map user-facing flows.** List every action a user can take, from first visit to task completion.

If the test suite fails to run (missing dependencies, broken config): document the failure, fix it as Round 0, then proceed.

### Step 2: Execute Rounds

Repeat the following structure for each round (Round 1 through Round N):

#### 2a. Select Persona

Pick the next persona from this pool. Rotate sequentially (Round 1 = Persona 1, Round 2 = Persona 2, etc.). After Persona 12, restart from Persona 1.

**Persona pool** (a fixed list of simulated user types, one per round):

| # | Persona | What they need most | How they test the system |
|---|---------|--------------------|-----------------------|
| 1 | First-time user (never seen this product) | Understand value in 10 seconds, zero learning curve | Try to use the product with no prior knowledge |
| 2 | Busy professional (commuting, using phone) | One-hand operation, results in under 5 taps | Attempt all tasks with one thumb on a 375px screen |
| 3 | Deep researcher (heavy notes/data user) | Fast navigation, precise search, batch operations | Search for specific items, try to process 100+ items |
| 4 | Retired elder (declining vision, 65+ years old) | Large fonts (16px+), high contrast, simple linear flows | Read all text at arm's length, avoid multi-step processes |
| 5 | Non-native English speaker (mixed language input) | Clear terminology, contextual hints, no idioms | Enter mixed-language input, read all UI copy for clarity |
| 6 | Screen reader user (keyboard-only navigation) | Complete ARIA labels, keyboard reachable elements, semantic HTML | Tab through every element, verify announcements |
| 7 | Extremely impatient person (2-second attention span) | Instant feedback, zero perceived wait, visible progress | Abandon any flow that takes more than 2 seconds without feedback |
| 8 | Perfectionist designer (pixel-level precision) | Consistent spacing, aligned elements, restrained animation | Inspect every pixel, check 8px grid alignment, verify consistency |
| 9 | Steve Jobs (remove everything unnecessary) | Radical simplicity, only essential elements remain | For every element ask: "Does removing this break core function?" If no, remove it |
| 10 | Competitor's user (just switched from Notion/Readwise) | Feature parity with alternatives, unique advantages visible | Compare each feature against the equivalent in competing products |
| 11 | Malicious user (adversarial input) | Exploit security gaps, inject scripts, abuse rate limits | Submit XSS payloads, SQL injection, oversized inputs, rapid-fire requests |
| 12 | DevOps engineer (3 AM production incident) | Observability, graceful degradation, fast recovery | Kill services, corrupt data, simulate network partition |

#### 2b. Walk the Full Flow

Execute these actions as the selected persona:

1. Open the application entry point (or primary file if CLI/library).
2. Attempt to complete the persona's primary task (defined in "What they need most" column).
3. Record every point where you encounter: confusion, errors, delays, missing feedback, broken flows.
4. Note the file path and line number for each issue found.

If the persona cannot complete their primary task: that is automatically a critical (high-severity) finding.

#### 2c. Criticize

Apply ALL of the following checklists. Mark each item as PASS or FAIL:

**Engineering checklist:**

| # | Question | If FAIL, severity |
|---|----------|------------------|
| 1 | Would this break in production under 100 concurrent users? | High |
| 2 | Is there code that is defined but never called? | Medium |
| 3 | Do the docs claim a feature that the code does not implement? | High |
| 4 | What happens with malformed input / network timeout / null values? | High |
| 5 | Are there implicit assumptions (hardcoded values, assumed environment)? | Medium |

**UX checklist (the 5 dimensions from /ux-audit):**

| # | Dimension | Pass Criteria |
|---|-----------|--------------|
| 1 | Happy Path Flow | User completes primary task in under 3 clicks/commands without hesitation |
| 2 | Blind User Intuition | Every UI element is understandable without reading documentation |
| 3 | Edge Cases & Fault Tolerance | Rapid clicks, race conditions, offline mode all handled gracefully |
| 4 | State Feedback | Every action produces visible feedback within 300ms |
| 5 | Information Hierarchy | The most important element on each screen is visually dominant |

**Measurable standards checklist (verify every round):**

| Dimension | Pass Criteria | Measurement Method |
|-----------|---------------|--------------------|
| Information findability | User finds target content in under 3 seconds | Count seconds from page load to target |
| First-time completion | User completes core task without instructions | Attempt task with zero prior context |
| Error messages | Every error shows: what failed, why, and what to do next | Review all catch/error blocks |
| Loading states | Operations over 300ms display skeleton or progress indicator | Check all async operations |
| Empty states | Screens with no data show guidance on how to add data | Navigate to each empty state |
| Touch targets | All clickable elements are at least 44x44 pixels | Measure element dimensions |
| Color contrast | Body text ratio >= 4.5:1, large text >= 3:1 | Use contrast checker tool |
| Responsive layout | No horizontal scroll or overlap at 375px, 768px, 1440px widths | Resize viewport and verify |
| Animation purpose | Every animation communicates state change (not decoration) | Disable animations, check if meaning is lost |
| Copy clarity | Zero jargon in user-facing text, all labels start with a verb | Read every visible string |
| Behavior consistency | Same action produces same result everywhere in the app | Test same interaction in different locations |
| Dangerous action safety | Delete/destructive actions require confirmation and offer undo | Trigger every destructive action |
| Performance | First contentful paint under 1 second, interaction response under 100ms | Measure with performance tools |

Output: A numbered list of problems. Each problem must include:
- Severity: `[HIGH]`, `[MEDIUM]`, or `[LOW]`
- Location: file path and line number (or component name if no line number)
- Description: one sentence stating what is wrong
- Impact: one sentence stating what happens to users because of this

#### 2d. Propose Fixes

For each problem found in Step 2c, write:
1. **What is wrong** (one sentence)
2. **Why it matters** (one sentence connecting to user impact)
3. **Exact fix** (code change, config change, or file addition - must be implementable, not advisory)

If a problem has multiple possible fixes: choose the simplest one that fully resolves the issue.

#### 2e. Implement Fixes

Execute ALL proposed fixes from Step 2d:
- Modify the code directly
- Add or update tests for each fix
- Run the full test suite after all fixes are applied
- If any test fails: fix the regression before proceeding

**Zero regressions rule:** The test count must be >= the baseline from Step 1. No previously passing test may now fail.

#### 2f. Verify

After implementing fixes:
1. Run the full test suite. Confirm: all tests pass, coverage >= baseline.
2. Re-check each fix: does the fix introduce any new problem? If yes, fix it now (do not defer to next round).
3. Commit with message format: `fix(scope): description (Round N)`

If verification fails: do NOT proceed to the next round. Fix the issue first.

### Step 3: Escalation Between Rounds

Each round group focuses on progressively deeper issues:

| Rounds | Focus Area | What to Look For |
|--------|-----------|-----------------|
| 1-2 | Surface layer | Missing error handling, obvious UX gaps, broken links, typos |
| 3-4 | Structural layer | Architecture disconnects, dead code, broken interaction flows, missing tests |
| 5-6 | Usability layer | First-run experience, documentation gaps, error message quality, accessibility |
| 7-8 | Operational layer | Concurrency bugs, performance bottlenecks, observability gaps, graceful degradation |
| 9-10 | Edge case layer | Adversarial inputs, real-world integration issues, visual polish |
| 11+ | Diminishing returns | Apply stopping criteria (see Step 4) |

### Step 4: Stopping Criteria

**Stop iterating when ALL of these conditions are true simultaneously:**

1. Minimum rounds completed (default 10, or the number specified by user)
2. Test coverage is at or above target (default 90%)
3. The latest round found zero critical or high-severity issues
4. A new user can complete the primary task end-to-end following only the docs
5. Every feature claimed in docs is implemented and has at least one test
6. Two consecutive rounds produced zero substantial findings (only cosmetic or no findings)

**If ANY condition is false:** execute another round.

**If rounds exceed 2x the requested amount** (e.g., 20 rounds when 10 were requested): stop and report remaining issues as "deferred" with severity and recommended priority.

---

## Output Format

### Per-Round Output

```markdown
## Round N: [Persona Name]

### Philosophy Layer
> Eastern philosophy principle guiding this round's approach
> Connection to concrete action: [one sentence linking principle to what we will do]

### Findings
1. [HIGH/MEDIUM/LOW] Specific problem (file:line or component name)
   - Impact: what happens to users
2. ...

### Fixes Applied
- file:line - what was changed and why (one sentence each)

### Verification
- Tests: X total, Y passed, Z added this round
- Coverage: N%
- Commit: `fix(scope): message (Round N)`

### Simplicity Check
> One sentence: Did this round make the product simpler or more complex? If more complex, justify why.
```

### Final Summary (after all rounds complete)

```markdown
## Iteration Complete

### Statistics
- Rounds executed: N
- Total problems found: X (HIGH: a, MEDIUM: b, LOW: c)
- Problems fixed: Y
- Tests added: Z
- Coverage: before% -> after%

### Before/After Comparison
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Test count | ... | ... | +N |
| Coverage % | ... | ... | +N% |
| Known issues | ... | ... | -N |
| Critical bugs | ... | ... | -N |

### Remaining Limitations (unfixed)
- [severity] description - reason not fixed (e.g., requires external dependency, out of scope)

### Recommended Next Steps
1. Highest priority remaining issue and suggested approach
2. ...
```

---

## Philosophy

These Eastern philosophy principles guide the iteration approach. Each principle connects to a concrete behavior:

### Dao (The Way) - Simplification Principles

| Principle | Chinese | Meaning | Concrete Rule |
|-----------|---------|---------|---------------|
| Simplicity is the ultimate sophistication | 大道至简 (da dao zhi jian) | The best solution is the simplest one | Every fix must reduce total code lines OR reduce user steps. If a fix adds complexity, find a simpler alternative. |
| Serve without competing | 水利万物而不争 (shui li wan wu er bu zheng) | Good UX is invisible - users achieve goals without noticing the tool | Remove all UI elements that draw attention to the tool rather than the user's task. |
| Less yields more | 少则得，多则惑 (shao ze de, duo ze huo) | Every element must justify its existence | Before adding any element, verify: removing it would break a user's ability to complete their task. If not, do not add it. |

### Strategy (The Art of War) - Tactical Principles

| Principle | Chinese | Meaning | Concrete Rule |
|-----------|---------|---------|---------------|
| Know yourself and your enemy | 知己知彼 (zhi ji zhi bi) | Understand both the system's state and the user's context | Before each round, re-read the current state of the code. Do not assume it matches your memory. |
| Win before fighting | 先胜后战 (xian sheng hou zhan) | Plan the fix before writing code | Write the fix description in Step 2d before touching any code in Step 2e. |
| Speed is respect | 兵贵神速 (bing gui shen su) | Minimize the user's time cost at every interaction | Every user-facing operation must complete or show feedback within 300ms. |
| Adapt to what you find | 因敌变化而取胜 (yin di bian hua er qu sheng) | Change strategy based on what each round reveals | If Round N finds mostly UX issues, shift Round N+1 to deeper UX investigation rather than following the default escalation. |

### The Simplicity Standard

Apply these three questions to every change:

1. **Could a non-technical person use this feature without help?** If no, simplify until they can.
2. **Does every visible element serve the user's immediate goal?** If no, remove it.
3. **Does every interaction feel instant and predictable?** If no, add feedback or reduce latency.

---

## Quality Targets

| Metric | Minimum Acceptable | Ideal Target |
|--------|-------------------|--------------|
| Test coverage | 90% | 98%+ |
| Rounds executed | User-specified (default 10) | Until all stopping criteria met |
| Regressions introduced | 0 | 0 |
| HIGH issues remaining at end | 0 | 0 |
| MEDIUM issues remaining at end | 3 or fewer | 0 |

---

## Anti-Patterns (Never Do These)

| Anti-Pattern | Why It Fails | Do This Instead |
|--------------|-------------|-----------------|
| Adding code without finding a real problem first | Creates bloat with no user benefit | Always identify the problem before writing any fix |
| Fixing cosmetic issues while structural problems remain | Ignores root causes | Fix HIGH severity before MEDIUM, MEDIUM before LOW |
| Writing tests that test the framework, not the system | Inflates coverage without catching real bugs | Every test must simulate a real user action or real input |
| Stopping after 1-2 rounds because "it looks fine" | Surface review misses deep issues | Complete minimum rounds regardless of initial impressions |
| Sugarcoating: "this could potentially be improved" | Avoids accountability | State directly: "This is broken because X. Fix: Y." |
| Adding features disguised as fixes (scope creep) | Changes requirements mid-iteration | If a new feature is needed, log it as a separate task, do not implement it in this iteration |
| Praising code quality without evidence | Wastes output space | Only state quality claims with specific evidence (test results, metrics) |
| Paper-only analysis without code changes | Produces reports but no improvement | Every round must commit at least one code change (or explicitly state "zero issues found") |

---

## Integration with Other Skills

| Skill | Relationship | How They Work Together |
|-------|-------------|----------------------|
| `/ux-audit` | Diagnostic input | `/ux-audit` produces a problem report. `/iterate` takes that report and fixes every issue in a loop. Run `/ux-audit` first for diagnosis, then `/iterate` for treatment. |
| Other analysis skills | Can feed findings | Any skill that produces a list of issues can feed into `/iterate` as the initial problem list for Round 1. |

---

## Invocation Examples

```
User: "/iterate"
→ 10 rounds, full-stack scope, maximum strictness

User: "/iterate 20 ui"
→ 20 rounds, UI/UX files only, maximum strictness

User: "迭代这个页面，挑刺，至少10轮"
→ Translation: "Iterate this page, find faults, at least 10 rounds"
→ 10 rounds, scope = current page files, maximum strictness

User: "Keep iterating on this until it's production quality"
→ 10 rounds minimum, full-stack, stop only when all stopping criteria met

User: "Stress test this codebase, find every problem"
→ 10 rounds, full-stack, maximum strictness, focus on edge cases

User: "用挑刺者角度分析问题然后修复，不断循环"
→ Translation: "Analyze problems from a fault-finder's perspective, then fix, continuous loop"
→ 10 rounds, full-stack, maximum strictness

User: "Harden this system, I want 90%+ coverage and zero known bugs"
→ 10 rounds, full-stack, maximum strictness, coverage target = 90%

User: "Polish this UI, simulate real users"
→ 10 rounds, UI scope, rotate through user personas

User: "这个页面体验不好，帮我迭代优化"
→ Translation: "This page has bad UX, help me iterate and optimize"
→ 10 rounds, scope = current page, maximum strictness, UX focus
```
