import streamlit as st
import json
import io
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Feedback Report")
st.title("Final Results & Feedback Report")

# ----------------------------
# LOAD RESULTS
# ----------------------------
results = (
    st.session_state.get("evaluation_results")
    or st.session_state.get("interview_results")
    or st.session_state.get("results")
    or []
)

if not isinstance(results, list):
    if isinstance(results, dict):
        results = results.get("per_question") or results.get("questions") or []
    else:
        results = []

if not results:
    st.warning("No evaluation results found. Please complete and evaluate an interview first.")
    st.page_link("pages/3_Conduct_Interview.py", label="Go to Interview", icon="🎙️")
    st.stop()

# ----------------------------
# NORMALIZATION
# ----------------------------
normalized = []

for item in results:

    # Case 1: If item is not a dict (should not happen but safe fallback)
    if not isinstance(item, dict):
        normalized.append({
            "question": str(item),
            "answer": "",
            "score": 0.0,
            "feedback": "",
            "criteria": {
                "accuracy": 0,
                "depth": 0,
                "clarity": 0,
                "relevance": 0
            },
            "domain": "General"
        })
        continue

    # Extract score safely
    score = item.get("score") or item.get("final_score") or 0.0
    try:
        score = float(score)
        if 0 <= score <= 1:
            score *= 10
    except:
        score = 0.0

    # Case 2: Proper dict normalization
    normalized.append({
        "question": item.get("question", ""),
        "answer": item.get("answer", ""),
        "score": round(score, 1),
        "feedback": item.get("feedback") or item.get("details", {}).get("feedback", ""),
        "criteria": item.get("criteria", {
            "accuracy": 0,
            "depth": 0,
            "clarity": 0,
            "relevance": 0
        }),
        "domain": item.get("domain", "General")
    })

# ----------------------------
# OVERALL AVERAGE
# ----------------------------
total = sum(r["score"] for r in normalized)
count = len(normalized)
average = total / count if count else 0

st.metric("Overall Average Score", f"{average:.1f} / 10")
st.divider()

# ============================================================
# PART 1 — BAR CHART (Question-wise scores)
# ============================================================

st.subheader("Question-wise Score Chart")
fig_bar, ax_bar = plt.subplots(figsize=(10,5))
questions = [r["question"][:40] + "..." if len(r["question"]) > 40 else r["question"] for r in normalized]
scores = [r["score"] for r in normalized]

ax_bar.barh(questions, scores)
ax_bar.set_xlabel("Score (0–10)")
ax_bar.set_title("Performance Per Question")
plt.tight_layout()

st.pyplot(fig_bar)
st.divider()

# ============================================================
# PART 3 — PIE CHART (Performance Distribution)
# ============================================================

st.subheader("Performance Distribution")
labels = ["High (8–10)", "Medium (5–7)", "Low (0–4)"]
counts = [
    sum(1 for r in normalized if r["score"] >= 8),
    sum(1 for r in normalized if 5 <= r["score"] < 8),
    sum(1 for r in normalized if r["score"] < 5)
]

fig_pie, ax_pie = plt.subplots()
ax_pie.pie(counts, labels=labels, autopct="%1.1f%%", startangle=90)
ax_pie.axis("equal")
st.pyplot(fig_pie)
st.divider()

# ============================================================
# PART 4 — Top 3 Weakest Questions
# ============================================================

weakest = sorted(normalized, key=lambda x: x["score"])[:3]

st.subheader("Your 3 Weakest Questions (Needs Improvement)")
for w in weakest:
    st.markdown(f"""
    **Question:** {w['question']}  
    **Score:** {w['score']} / 20  
    **Issue:** Weak performance.  
    **Tip:** Revise this topic. Watch 5–10 min explanations and summarise it in your own words.
    """)
    st.divider()

# ============================================================
# PART 5 — Detailed Breakdown
# ============================================================

st.header("Detailed Breakdown")
for idx, r in enumerate(normalized, start=1):
    with st.expander(f"Question {idx} — Score: {r['score']} / 20"):
        st.markdown(f"**Question:** {r['question']}")
        st.markdown("**Your answer:**")
        st.write(r["answer"])
        st.markdown("**Feedback:**")
        st.info(r["feedback"] or "No feedback received.")
st.divider()

# ============================================================
# NEW SECTION — Strengths, Weaknesses, Skill-wise Evaluation
# ============================================================

st.header("Strengths & Weaknesses Summary")

# ----------------------------
# STRENGTHS & WEAKNESSES
# ----------------------------

strengths = [r for r in normalized if r["score"] >= 8]
weaknesses = [r for r in normalized if r["score"] < 5]

st.subheader("Your Strengths 💪")
if strengths:
    for s in strengths:
        st.markdown(f"✔️ **{s['question']}** — *Excellent performance* (Score: {s['score']}/20)")
else:
    st.info("No strong areas detected yet.")

st.subheader("Your Weak Areas ⚠️")
if weaknesses:
    for w in weaknesses:
        st.markdown(f"❌ **{w['question']}** — *Needs improvement* (Score: {w['score']}/20)")
else:
    st.info("You have no major weak areas.")

st.divider()

# ----------------------------
# SKILL-WISE EVALUATION (AUTO DETECT DOMAIN FROM JSON)
# ----------------------------

st.header("Skill-wise Evaluation")

