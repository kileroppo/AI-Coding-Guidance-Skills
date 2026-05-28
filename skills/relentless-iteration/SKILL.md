---
name: relentless-iteration
description: "Multi-round critical iteration combining code hardening AND real-user UX stress-testing. Triggers on: /iterate, 迭代, 挑刺, 优化循环, iterate, polish, keep improving, harden this, stress test, find problems, iterate until done."
---

# Relentless Iteration

## What This Skill Does

Runs repeated rounds of critical analysis on your code and UI. Each round, the AI adopts a different user persona, walks your system, finds real problems, implements fixes, and verifies with tests. Repeats until the system is robust.

**Who this is for:** AI creators who want stress-testing from multiple real-world perspectives.

**How to use it:** Type `/iterate`. The AI begins multi-round improvement automatically.

**Why this approach:** Ad-hoc prompting ("review my code") produces shallow single-perspective feedback. Structured iteration catches 3-5x more issues through forced perspective rotation, minimum round enforcement, and mandatory verification. Without structure, teams find the same surface issues while deep problems ship to production.

---

## When NOT to Use This

- **No code yet:** Use brainstorming/design skills for greenfield ideation
- **Single known bug:** Just fix it directly
- **Documentation-only:** Use writing/editing skills
- **Performance profiling:** Use dedicated profiling tools
- **Backend with no UI:** Pass `backend` scope to skip UX checks

**Time:** 10 rounds = 15-40 findings, 20-45 min. 20 rounds = 30-70 findings, 40-90 min.

---

## Trigger

```
/iterate [rounds] [scope] [strictness]
```

| Command | Rounds | Scope | Strictness |
|---------|--------|-------|------------|
| `/iterate` | 10 | full-stack | maximum |
| `/iterate 20` | 20 | full-stack | maximum |
| `/iterate ui` | 10 | UI/UX only | maximum |
| `/iterate backend` | 10 | Backend only | maximum |
| `/iterate mild` | 10 | full-stack | reduced (critical only) |
| `/iterate 5 ui` | 5 | UI/UX only | maximum |

**Alternative triggers:**

| Phrase | Meaning |
|--------|---------|
| 迭代 (die dai) | "iterate" |
| 挑刺 (tiao ci) | "find faults/nitpick" - max strictness |
| 优化循环 (you hua xun huan) | "optimization loop" |
| polish / keep improving | refine quality |
| harden this | robustness focus (backend) |
| stress test / find problems | find breaking points |

**Parameters:**

| Parameter | Default | Values |
|-----------|---------|--------|
| Rounds | 10 | 1-100 |
| Scope | full-stack | `full-stack`, `ui`, `backend`, `frontend`, `infra` |
| Strictness | maximum | `maximum`, `mild` (critical/high only) |

---

## Process

### Step 1: Establish Baseline (once before Round 1)

1. Run full test suite. Record: total tests, passes, fails, coverage %.
2. Read entry points: config, app entry, routes, primary modules.
3. List claimed capabilities from README/docs.
4. Map user flows: every action from first visit to task completion.

If tests fail to run: fix as Round 0, then proceed.

### Step 2: Execute Rounds (repeat 1 through N)

#### 2a. Select Persona

Rotate sequentially. After 12, restart from 1.

| # | Persona | What they test |
|---|---------|---------------|
| 1 | First-time user | Zero-knowledge product use |
| 2 | Busy commuter (phone) | One thumb, 375px, under 5 taps |
| 3 | Heavy data user | Search, batch ops, 100+ items |
| 4 | Elder (65+) | Large fonts, high contrast, simple flows |
| 5 | Non-native speaker | Mixed-language input, clear terms |
| 6 | Screen reader user | Keyboard-only, ARIA, semantic HTML |
| 7 | Impatient (2s span) | Abandon without instant feedback |
| 8 | Perfectionist designer | Pixel alignment, 8px grid, consistency |
| 9 | Minimalist | Remove anything not breaking core function |
| 10 | Competitor's user | Feature parity, unique advantages |
| 11 | Malicious user | XSS, injection, oversized input, rapid-fire |
| 12 | DevOps (3 AM incident) | Kill services, corrupt data, partitions |

