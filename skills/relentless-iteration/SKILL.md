---
name: relentless-iteration
description: "Multi-round critical iteration combining code hardening AND real-user UX stress-testing. Triggers on: /iterate, 迭代, 挑刺, 优化循环, iterate, polish, keep improving, harden this, stress test, find problems, iterate until done."
---

# Relentless Iteration

Systematic multi-round critical analysis from **both engineering AND real-user perspectives**. Each round: adopt a persona → walk the full flow → find real problems → implement fixes → verify → repeat. Never stop until the system is genuinely robust AND delightful.

## Philosophy

### 道（The Way）
- **大道至简** — Each fix should simplify, not add complexity. Remove everything the user doesn't need.
- **水利万物而不争** — UI and features serve the user without showing off.
- **少则得，多则惑** — Less is more. Every element must earn its place.

### 术（Strategy）
- **知己知彼** — Deep understanding of user context. Be brutally honest about what's broken.
- **先胜后战** — Design before code. Think before act.
- **兵贵神速** — Minimize interaction cost. Speed is respect for the user's time.
- **因敌变化而取胜** — Adapt quickly based on feedback.

### The Jobs Standard
- Could your grandmother use this?
- Does it feel "insanely great"?
- Does every pixel, every interaction have a reason to exist?

## Trigger

```
/iterate [rounds] [scope] [strictness]
/iterate                    → 10 rounds, full-stack, maximum strictness
/iterate 20                 → 20 rounds
/iterate ui                 → UI/UX only
/iterate backend            → Backend only
/iterate mild               → Reduced strictness
/iterate 5 ui               → 5 rounds, UI only
```

Also triggers on: "迭代", "挑刺", "优化循环", "polish", "keep iterating", "keep improving", "harden this", "stress test", "find problems"

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Rounds | 10 | `/iterate 20` runs 20 rounds |
| Scope | full-stack | `/iterate ui` = UI only, `/iterate backend` = backend only |
| Strictness | maximum | `/iterate mild` reduces intensity |

## Process

### 1. Establish Baseline

Before the first round:
- Run the full test suite. Record: test count, coverage %, pass/fail.
- Read the core architecture files (entry points, main modules, config).
- Identify the system's claimed capabilities vs actual implementation.
- Map user-facing flows and entry points.

### 2. Execute Rounds

Each round follows this exact structure:

#### a) Select Persona

Choose from the persona pool (rotate each round):

| # | Persona | Core Need |
|---|---------|-----------|
| 1 | First-time user (never seen this product) | Understand value in 10s, zero learning cost |
| 2 | Busy professional (commuting, on phone) | One-hand operation, quick results |
| 3 | Deep researcher (heavy notes user) | Efficient navigation, precise search, batch ops |
| 4 | Retired elder (declining vision) | Large fonts, high contrast, simple flows |
| 5 | Non-native speaker (mixed languages) | Understandable terms, contextual hints |
| 6 | Accessibility user (screen reader) | Complete ARIA, keyboard reachable, semantic HTML |
| 7 | Extremely impatient person (2s attention) | Instant feedback, zero wait feel, visible progress |
| 8 | Perfectionist designer | Pixel alignment, consistent spacing, restrained animation |
| 9 | Steve Jobs himself | Remove everything unnecessary. Then remove one more layer. |
| 10 | Competitor's user (just left Notion/Readwise) | Not worse than alternatives, has unique highlights |
| 11 | Malicious user (adversarial input) | Security, injection, abuse scenarios |
| 12 | DevOps engineer (production incident) | Observability, graceful degradation, recovery |

#### b) Walk the Full Flow

As the selected persona, walk through the complete user journey and codebase.

#### c) Criticize (挑刺)

Adopt the mindset of the harshest reviewer. Check ALL applicable dimensions:

**Engineering Dimensions:**
- What would break in production?
- What's implemented but never actually called?
- What's claimed in docs but missing in code?
- What happens under concurrent access / bad input / network failure?
- Where are the implicit assumptions that will bite later?

