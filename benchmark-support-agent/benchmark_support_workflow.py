"""Support workflow benchmark — Statewave vs naive history dump for handoff.

Same 4-session scenario for both. Statewave produces a handoff pack via
/v1/handoff (active-issue extraction, health scoring, resolution-aware
ranking, provenance). Naive concatenates all messages.

Run:  pip install statewave httpx
      python benchmark_support_workflow.py
"""

from __future__ import annotations

import os
import sys

import httpx
from statewave import StatewaveClient

SUBJECT_ID = "bench-workflow-carol"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")

EPISODES = [
    # sess-A: billing gateway timeout (resolved — restart fixed it)
    {"session_id": "sess-A", "messages": [{"role": "user", "content": "Hi, I'm Carol from DataFlow Inc. Enterprise plan. Our billing gateway is timing out when processing payments."}]},
    {"session_id": "sess-A", "messages": [{"role": "assistant", "content": "Hi Carol! I see the gateway timeout. Let me restart the payment processing service."}]},
    {"session_id": "sess-A", "messages": [{"role": "user", "content": "That fixed it, payments are going through now. Thanks!"}]},
    # sess-B: password reset (resolved, unrelated)
    {"session_id": "sess-B", "messages": [{"role": "user", "content": "Hey, I need to reset my admin password for our dashboard."}]},
    {"session_id": "sess-B", "messages": [{"role": "assistant", "content": "Done — reset link sent to carol@dataflow.io."}]},
    # sess-C: billing gateway timeout RECURRING (open, urgent)
    {"session_id": "sess-C", "messages": [{"role": "user", "content": "The billing gateway is timing out AGAIN. This is urgent — invoices due today and payments are failing."}]},
    {"session_id": "sess-C", "messages": [{"role": "assistant", "content": "I see the timeout recurring. The restart fix from last time isn't holding. Let me check the gateway logs and escalate."}]},
    {"session_id": "sess-C", "messages": [{"role": "assistant", "content": "Escalated to the payments team. Root cause: connection pool exhaustion. They're deploying a fix."}]},
    # sess-D: active — Carol checking status
    {"session_id": "sess-D", "messages": [{"role": "user", "content": "Hi, any update on the billing gateway issue? We're still blocked and this is critical for our month-end close."}]},
]

RESOLUTIONS = [
    {"session_id": "sess-A", "status": "resolved", "resolution_summary": "Restarted payment processing service, gateway timeout resolved"},
    {"session_id": "sess-B", "status": "resolved", "resolution_summary": "Password reset link sent successfully"},
    {"session_id": "sess-C", "status": "open", "resolution_summary": "Billing gateway timeout recurring, escalated to payments team"},
]


def contains(text: str, needle: str) -> bool:
    return needle.lower() in (text or "").lower()


def naive_handoff_text() -> str:
    return "\n".join(
        f"[{m['role']}] {m['content']}"
        for ep in EPISODES
        for m in ep["messages"]
    )


def main() -> None:
    sw = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    http = httpx.Client(base_url=SERVER_URL, headers=headers)

    sw.delete_subject(SUBJECT_ID)
    for ep in EPISODES:
        # session_id isn't on the SDK yet — post directly so resolutions can link.
        http.post("/v1/episodes", json={
            "subject_id": SUBJECT_ID,
            "source": "support-chat",
            "type": "message",
            "payload": {"messages": ep["messages"]},
            "session_id": ep["session_id"],
        })
    sw.compile_memories(SUBJECT_ID)
    for r in RESOLUTIONS:
        http.post("/v1/resolutions", json={"subject_id": SUBJECT_ID, **r})

    handoff = http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    ).json()
    health = http.get(f"/v1/subjects/{SUBJECT_ID}/health").json()
    handoff2 = http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    ).json()
    naive = naive_handoff_text()
    notes = handoff.get("handoff_notes", "")

    criteria = [
        ("Active issue identified",
         contains(handoff.get("active_issue"), "gateway") or contains(handoff.get("active_issue"), "billing"),
         False),
        ("Recurring issue pattern detected",
         contains(notes, "restart") or contains(notes, "Previously Resolved"),
         False),
        ("Customer health computed",
         health.get("state") in ("watch", "at_risk") and health.get("score", 100) < 70,
         False),
        ("Health state in handoff",
         handoff.get("health_state") in ("watch", "at_risk"),
         False),
        ("Resolved issues deprioritized",
         not contains(handoff.get("active_issue"), "password"),
         False),
        ("Compact output",
         len(notes) < len(naive) * 2,
         True),
        ("Deterministic output",
         handoff.get("handoff_notes") == handoff2.get("handoff_notes"),
         True),
        ("Provenance tracing",
         len(handoff.get("provenance", {}).get("episode_ids", [])) > 0
         and len(handoff.get("provenance", {}).get("resolution_ids", [])) > 0,
         False),
    ]

    print(f"\n{'Criterion':<38} {'Statewave':>10} {'Naive':>10}")
    print("-" * 60)
    for name, sw_pass, naive_pass in criteria:
        print(f"{name:<38} {'✓' if sw_pass else '✗':>10} {'✓' if naive_pass else '✗':>10}")

    sw_score = sum(1 for _, p, _ in criteria if p)
    naive_score = sum(1 for _, _, p in criteria if p)
    print(f"\nScore: Statewave {sw_score}/{len(criteria)} | Naive {naive_score}/{len(criteria)}")

    sw.delete_subject(SUBJECT_ID)
    http.close()
    sys.exit(0 if sw_score > naive_score else 1)


if __name__ == "__main__":
    main()
