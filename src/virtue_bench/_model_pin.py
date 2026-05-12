"""Canonical Hugging Face model revisions for ScriptureVec Justice paper runs.

Every paper-facing run was produced against the revisions pinned here.
The CLI runners thread the matching revision through to ``from_pretrained``;
override with ``--model-revision`` on the CLI to test a different snapshot.

To verify or update a pin, look the revision up on the Hugging Face hub
(``huggingface_hub.HfApi().model_info(MODEL_ID, revision="main").sha``)
and replace the value below. The ``last_modified`` field is informational
and lets a future reader reason about the snapshot in time without an
external lookup.

PINNING_STATUS:
    "verified" -- the revision below was checked against the GPU host
                  used to produce the paper's headline numbers.
    "needs_verification" -- the revision below is a best-effort placeholder
                            from the maintainer's local checkout; please
                            verify before relying on it for a published
                            reproduction.

The current status for Qwen/Qwen3-14B is "needs_verification". The pin
should be confirmed by the paper's author against the GPU host that ran
the canon discovery, book confirmation, chapter confirmation, and layer
localization sweeps in May 2026, then this docstring should be flipped
to "verified".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPin:
    model_id: str
    revision: str
    last_modified: str
    note: str


# Update the revision string after verifying against the GPU host that
# produced the paper's headline numbers (see PINNING_STATUS in the
# module docstring).
QWEN3_14B = ModelPin(
    model_id="Qwen/Qwen3-14B",
    revision="main",  # TODO: replace with the exact commit SHA used for paper runs
    last_modified="2026-05-03",  # paper-run date; HF last_modified should be earlier
    note=(
        "Headline model for the ScriptureVec Justice paper. All canon "
        "discovery, book confirmation, chapter confirmation, and layer "
        "localization runs targeted this model in bf16 on Windows GPU "
        "(paper §3.1). Replace 'main' with the verified commit SHA before "
        "publishing reproduction instructions."
    ),
)

PAPER_MODEL = QWEN3_14B


def describe(pin: ModelPin = PAPER_MODEL) -> str:
    return (
        f"{pin.model_id} @ {pin.revision} (last_modified={pin.last_modified})\n"
        f"  {pin.note}"
    )


if __name__ == "__main__":
    print(describe())
