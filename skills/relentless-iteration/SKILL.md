---
name: relentless-iteration
description: "Continuous fault-finding and fixing in cycles until a system is production-quality. Use when user wants to harden code, stress-test architecture, run multiple improvement passes, or iterate until a quality bar is met. Triggers on: keep iterating, keep improving, harden this, stress test, find problems, 挑刺, iterate until done."
---

# Relentless Iteration

Systematic multi-round critical analysis and repair. Each round: find real problems → propose fixes → implement → verify → repeat. Never stop until the system is genuinely robust.

## Philosophy

- 道德经「大道至简」: Each fix should simplify, not add complexity for its own sake.
- 孙子兵法「知彼知己」: Be brutally honest about what's broken. No sugarcoating.

## Process

### 1. Establish Baseline

Before the first round:
- Run the full test suite. Record: test count, coverage %, pass/fail.
- Read the core architecture files (entry points, main modules, config).
- Identify the system's claimed capabilities vs actual implementation.

### 2. Execute Rounds (minimum 5)

Each round follows this exact structure:

#### a) Criticize (挑刺)

Adopt the mindset of the harshest code reviewer you've ever met. Ask:

- What would break in production?
- What's implemented but never actually called?
- What's claimed in docs but missing in code?
- What happens under concurrent access / bad input / network failure?
- Where are the implicit assumptions that will bite later?
- What would a user's FIRST experience be? Would they succeed?

Output: A numbered list of problems, ranked by severity.

#### b) Propose

For each problem:
- One sentence: what's wrong
- One sentence: why it matters
- The fix (concrete, implementable, not vague)

#### c) Implement

- Fix ALL problems identified in this round
- Write tests for every fix
- Run full test suite after each round — zero regressions allowed

#### d) Verify

After implementing:
- Tests pass? Coverage still above threshold?
- Did the fix introduce new problems? (recursive self-check)
- Commit with clear message: `fix(scope): description of what was fixed (Round N)`

### 3. Escalation Between Rounds

Each subsequent round should go DEEPER:

| Round | Focus |
|-------|-------|
| 1 | Surface bugs, missing error handling, obvious gaps |
| 2 | Architecture problems, disconnected systems, dead code |
| 3 | Usability: first-run experience, documentation, error messages |
| 4 | Operational: concurrency, performance, observability, graceful degradation |
| 5+ | Edge cases, adversarial inputs, real-world integration scenarios |

### 4. Stopping Criteria

Stop when ALL of these are true:
- [ ] 5+ rounds completed
- [ ] Test coverage above target (default 90%)
- [ ] No critical or high-severity issues found in latest round
- [ ] System can be used end-to-end by a new user following only the docs
- [ ] All "claimed features" are actually implemented and tested

If any criterion fails, do another round.

## Quality Targets

| Metric | Minimum | Ideal |
|--------|---------|-------|
| Test coverage | 90% | 98%+ |
| Rounds | 5 | Until clean |
| Tests per round | 10+ new | 50+ new |
| Regressions | 0 | 0 |

## Anti-Patterns (Avoid These)

- ❌ "Adding more code" without finding real problems first
- ❌ Fixing cosmetic issues while structural problems remain
- ❌ Writing tests that test the test framework, not the system
- ❌ Stopping after 1-2 rounds because "it looks fine"
- ❌ Sugarcoating: "this could potentially be improved" → say "this is broken because X"
- ❌ Adding features disguised as fixes (scope creep)

## Invocation Examples

```
User: "这个系统挑刺一下，至少迭代5轮"
User: "Keep iterating on this until it's production quality"
User: "Stress test this codebase, find every problem"
User: "用挑刺者角度分析问题然后修复，不断循环"
User: "Harden this system, I want 90%+ coverage and zero known bugs"
```

## Output Per Round

Each round should output:

1. **Problem List** (numbered, severity-tagged)
2. **Fix Summary** (what was done for each)
3. **Verification** (test count, coverage, pass/fail)
4. **Commit** (one per round with clear message)

At the end of all rounds:

- Total problems found and fixed
- Before/after comparison (tests, coverage, code lines)
- Remaining known limitations (if any)
- What the next person should look at
