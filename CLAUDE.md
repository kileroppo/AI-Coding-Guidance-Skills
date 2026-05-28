# CLAUDE.md - System Rules for claude --print mode

You are operating inside a **self-evolving kernel**. Your output is parsed programmatically by `runner.py`. Do not treat this as a conversation. Treat it as a structured protocol.

## MANDATORY OUTPUT FORMAT

Every response MUST end with these two lines as plain text (NOT inside a code block):

STATUS: success
TRANSITION: <condition>

Or on failure:

STATUS: failure
TRANSITION: <condition>

If you omit these lines, runner.py will reject your output and retry. This wastes iteration budget. Do not forget them.

## Valid TRANSITION values by node

| Node    | Valid TRANSITION values                     |
|---------|---------------------------------------------|
| init    | goal_loaded                                 |
| plan    | plan_ready, plan_needs_revision             |
| code    | code_written, code_needs_retry              |
| test    | tests_pass, tests_fail                      |
| review  | review_pass, review_needs_changes           |
| reflect | evolution_proposed, no_evolution_needed      |
| evolve  | evolution_applied                           |

## Optional: FILES_WRITTEN

If you created or modified files, include:

FILES_WRITTEN: path/to/file1.py, path/to/file2.py

## Rules

1. STATUS must be exactly `success` or `failure`
2. TRANSITION must be a valid value for the current node
3. These lines must appear at the END of your response, as raw text
4. Do not wrap them in markdown code fences
5. Do not omit them under any circumstance
