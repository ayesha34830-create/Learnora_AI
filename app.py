import streamlit as st
from workflow import run_workflow
from helpers import SECTIONS, validate_inputs, display_study_pack, create_download_data

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Study Pack Generator")
st.markdown(
    "Create a personalized study pack through a **4-stage AI workflow**: "
    "Planning → Content Generation → Assessment Review → Refinement."
)

with st.sidebar:
    st.header("🎓 Student Information")

    student_name = st.text_input("Student Name")
    subject = st.text_input("Subject", placeholder="e.g. Mathematics")
    topic = st.text_input("Topic / Chapter", placeholder="e.g. Quadratic Equations")

    education_level = st.selectbox(
        "Education Level",
        ["School", "College", "University", "Beginner / Self-learning"],
    )

    skill_level = st.selectbox(
        "Skill Level / Difficulty",
        ["Easy", "Medium", "Hard"],
    )

    study_duration = st.text_input(
        "Study Duration",
        placeholder="e.g. 2 hours",
    )

    learning_goal = st.text_area(
        "Learning Goal",
        placeholder="e.g. Exam preparation",
    )

    question_count = st.number_input(
        "Number of Quiz / Practice Questions",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
    )

    selected_sections = st.multiselect(
        "Sections You Want",
        SECTIONS,
        default=SECTIONS,
    )

    additional_instructions = st.text_area(
        "Additional Instructions",
        placeholder="Any special instructions for the AI?",
    )

    generate = st.button(
        "📚 Generate Study Pack",
        type="primary",
        use_container_width=True,
    )

if generate:
    error = validate_inputs(subject, topic, selected_sections)

    if error:
        st.error(error)
        st.stop()

    inputs = {
        "student_name": student_name.strip() or "Student",
        "subject": subject.strip(),
        "topic": topic.strip(),
        "education_level": education_level,
        "skill_level": skill_level,
        "study_duration": study_duration.strip() or "Not specified",
        "learning_goal": learning_goal.strip() or "Exam preparation",
        "question_count": int(question_count),
        "selected_sections": selected_sections,
        "additional_instructions": additional_instructions.strip(),
    }

    try:
        with st.status("🚀 Running AI Study Pack Workflow...", expanded=True) as status:
            st.write("🧠 Stage 1/4 — Planning")
            st.write("✍️ Stage 2/4 — Content Generation")
            st.write("🔍 Stage 3/4 — Assessment & Review")
            st.write("✨ Stage 4/4 — Refinement")

            result = run_workflow(inputs)

            status.update(
                label="✅ All 4 AI stages completed successfully!",
                state="complete",
                expanded=False,
            )

        st.session_state["result"] = result
        st.session_state["inputs"] = inputs

    except Exception as exc:
        st.error(f"Workflow error: {exc}")
        st.info(
            "Please check your GROQ_API_KEY and GROQ_MODEL settings, "
            "then try again."
        )

if "result" in st.session_state:
    result = st.session_state["result"]
    inputs = st.session_state["inputs"]

    st.divider()
    st.header("📖 Your Personalized Study Pack")
    st.caption(
        f"Student: {inputs['student_name']}  •  "
        f"Subject: {inputs['subject']}  •  "
        f"Topic: {inputs['topic']}  •  "
        f"Duration: {inputs['study_duration']}  •  "
        f"Quiz Questions: {inputs['question_count']}"
    )

    display_study_pack(result["final"])

    st.divider()
    st.subheader("🔍 AI Workflow Quality Review")

    review = result["review"]
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Review Score", str(review.get("overall_score", "N/A")))

    with col2:
        st.metric(
            "Status",
            "Approved" if review.get("approved") else "Needs Review",
        )

    with st.expander("🧠 View Planning Stage Output"):
        st.json(result["plan"])

    with st.expander("🔍 View Assessment / Review Output"):
        st.json(result["review"])

    st.download_button(
        label="⬇️ Download Study Pack as JSON",
        data=create_download_data(result["final"]),
        file_name="ai_study_pack.json",
        mime="application/json",
        use_container_width=True,
    )
