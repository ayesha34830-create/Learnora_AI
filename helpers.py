import json
from typing import Any, Dict, List, Optional

import streamlit as st


SECTIONS = [
    "Study Notes",
    "Learning Objectives",
    "Definitions",
    "Formulas",
    "Practice Questions",
    "Answers / Solutions",
    "MCQ Quiz",
    "Flashcards",
    "Study Plan",
    "Exam Tips",
]


def validate_inputs(
    subject: str,
    topic: str,
    selected_sections: List[str],
) -> Optional[str]:
    """Validate the most important required inputs."""
    if not subject.strip():
        return "Please enter a subject."

    if not topic.strip():
        return "Please enter a topic or chapter."

    if not selected_sections:
        return "Please select at least one study-pack section."

    return None


def create_download_data(study_pack: Dict[str, Any]) -> bytes:
    """Convert the final study pack into downloadable JSON bytes."""
    return json.dumps(
        study_pack,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")


def display_study_pack(pack: Dict[str, Any]) -> None:
    """Display each generated section in a readable Streamlit format."""

    if pack.get("topic_summary"):
        st.subheader("📝 Topic Summary")
        st.markdown(str(pack["topic_summary"]))

    if pack.get("learning_objectives"):
        st.subheader("🎯 Learning Objectives")
        for item in pack["learning_objectives"]:
            st.markdown(f"- {item}")

    if pack.get("definitions"):
        st.subheader("📚 Important Definitions")
        for item in pack["definitions"]:
            if isinstance(item, dict):
                st.markdown(
                    f"**{item.get('term', 'Term')}:** "
                    f"{item.get('definition', '')}"
                )
            else:
                st.markdown(f"- {item}")

    if pack.get("study_notes"):
        st.subheader("📒 Study Notes")
        notes = pack["study_notes"]

        if isinstance(notes, list):
            for item in notes:
                st.markdown(f"- {item}")
        else:
            st.markdown(str(notes))

    if pack.get("formulas"):
        st.subheader("➗ Important Formulas")

        for item in pack["formulas"]:
            if isinstance(item, dict):
                st.markdown(
                    f"**{item.get('name', 'Formula')}**  \n"
                    f"`{item.get('formula', '')}`  \n"
                    f"{item.get('use', '')}"
                )
            else:
                st.markdown(f"- {item}")

    if pack.get("practice_questions"):
        st.subheader("✍️ Practice Questions")

        for i, item in enumerate(pack["practice_questions"], 1):
            question = (
                item.get("question", "")
                if isinstance(item, dict)
                else str(item)
            )
            st.markdown(f"**Q{i}. {question}**")

    if pack.get("answers_solutions"):
        st.subheader("✅ Answers / Solutions")

        for i, item in enumerate(pack["answers_solutions"], 1):
            if isinstance(item, dict):
                st.markdown(
                    f"**Answer {i}:** {item.get('answer', '')}"
                )

                for step in item.get("steps", []):
                    st.markdown(f"- {step}")
            else:
                st.markdown(f"**Answer {i}:** {item}")

    if pack.get("mcq_quiz"):
        st.subheader("🧠 MCQ Quiz")

        for i, item in enumerate(pack["mcq_quiz"], 1):
            if isinstance(item, dict):
                st.markdown(
                    f"**Q{i}. {item.get('question', '')}**"
                )

                for option in item.get("options", []):
                    st.markdown(f"- {option}")

                st.caption(
                    f"Correct answer: "
                    f"{item.get('correct_answer', '')}"
                )

    if pack.get("flashcards"):
        st.subheader("🗂️ Flashcards")

        for i, item in enumerate(pack["flashcards"], 1):
            if isinstance(item, dict):
                with st.expander(
                    f"Flashcard {i}: "
                    f"{item.get('front', 'Question')}"
                ):
                    st.write(item.get("back", "Answer"))

    if pack.get("study_plan"):
        st.subheader("📅 Personalized Study Plan")

        if isinstance(pack["study_plan"], list):
            for item in pack["study_plan"]:
                st.markdown(f"- {item}")
        else:
            st.markdown(str(pack["study_plan"]))

    if pack.get("exam_tips"):
        st.subheader("🎓 Exam Tips")

        for item in pack["exam_tips"]:
            st.markdown(f"- {item}")
