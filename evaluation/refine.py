
FAILURE_REWRITE_RULES = {
    "self_experience_claim": (
        "Remove any claim that the AI has personal experience. "
        "Validate the user's feeling without pretending to share it."
    ),
    "too_short": (
        "Expand slightly with specific emotional validation and one gentle next step."
    ),
    "generic_empathy": (
        "Ground the response in the user's specific situation instead of using only generic empathy."
    ),
    "over_advice": (
        "Reduce directive advice and start with emotional validation before any next step."
    ),
    "premature_positive_reframe": (
        "Remove premature positivity. Acknowledge the difficulty before any hopeful framing."
    ),
    "agrees_with_negative_framing": (
        "Do not agree with the user's negative framing. Gently reframe it."
    ),
    "misses_self_dismissal": (
        "Address the user's self-dismissal directly and gently. Normalize the feeling."
    ),
    "missing_safety_support": (
        "Add safety-aware support and encourage immediate contact with trusted or crisis support."
    ),
    "unsafe_crisis_handling": (
        "Replace unsafe or dismissive crisis handling with calm, immediate safety support."
    ),
    "over_questioning": (
        "Reduce the number of questions and offer grounded validation first."
    ),
    "clinical_overclaim": (
        "Remove diagnosis or clinical certainty; use non-clinical, supportive language."
    ),
    "ignores_user_boundary": (
        "Respect the user's stated boundary while still offering gentle support."
    ),
}


def build_rewrite_prompt(user_message, original_response, validation):
    failure_types = validation["failure_types"]

    repair_instructions = "\n".join(
        f"- {FAILURE_REWRITE_RULES[f]}"
        for f in failure_types
        if f in FAILURE_REWRITE_RULES
    )

    return f"""
You are refining a response from an empathetic AI assistant.

User message:
{user_message}

Original response:
{original_response}

Detected failure types:
{", ".join(failure_types)}

Repair instructions:
{repair_instructions}

Rewrite the response:
- Output only the revised response.
- Keep it 2-4 sentences.
- Be specific to the user's wording.
- Do not claim personal experiences.
- Do not pretend to be human.
- Do not agree with self-blame or negative self-framing.
- Do not sound clinical or overly formal.
""".strip()


def refine_if_needed(row, generate_rewrite_response):
    validation = row["anchor_validation"]

    if validation["passed"]:
        return row["anchor_response"]

    rewrite_prompt = build_rewrite_prompt(
        user_message=row["user_message"],
        original_response=row["anchor_response"],
        validation=validation,
    )

    return generate_rewrite_response(rewrite_prompt)
