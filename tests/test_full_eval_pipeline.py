import pandas as pd

from scripts.run_full_eval_pipeline import run_full_pipeline


def test_full_eval_pipeline_with_fake_csv(tmp_path):
    raw_output = tmp_path / "backend_outputs.csv"
    final_output = tmp_path / "final_with_refinement.csv"
    summary_output = tmp_path / "eval_summary.csv"
    details_output = tmp_path / "eval_summary_details.csv"
    failure_counts_output = tmp_path / "eval_summary_failure_counts.csv"

    pd.DataFrame(
        [
            {
                "case_id": "fake_001",
                "scenario_type": "self_dismissal",
                "user_message": "I am probably being dramatic about this.",
                "expected_risk": "low",
                "expected_need": "reduce self-dismissal",
                "anchor_response": "You should just move on.",
                "primary_emotion": "sadness",
                "secondary_emotion": "shame",
                "crisis_detected": False,
                "intent": "venting",
                "scenario_tier": "subtle",
                "support_need": "validation",
                "safety_flag": "none",
                "is_implicit": True,
                "emotion_intensity": 0.6,
            },
            {
                "case_id": "fake_002",
                "type": "common",
                "user_message": "I got the job and I am nervous now.",
                "expected_risk": "low",
                "expected_need": "grounded encouragement",
                "reply": (
                    "It makes sense to feel nervous after getting something you wanted. "
                    "That mix of excitement and pressure can be a lot to hold."
                ),
            },
        ]
    ).to_csv(raw_output, index=False)

    result = run_full_pipeline(
        raw_output=str(raw_output),
        skip_backend=True,
        final_output=str(final_output),
        summary_output=str(summary_output),
        details_output=str(details_output),
        failure_counts_output=str(failure_counts_output),
    )

    assert result["cases"] == 2
    assert final_output.exists()
    assert summary_output.exists()
    assert details_output.exists()
    assert failure_counts_output.exists()

    final_df = pd.read_csv(final_output).fillna("")
    assert "support_plan_json" in final_df.columns
    assert "support_plan_summary" in final_df.columns
    assert "refined_anchor_response" in final_df.columns
    assert final_df.loc[0, "refined_anchor_response"] != "You should just move on."

    summary_df = pd.read_csv(summary_output).fillna("")
    assert "number_of_cases" in set(summary_df["metric"])
    assert "failure_counts" in set(summary_df["section"])