#### 2b. Walk the Full Flow

1. Open entry point. Attempt persona's primary task.
2. Record every confusion, error, delay, missing feedback, broken flow.
3. Note file:line for each issue.

Persona cannot complete task = automatic HIGH finding.

#### 2c. Criticize

Mark each PASS or FAIL:

**Engineering:**

| # | Question | If FAIL |
|---|----------|---------|
| 1 | Breaks under 100 concurrent users? | High |
| 2 | Dead code (defined, never called)? | Medium |
| 3 | Docs claim unimplemented feature? | High |
| 4 | Malformed input / timeout / null handling? | High |
| 5 | Hardcoded values / assumed environment? | Medium |

**UX (5 dimensions from /ux-audit):**

| # | Dimension | Pass Criteria |
|---|-----------|--------------|
| 1 | Happy Path | Primary task in under 3 clicks, no hesitation |
| 2 | Intuition | Every element understandable without docs |
| 3 | Fault Tolerance | Rapid clicks, race conditions, offline handled |
| 4 | State Feedback | Visible feedback within 300ms |
| 5 | Hierarchy | Most important element visually dominant |

**Measurable standards:**

| Check | Pass |
|-------|------|
| Content findable in under 3s | Yes/No |
| Core task done without instructions | Yes/No |
| Errors show what/why/next-step | Yes/No |
| Ops >300ms show progress | Yes/No |
| Empty states show guidance | Yes/No |
| Touch targets >= 44x44px | Yes/No |
| Contrast >= 4.5:1 body, 3:1 large | Yes/No |
| No overflow at 375px | Yes/No |
| Zero jargon, verb-first labels | Yes/No |
| Destructive actions need confirm+undo | Yes/No |

Output per problem: `[HIGH/MEDIUM/LOW]` + file:line + description + impact.

#### 2d. Propose Fixes

Per problem: what is wrong (1 sentence), why it matters (1 sentence), exact fix (implementable).

#### 2e. Implement & Verify

- Modify code, add/update tests, run full suite
- Zero regressions: test count >= baseline, no new failures
- Re-check fixes for introduced problems
- Commit: `fix(scope): description (Round N)`

Do NOT proceed if verification fails. Fix first.

### Step 3: Escalation

| Rounds | Focus |
|--------|-------|
| 1-2 | Surface: error handling, broken links, obvious gaps |
| 3-4 | Structural: architecture, dead code, missing tests |
| 5-6 | Usability: first-run, docs, accessibility |
| 7-8 | Operational: concurrency, performance, degradation |
| 9-10 | Edge cases: adversarial input, integration, polish |
| 11+ | Apply stopping criteria |

### Step 4: Stopping Criteria

Stop when ALL true simultaneously:
1. Minimum rounds completed
2. Coverage >= target (default 90%)
3. Latest round: zero HIGH/MEDIUM issues
4. New user completes primary task from docs alone
5. Every claimed feature implemented and tested
6. Two consecutive rounds: zero substantial findings

If ANY false: continue. If rounds > 2x requested: stop, report remaining as "deferred."

---

## Before/After Example

**Before (Round 3 input):**
```tsx
// LoginForm.tsx - no loading, no error handling
const handleSubmit = () => {
  fetch('/api/login', { method: 'POST', body: JSON.stringify(form) })
    .then(res => res.json())
    .then(data => setUser(data))
}
```

**Round 3 findings (Persona: Heavy data user):**
1. [HIGH] LoginForm.tsx:4 - No loading state. User clicks multiple times.
2. [HIGH] LoginForm.tsx:4 - No error handling. Network failure shows nothing.
3. [MEDIUM] LoginForm.tsx:4 - No validation before submit.