skill_scores = {}

for r in normalized:

    # 1️⃣ Direct domain from JSON
    domain = r.get("domain")

    # 2️⃣ If missing, infer from first word of the question
    if not domain or domain == "":
        parts = r["question"].split(" ")
        if parts:
            first = parts[0].lower()
            if first in ["python", "ml", "ai", "dbms", "networking"]:
                domain = first.title()
            else:
                domain = "General"

    # 3️⃣ Add to dictionary
    if domain not in skill_scores:
        skill_scores[domain] = []

    skill_scores[domain].append(r["score"])

# Display domain-wise averages
domain_avg = {d: sum(v)/len(v) for d, v in skill_scores.items()}

for d, avg in domain_avg.items():
    st.markdown(f"### 📘 {d} — **{avg:.1f} / 10**")

st.divider()

# Display skill averages
domain_avg = {d: sum(v)/len(v) for d, v in skill_scores.items()}

for d, avg in domain_avg.items():
    st.markdown(f"### 📘 {d} — **{avg:.1f} / 10**")

st.divider()

# ----------------------------
# IMPROVEMENT PLAN (AI-LIKE RULE-BASED)
# ----------------------------

st.header("Personalized Improvement Plan")

def get_improvement_plan(score):
    if score >= 8:
        return "✔️ Continue practicing advanced problems. You are strong in this area."
    elif score >= 5:
        return "⚠️ Revise core concepts and practice 2–3 medium difficulty questions."
    else:
        return "❌ Start from basics: watch short videos, read summaries, and practice 5 easy questions."

for domain, avg_score in domain_avg.items():
    st.subheader(f"📌 {domain}")
    st.write(get_improvement_plan(avg_score))

st.divider()

# ============================================================
# SUMMARY FOR PDF (REQUIRED)
# ============================================================
skill_summary = {
    "High Scores (8–10)": counts[0],
    "Medium Scores (5–7)": counts[1],
    "Low Scores (0–4)": counts[2]
}


# ============================================================
# PART 6 — PDF EXPORT  (FIXED)
# ============================================================
def create_pdf(buffer, results, summary, strengths, weaknesses, domain_avg):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # TITLE
    story.append(Paragraph("<b>Interview Feedback Report</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    # OVERALL SCORE
    story.append(Paragraph(f"<b>Overall Score:</b> {average:.1f} / 20", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # PERFORMANCE SUMMARY
    story.append(Paragraph("<b>Performance Summary:</b>", styles["Heading2"]))

    for k, v in summary.items():
        story.append(Paragraph(f"- {k}: {v}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # STRENGTHS
    story.append(Paragraph("<b>Strengths:</b>", styles["Heading2"]))
    if strengths:
        for s in strengths:
            story.append(Paragraph(
                f"✔️ {s['question']} — Score: {s['score']}/10",
                styles["Normal"]
            ))
    else:
        story.append(Paragraph("No strong areas detected.", styles["Normal"]))
    story.append(Spacer(1, 12))

    # WEAKNESSES
    story.append(Paragraph("<b>Weak Areas:</b>", styles["Heading2"]))
    if weaknesses:
        for w in weaknesses:
            story.append(Paragraph(
                f"❌ {w['question']} — Score: {w['score']}/10",
                styles["Normal"]
            ))
    else:
        story.append(Paragraph("You have no major weak areas.", styles["Normal"]))
    story.append(Spacer(1, 12))

    # SKILL-WISE EVALUATION
    story.append(Paragraph("<b>Skill-wise Evaluation:</b>", styles["Heading2"]))
    for domain, avg in domain_avg.items():
        story.append(Paragraph(f"- <b>{domain}</b>: {avg:.1f} / 10", styles["Normal"]))
    story.append(Spacer(1, 12))

    # IMPROVEMENT PLAN
    story.append(Paragraph("<b>Improvement Plan:</b>", styles["Heading2"]))
    for domain, avg_score in domain_avg.items():
        if avg_score >= 8:
            plan = "✔ Strong domain. Continue practicing advanced-level problems."
        elif avg_score >= 5:
            plan = "⚠ Needs improvement. Revise core concepts and solve medium problems."
        else:
            plan = "❌ Weak domain. Start with basics and do 5 beginner questions."

        story.append(Paragraph(f"<b>{domain}:</b> {plan}", styles["Normal"]))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 20))

    # DETAILED FEEDBACK
    story.append(Paragraph("<b>Detailed Question-wise Feedback:</b>", styles["Heading2"]))
    for r in results:
        story.append(Paragraph(f"<b>{r['question']}</b>", styles["Heading3"]))
        story.append(Paragraph(f"Score: {r['score']}/20", styles["Normal"]))
        fb = r['feedback'] if r['feedback'] else "No detailed feedback provided."
        story.append(Paragraph(f"Feedback: {fb}", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    return buffer
# ============================================================
# FINAL PDF DOWNLOAD BUTTON (FIXED)
# ============================================================

buffer = io.BytesIO()
pdf_buffer = create_pdf(buffer, normalized, skill_summary, strengths, weaknesses, domain_avg)
pdf_bytes = pdf_buffer.getvalue()

st.download_button(
    "Download Full PDF Report",
    data=pdf_bytes,
    file_name=f"Interview_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
    mime="application/pdf"
)
