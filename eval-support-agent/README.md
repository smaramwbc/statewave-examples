# Support Agent Context Quality Eval

Proves that Statewave delivers correct, relevant context for support-agent scenarios.

## What this does

### Context eval (`eval_support_context.py`)

1. Seeds realistic multi-session support episodes for a customer
2. Compiles memories from those episodes
3. Requests context bundles for specific support tasks
4. Asserts that expected facts, preferences, and history appear in the context
5. Reports pass/fail with a quality score

### Handoff eval (`eval_handoff.py`)

1. Seeds a 3-session scenario with resolved and active issues
2. Creates resolution records (2 resolved, 1 open)
3. Generates a handoff context pack for the active session
4. Asserts: active issue surfaced, customer facts present, attempted steps preserved, resolved items deprioritized, output compact and deterministic, provenance tracked, **customer health state included with factors**
5. Compares against a naive "dump all history" baseline

**Health-aware handoff:** The handoff response includes `health_score`, `health_state` (healthy/watch/at_risk), and top contributing factors — so the receiving agent immediately knows if the customer is at risk and why.

### Advanced support-agent eval (`eval_support_advanced.py`)

Covers capabilities not in the basic eval:

1. Seeds a 4-session scenario with a **recurring issue pattern** (billing gateway timeout resolved, then recurring)
2. Tests session-aware ranking (active session content boosted)
3. Tests repeat-issue detection (prior resolution surfaced for recurring problem)
4. Tests customer health scoring (at-risk state computed, factors explainable)
5. Tests health-aware handoff (health state/score/factors in handoff response + notes)
6. Tests resolution-aware ranking (open issues prioritized, resolved deprioritized)
7. Tests compactness and determinism

**7 tests, 24 assertions** covering the full support-agent capability stack.

### Support-specific ranking (unit tests in `statewave/tests/test_support_ranking.py`)

Validates that Statewave's scoring model applies support-agent-specific signals:
- Open-issue episodes outrank untracked sessions (+4 boost)
- Agent/assistant action episodes outrank user greetings (+2 boost)
- Urgency keywords (critical, blocked, deadline, compliance) boost episodes (+2)
- Idle chatter (very short messages) is deprioritized (-2 penalty)
- Resolved sessions are penalized while open issues are boosted
- Combined signals produce correct ordering under tight token budgets

## Why this matters

This eval proves Statewave's context quality is **measurable and deterministic** — not anecdotal. Every deployment can run this suite to validate memory correctness.

## Run

```bash
# Requires: Statewave server running at localhost:8100
pip install statewave-py

python eval_support_context.py
```

## Expected output

```
═══ Statewave Support Agent — Context Quality Eval ═══

Scenario: Returning enterprise customer (3 sessions)
  Seeding 8 episodes... ✓
  Compiling memories... ✓ (5 memories created)

Test 1: Identity recall
  Task: "Help this customer with their billing question"
  Assertions:
    ✓ Customer name "Alice Chen" in context
    ✓ Company "Globex Corporation" in context
    ✓ Plan "Enterprise" in context
  Score: 3/3

Test 2: Preference recall
  Task: "Suggest an integration approach"
  Assertions:
    ✓ Preference "Python SDK" in context
    ✓ Preference "webhook" in context
  Score: 2/2

Test 3: History recall
  Task: "Follow up on their open issue"
  Assertions:
    ✓ Prior issue "SSO configuration" in context
    ✓ Status "escalated to engineering" in context
  Score: 2/2

Test 4: Negative — irrelevant context excluded
  Task: "Help with password reset"
  Assertions:
    ✓ Token estimate < 500 (was 287)
    ✓ No unrelated memories leaked

═══ RESULTS: 9/9 assertions passed (100%) ═══
```

## Comparison: Without Statewave

Without Statewave, a support agent either:
- Starts with zero context (fails tests 1–3 completely)
- Stuffs entire chat history into the prompt (blows token budget, fails test 4)
- Uses raw vector search (non-deterministic, no provenance, unreliable recall)

This eval quantifies the difference.