**After (Round 3 output):**
```tsx
const handleSubmit = async () => {
  if (!form.email || !form.password) return setError('Email and password required')
  setLoading(true); setError(null)
  try {
    const res = await fetch('/api/login', { method: 'POST', body: JSON.stringify(form) })
    if (!res.ok) throw new Error(`Login failed: ${res.statusText}`)
    setUser(await res.json())
  } catch (e) {
    setError(e.message + '. Check connection and retry.')
  } finally { setLoading(false) }
}
```

One round, one persona, 3 findings fixed. Multiply by 10 rounds across 12 personas.

---

## Output Format

### Per-Round

```markdown
## Round N: [Persona Name]

### Findings
1. [HIGH/MEDIUM/LOW] Problem (file:line)
   - Impact: what happens to users

### Fixes Applied
- file:line - what changed and why

### Verification
- Tests: X passed, Z added | Coverage: N% | Commit: `fix(scope): msg (Round N)`
```

### Final Summary

```markdown
## Iteration Complete
- Rounds: N | Found: X (H:a M:b L:c) | Fixed: Y | Tests added: Z
- Coverage: before% -> after%

| Metric | Before | After |
|--------|--------|-------|
| Tests | ... | +N |
| Coverage | ... | +N% |
| Known issues | ... | -N |

### Remaining: [severity] description - reason unfixed
### Next Steps: 1. ... 2. ...
```

---

## Philosophy

Each principle connects to a concrete rule:

| Principle | Chinese | Rule |
|-----------|---------|------|
| Simplicity is sophistication | 大道至简 (da dao zhi jian) | Every fix reduces code lines OR user steps |
| Serve without competing | 水利万物而不争 (shui li wan wu er bu zheng) | Remove UI that draws attention to tool over task |
| Less yields more | 少则得，多则惑 (shao ze de, duo ze huo) | If removing element doesn't break task, don't add it |
| Know yourself and enemy | 知己知彼 (zhi ji zhi bi) | Re-read code before each round, never assume |
| Speed is respect | 兵贵神速 (bing gui shen su) | Every operation: feedback within 300ms |
| Adapt to findings | 因敌变化而取胜 (yin di bian hua er qu sheng) | Shift focus based on what each round reveals |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Add code without finding a problem | Problem first, then fix |
| Fix cosmetic while structural remains | HIGH > MEDIUM > LOW |
| Test the framework, not the system | Test real user actions |
| Stop early ("looks fine") | Complete minimum rounds |
| Sugarcoat ("could be improved") | "Broken because X. Fix: Y." |
| Add features as fixes | Log features separately |
| Analyze without changing code | Every round commits changes |

---

## Customization

**You can change:**
- **Rounds:** `/iterate N` (1-100)
- **Scope:** `ui`, `backend`, `frontend`, `infra`
- **Strictness:** `mild` for critical-only
- **Personas:** Add to pool table: `| # | Name | What they test |`
- **Checklists:** Add rows to any table for domain concerns
- **Stopping criteria:** Add conditions to the list
- **Quality targets:** Adjust coverage/thresholds

**Must stay fixed:**
- Round structure: persona -> walk -> criticize -> propose -> implement -> verify
- Zero regressions rule
- Severity classification (HIGH/MEDIUM/LOW)
- Verification step every round

**Composability:**
- Single focus: `/iterate ui` with UX checklist only
- Skill chaining: any skill's issue list feeds Round 1 input
- Single persona: "use persona 11 for all rounds" = security focus
- Pipeline: `/ux-audit` (diagnosis) then `/iterate` (treatment)

---

## CI/Workflow Integration

Structured output enables:
- **GitHub Issues:** HIGH findings = issues with severity label
- **PR comments:** file:line enables inline review comments
- **Sprint planning:** MEDIUM = backlog items
- **CI gate:** `/iterate 3 mild` as pre-merge quality check

---

## Examples

```
User: "/iterate" -> 10 rounds, full-stack, max strictness
User: "/iterate 20 ui" -> 20 rounds, UI only
User: "迭代这个页面，挑刺" -> "Iterate this page, nitpick" -> max strictness
User: "Keep iterating until production quality" -> stop when criteria met
User: "用挑刺者角度分析修复，不断循环" -> "Nitpick, fix, loop" -> full iteration
```
