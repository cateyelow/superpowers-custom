# Implementer Subagent Prompt Template — via codex-worker (OpenAI GPT)

Use this template when dispatching an implementer. The implementer is **Codex/GPT**, dispatched through the `codex-worker` agent (`~/.claude/agents/codex-worker.md`), which relays this prompt VERBATIM to `codex exec` (gpt-5.6-sol, reasoning max, host-safe flags) and relays the result back. That means:

- **The prompt below is the ENTIRE world the implementer sees.** Nothing you don't paste in reaches it — full task text, acceptance criteria, and every file/context reference must be included.
- **One-shot semantics.** Codex cannot pause mid-run to ask you questions. Questions come back as a `NEEDS_CONTEXT` final report instead — answer them and re-dispatch.
- **Credit exhaustion = HARD STOP.** If codex-worker reports an OpenAI credit/quota/rate-limit error (`insufficient_quota` / `429`), implementation CANNOT proceed. Do not fall back to a Claude implementer. Stop and tell the user to recharge (see SKILL.md).

```
Agent tool (codex-worker):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description

    [FULL TEXT of task from plan - paste it here, don't make subagent read file]

    ## Context

    [Scene-setting: where this fits, dependencies, architectural context]

    ## Acceptance Criteria (Definition of Done)

    [Concrete, checkable criteria copied/derived from the plan — the subagent must be able
    to verify each one itself. Always include: type-check passes, lint clean, relevant
    tests pass. For UI tasks: the exact user-visible behavior that must work in a browser.
    Measured on this host: incomplete subagent output traces to incomplete specs, not
    model capability — this section is the completeness lever.]

    ## Before You Begin

    You run one-shot: you cannot pause to ask questions mid-run. So decide NOW, before
    writing any code: if the requirements, acceptance criteria, approach, dependencies,
    or anything in the task description is unclear or contradictory, do NOT implement.
    Instead return status NEEDS_CONTEXT with your specific questions as your final
    report. A round-trip for answers is cheap; guessed-wrong work is not.

    ## Your Job

    Once you're clear on requirements:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. Commit your work
    5. Self-review (see below)
    6. Report back

    Work from: [directory]
    Apply the changes directly to the files.

    **While you work:** If you hit something unexpected that changes the shape of the
    task — a missing dependency, code that contradicts the plan, an assumption that
    turns out false — do not guess through it. Stop and return BLOCKED or NEEDS_CONTEXT
    describing exactly what you found.

    ## Code Organization

    You reason best about code you can hold in context at once, and your edits are more
    reliable when files are focused. Keep this in mind:
    - Follow the file structure defined in the plan
    - Each file should have one clear responsibility with a well-defined interface
    - If a file you're creating is growing beyond the plan's intent, stop and report
      it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
    - If an existing file you're modifying is already large or tangled, work carefully
      and note it as a concern in your report
    - In existing codebases, follow established patterns. Improve code you're touching
      the way a good developer would, but don't restructure things outside your task.

    ## When You're in Over Your Head

    It is always OK to stop and say "this is too hard for me." Bad work is worse than
    no work. You will not be penalized for escalating.

    **STOP and escalate when:**
    - The task requires architectural decisions with multiple valid approaches
    - You need to understand code beyond what was provided and can't find clarity
    - You feel uncertain about whether your approach is correct
    - The task involves restructuring existing code in ways the plan didn't anticipate
    - You've been reading file after file trying to understand the system without progress

    **How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe
    specifically what you're stuck on, what you've tried, and what kind of help you need.
    The controller can provide more context or a fuller spec, or break the task into
    smaller pieces.

    ## Before Reporting Back: Self-Review

    Review your work with fresh eyes. Ask yourself:

    **Completeness:**
    - Did I fully implement everything in the spec?
    - Did I miss any requirements?
    - Are there edge cases I didn't handle?

    **Quality:**
    - Is this my best work?
    - Are names clear and accurate (match what things do, not how they work)?
    - Is the code clean and maintainable?

    **Discipline:**
    - Did I avoid overbuilding (YAGNI)?
    - Did I only build what was requested?
    - Did I follow existing patterns in the codebase?

    **Testing:**
    - Do tests actually verify behavior (not just mock behavior)?
    - Did I follow TDD if required?
    - Are tests comprehensive?

    If you find issues during self-review, fix them now before reporting.

    ## After Review Findings

    If the task review finds issues, you will be resumed with the findings.
    Fix them, re-run the tests that cover the amended code, and append a fix
    report to your report file: what you changed, the covering tests you
    ran, the command, and the output. Reviewers will not re-run tests for
    you — your report is the test evidence. Then reply with the same short
    status contract as your first report.

    ## Report Format

    When done, report:
    - **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    - What you implemented (or what you attempted, if blocked)
    - What you tested and test results
    - Files changed
    - Self-review findings (if any)
    - Any issues or concerns

    Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
    Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
    information that wasn't provided. Never silently produce work you're unsure about.
```

## Controller notes

- codex-worker prepends a status line (`[codex gpt-5.6-sol / effort max / exit N / M min]`) and appends the list of files codex actually touched (`git status --porcelain`) — cross-check that list against the implementer's own "Files changed" claim before sending the work to review.
- If codex-worker reports exit 124/137 (hung / over-ran its 20-min ceiling), treat it as BLOCKED: read the partial report, split the task into smaller pieces, and re-dispatch. Do not silently re-run the same oversized task.
- Re-dispatches (fix rounds after a review) are NEW codex-worker dispatches — include the reviewer's findings verbatim plus the original task spec, since codex has no memory of the previous run.
