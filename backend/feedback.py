# feedback.py
"""
Feedback Generator for Evaluated Interview Answers
---------------------------------------------------
Supports:

✔ Per-question feedback 
✔ Overall summary
✔ Strengths summary
✔ Weakness summary
✔ Skill-wise scoring (accuracy, depth, clarity, relevance)
✔ Improvement plan
✔ PDF-friendly fields

Evaluator output:
{
    "question": "...",
    "score": float,
    "reason": "...",
    "criteria": {
        "accuracy": float,
        "depth": float,
        "clarity": float,
        "relevance": float
    }
}
---------------------------------------------------
"""

def classify_performance(score: float) -> str:
    if score >= 7:
        return "high"
    elif score >= 4:
        return "average"
    return "low"


def tips_for_score(performance: str) -> str:
    if performance == "high":
        return (
            "Strong answer — you covered key concepts well. "
            "Try adding real-world examples or deeper insights to reach excellence."
        )
    elif performance == "average":
        return (
            "Decent attempt — some relevant points are there, but depth or clarity is missing. "
            "Improve structure and provide more detailed explanations."
        )
    else:
        return (
            "Weak response — core concepts were either missing or unclear. "
            "Revise the fundamentals and practice structured explanations."
        )


def generate_strengths(criteria_avg):
    strengths = []
    if criteria_avg["accuracy"] >= 2:
        strengths.append("Good conceptual accuracy.")
    if criteria_avg["clarity"] >= 2:
        strengths.append("Clear and understandable explanations.")
    if criteria_avg["relevance"] >= 2:
        strengths.append("Answers remained focused and relevant to the question.")

    return strengths if strengths else ["No major strengths identified."]


def generate_weaknesses(criteria_avg):
    weaknesses = []
    if criteria_avg["depth"] < 2:
        weaknesses.append("Lack of depth in explanations.")
    if criteria_avg["accuracy"] < 1.5:
        weaknesses.append("Some conceptual inaccuracies.")
    if criteria_avg["clarity"] < 1.5:
        weaknesses.append("Explanations were unclear or poorly structured.")

    return weaknesses if weaknesses else ["No major weaknesses identified."]


def improvement_plan():
    return [
        "Revise fundamental concepts from each topic.",
        "Practice structured 3-step answers (Definition → Explanation → Example).",
        "Use real-world examples to improve depth.",
        "Increase clarity by writing shorter and more organised points."
    ]


def generate_feedback(evaluated_answers: list):
    if not evaluated_answers:
        return {
            "overall_score": 0,
            "overall_feedback": "No answers submitted.",
            "question_feedback": [],
            "strengths": [],
            "weaknesses": [],
            "skill_summary": {},
            "improvement_plan": []
        }

    question_feedback = []
    total_score = 0

    # Skill accumulators
    skills = {
        "accuracy": 0,
        "depth": 0,
        "clarity": 0,
        "relevance": 0
    }

    for item in evaluated_answers:
        score = item.get("score", 0)
        q = item.get("question", "Unknown Question")
        reason = item.get("reason", "")
        criteria = item.get("criteria", {})

        performance = classify_performance(score)
        suggestion = tips_for_score(performance)

        # Add skill-wise scoring
        for k in skills:
            skills[k] += criteria.get(k, 0)

        criteria_summary = (
            f"Accuracy: {criteria.get('accuracy', 0)}, "
            f"Depth: {criteria.get('depth', 0)}, "
            f"Clarity: {criteria.get('clarity', 0)}, "
            f"Relevance: {criteria.get('relevance', 0)}"
        )

        question_feedback.append({
            "question": q,
            "score": score,
            "performance": performance,
            "reason": reason,
            "criteria_breakdown": criteria_summary,
            "tips": suggestion
        })

        total_score += score

    # ------------------------------
    # OVERALL SCORE
    # ------------------------------
    avg = round(total_score / len(evaluated_answers), 2)

    if avg >= 7:
        overall_msg = (
            f"Excellent performance! Average score: {avg}/10. "
            "Your answers show strong understanding and clarity."
        )
    elif avg >= 4:
        overall_msg = (
            f"Average performance with a score of {avg}/10. "
            "You have a decent grasp of concepts but need to improve structure and depth."
        )
    else:
        overall_msg = (
            f"Below-average performance with a score of {avg}/10. "
            "Fundamental concepts need improvement."
        )

    # ------------------------------
    # SKILL AVERAGE SUMMARY
    # ------------------------------
    skill_summary = {k: round(v / len(evaluated_answers), 2) for k, v in skills.items()}

    # ------------------------------
    # Strengths & Weaknesses
    # ------------------------------
    strength_list = generate_strengths(skill_summary)
    weakness_list = generate_weaknesses(skill_summary)

    return {
        "evaluations": [
            {
                "question": qf["question"],
                "your_answer": qf.get("your_answer", "Not provided"),
                "score": qf["score"],
                "details": {
                    "feedback": qf["reason"],
                    "tips": qf["tips"],
                    "criteria_breakdown": qf["criteria_breakdown"]
                }
            }
            for qf in question_feedback
        ],

        "overall_score": avg,
        "overall_feedback": overall_msg,
        "strengths": strength_list,
        "weaknesses": weakness_list,
        "skill_summary": skill_summary,
        "improvement_plan": improvement_plan()
    }



# TEST BLOCK
if __name__ == "__main__":
    sample = [{
        "question": "What is AI?",
        "score": 6.2,
        "reason": "Good conceptual explanation but lacked depth.",
        "criteria": {
            "accuracy": 2.0,
            "depth": 1.2,
            "clarity": 1.8,
            "relevance": 1.0
        }
    }]

    print(generate_feedback(sample))
