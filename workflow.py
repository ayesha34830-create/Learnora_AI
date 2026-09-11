import json
import os
from typing import Any, Dict

from groq import Groq

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def get_api_key() -> str:
    """Read the Groq API key from an environment variable."""
    return os.getenv("GROQ_API_KEY", "").strip()


def get_client() -> Groq:
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your environment "
            "variable or Streamlit Secrets."
        )
    return Groq(api_key=key)


def call_ai(
    client: Groq,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 7000,
) -> str:
    """Reusable Groq API call."""
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def parse_json(text: str) -> Dict[str, Any]:
    """Parse model JSON and recover JSON wrapped in markdown fences."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("AI returned invalid JSON.")


# ============================================================
# STAGE 1 — PLANNING
# ============================================================
def planning_stage(client: Groq, inputs: Dict[str, Any]) -> Dict[str, Any]:
    system = """
You are the Planning Agent for an AI Study Pack Generator.

Analyze the learner, topic, difficulty, study duration, goal, question
count, and selected sections. Create a personalized generation plan.
Do not write the final study notes.

Return valid JSON only:
{
  "title": "...",
  "learning_objectives": ["..."],
  "content_strategy": "...",
  "difficulty_strategy": "...",
  "section_plan": [
    {
      "section": "...",
      "purpose": "...",
      "priority": "high|medium|low"
    }
  ],
  "question_strategy": "...",
  "study_plan_strategy": "..."
}
"""

    user = f"STUDENT INPUTS:\n{json.dumps(inputs, indent=2)}"

    return parse_json(call_ai(client, system, user, 0.2, 4500))


# ============================================================
# STAGE 2 — CONTENT GENERATION
# ============================================================
def generation_stage(
    client: Groq,
    inputs: Dict[str, Any],
    plan: Dict[str, Any],
) -> Dict[str, Any]:
    system = """
You are the Content Generation Agent.

Use the student's inputs AND the planning context.
Generate only the requested study-pack sections.

Return valid JSON only with these possible keys:
student_profile,
topic_summary,
learning_objectives,
definitions,
study_notes,
formulas,
practice_questions,
answers_solutions,
mcq_quiz,
flashcards,
study_plan,
exam_tips

Rules:
- Match the education level and skill level.
- Respect the study duration and learning goal.
- Generate the requested number of practice/quiz questions.
- Make MCQs have exactly four options and one correct answer.
- Give step-by-step solutions for numerical questions.
- Keep content accurate, clear, and exam-focused.
- For irrelevant formulas, use an empty list.
- Do not generate unrequested sections.
"""

    user = (
        "STUDENT INPUTS:\n"
        + json.dumps(inputs, indent=2)
        + "\n\nPLANNING CONTEXT:\n"
        + json.dumps(plan, indent=2)
    )

    return parse_json(
        call_ai(client, system, user, 0.25, 9000)
    )


# ============================================================
# STAGE 3 — ASSESSMENT / REVIEW
# ============================================================
def review_stage(
    client: Groq,
    inputs: Dict[str, Any],
    plan: Dict[str, Any],
    draft: Dict[str, Any],
) -> Dict[str, Any]:
    system = """
You are the Assessment and Quality Review Agent.

Review the draft study pack against:
1. Student education level
2. Skill/difficulty level
3. Topic relevance
4. Learning goal
5. Study duration
6. Requested sections
7. Accuracy
8. Question count
9. Practice question quality
10. MCQ quality
11. Answer correctness
12. Study-plan usefulness

Return valid JSON only:
{
  "overall_score": 0,
  "approved": true,
  "strengths": ["..."],
  "issues": [
    {
      "section": "...",
      "severity": "high|medium|low",
      "problem": "...",
      "fix": "..."
    }
  ],
  "required_refinements": ["..."]
}

Be strict and identify errors that should be fixed.
"""

    user = (
        "STUDENT INPUTS:\n"
        + json.dumps(inputs, indent=2)
        + "\n\nPLAN:\n"
        + json.dumps(plan, indent=2)
        + "\n\nDRAFT STUDY PACK:\n"
        + json.dumps(draft, indent=2)
    )

    return parse_json(
        call_ai(client, system, user, 0.1, 5000)
    )


# ============================================================
# STAGE 4 — REFINEMENT
# ============================================================
def refinement_stage(
    client: Groq,
    inputs: Dict[str, Any],
    plan: Dict[str, Any],
    draft: Dict[str, Any],
    review: Dict[str, Any],
) -> Dict[str, Any]:
    system = """
You are the Refinement Agent.

Use the student inputs, original plan, draft, and quality review.
Fix all high- and medium-severity issues. Improve low-severity issues
when practical. Preserve correct information.

Return the FINAL study pack as valid JSON only.

The final pack should contain the requested sections:
student_profile,
topic_summary,
learning_objectives,
definitions,
study_notes,
formulas,
practice_questions,
answers_solutions,
mcq_quiz,
flashcards,
study_plan,
exam_tips

Do not add unnecessary sections.
"""

    user = (
        "STUDENT INPUTS:\n"
        + json.dumps(inputs, indent=2)
        + "\n\nORIGINAL PLAN:\n"
        + json.dumps(plan, indent=2)
        + "\n\nFIRST DRAFT:\n"
        + json.dumps(draft, indent=2)
        + "\n\nQUALITY REVIEW:\n"
        + json.dumps(review, indent=2)
    )

    return parse_json(
        call_ai(client, system, user, 0.15, 9000)
    )


# ============================================================
# WORKFLOW ORCHESTRATOR
# ============================================================
def run_workflow(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all four stages.
    Each stage receives context from earlier stages.
    Errors are caught and reported with the failed stage.
    """
    client = get_client()

    try:
        plan = planning_stage(client, inputs)
    except Exception as exc:
        raise RuntimeError(f"Planning stage failed: {exc}") from exc

    try:
        draft = generation_stage(client, inputs, plan)
    except Exception as exc:
        raise RuntimeError(f"Content generation stage failed: {exc}") from exc

    try:
        review = review_stage(client, inputs, plan, draft)
    except Exception as exc:
        raise RuntimeError(f"Assessment/review stage failed: {exc}") from exc

    try:
        final_pack = refinement_stage(
            client,
            inputs,
            plan,
            draft,
            review,
        )
    except Exception as exc:
        raise RuntimeError(f"Refinement stage failed: {exc}") from exc

    return {
        "plan": plan,
        "draft": draft,
        "review": review,
        "final": final_pack,
    }
