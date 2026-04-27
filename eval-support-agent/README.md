# Support Agent Context Quality Eval

Proves that Statewave delivers correct, relevant context for support-agent scenarios.

## What this does

1. Seeds realistic multi-session support episodes for a customer
2. Compiles memories from those episodes
3. Requests context bundles for specific support tasks
4. Asserts that expected facts, preferences, and history appear in the context
5. Reports pass/fail with a quality score

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