**UX Dimensions (invoke /ux-audit's 5 pillars):**
- **Happy Path Flow** — Can the user complete tasks without hesitation?
- **Blind User Intuition** — Is the UI self-explanatory without docs?
- **Edge Cases & Fault Tolerance** — Rapid clicks, race conditions, offline?
- **State Feedback** — Every action has visible feedback?
- **Information Hierarchy** — Visual structure guides the eye correctly?

**Checklist (must verify each round):**

| Dimension | Question |
|-----------|----------|
| Information architecture | Can user find what they want in 3 seconds? |
| First-time experience | Can they complete core task without instructions? |
| Error handling | Every failure point has a friendly message? |
| Loading states | Operations > 300ms have skeleton/progress? |
| Empty states | No-data screens show guidance? |
| Touch targets | All clickable elements >= 44px? |
| Contrast | Text >= 4.5:1, large text >= 3:1? |
| Responsive | 375px / 768px / 1440px all work? |
| Animation | Meaningful? Respects prefers-reduced-motion? |
| Copy | No jargon, no ambiguity, verb-first? |
| Consistency | Same action behaves same everywhere? |
| Reversibility | Dangerous actions have confirmation? Undo? |
| Performance | First paint < 1s? Interaction response < 100ms? |

Output: A numbered list of problems, ranked by severity.

#### d) Propose

For each problem:
- One sentence: what's wrong
- One sentence: why it matters
- The fix (concrete, implementable, not vague)

#### e) Implement

- Fix ALL problems identified in this round
- Write tests for every fix
- Run full test suite — zero regressions allowed

#### f) Verify

- Tests pass? Coverage still above threshold?
- Did the fix introduce new problems? (recursive self-check)
- Commit with clear message: `fix(scope): description (Round N)`

### 3. Escalation Between Rounds

Each subsequent round goes DEEPER:

| Round | Focus |
|-------|-------|
| 1–2 | Surface bugs, missing error handling, obvious UX gaps |
| 3–4 | Architecture problems, disconnected systems, dead code, interaction flows |
| 5–6 | Usability: first-run experience, documentation, error messages, accessibility |
| 7–8 | Operational: concurrency, performance, observability, graceful degradation |
| 9–10 | Edge cases, adversarial inputs, real-world integration, polish |
| 11+ | Diminishing returns — stop if 2 consecutive rounds find nothing substantial |

### 4. Stopping Criteria

Stop when ALL of these are true:
- [ ] Minimum rounds completed (default 10, or user-specified)
- [ ] Test coverage above target (default 90%)
- [ ] No critical or high-severity issues found in latest round
- [ ] System can be used end-to-end by a new user following only the docs
- [ ] All "claimed features" are actually implemented and tested
- [ ] 2 consecutive rounds with no substantial findings

If any criterion fails, do another round.

## Output Per Round

```markdown
## Round N: [Persona Name]

### 道（Philosophy Layer）
> Dao De Jing quote + this round's simplification direction

### 术（Tactics Layer）
> Art of War quote + specific attack points

### Findings
1. [🛑/⚠️/🎨 Severity] Specific problem (file:line or component name)
2. ...

### Fixes
- What was changed and why

### Verification
- Tests: X passed, Y added, coverage: Z%
- Commit: `fix(scope): message (Round N)`

### The Jobs Verdict
> One sentence: Does this change bring the product closer to "insanely great"?
```

## Final Summary (after all rounds)

```markdown
## Iteration Complete

### Statistics
- Rounds executed: N
- Problems found: X (🛑 a / ⚠️ b / 🎨 c)
- Problems fixed: Y
- Tests added: Z
- Coverage: before% → after%

### Before/After
| Metric | Before | After |
|--------|--------|-------|
| Test count | ... | ... |
| Coverage | ... | ... |
| Known issues | ... | ... |

### Remaining Limitations
- ...

### What the Next Person Should Look At
- ...
```

## Quality Targets

| Metric | Minimum | Ideal |
|--------|---------|-------|
| Test coverage | 90% | 98%+ |
| Rounds | 10 | Until clean |
| Regressions | 0 | 0 |
| UX issues found per round | 1+ | Until none remain |

## Anti-Patterns (Avoid These)

- ❌ "Adding more code" without finding real problems first
- ❌ Fixing cosmetic issues while structural problems remain
- ❌ Writing tests that test the test framework, not the system
- ❌ Stopping after 1–2 rounds because "it looks fine"
- ❌ Sugarcoating: "this could potentially be improved" → say "this is broken because X"
- ❌ Adding features disguised as fixes (scope creep)
- ❌ Praising code quality without reason
- ❌ Giving generic advice instead of specific, actionable fixes
- ❌ Paper-only analysis without real code changes

## Relationship with /ux-audit

`/ux-audit` is a **diagnostic tool** — it reports UX problems in a structured audit.
`/iterate` is a **treatment workflow** — it finds, fixes, and verifies in a loop.

Each `/iterate` round internally uses `/ux-audit`'s 5 dimensions as its UX checklist. Users can run `/ux-audit` first to see the report, then `/iterate` to fix.

## Invocation Examples

```
User: "/iterate"
User: "/iterate 20 ui"
User: "迭代这个页面，挑刺，至少10轮"
User: "Keep iterating on this until it's production quality"
User: "Stress test this codebase, find every problem"
User: "用挑刺者角度分析问题然后修复，不断循环"
User: "Harden this system, I want 90%+ coverage and zero known bugs"
User: "Polish this UI, simulate real users"
User: "这个页面体验不好，帮我迭代优化"
```
