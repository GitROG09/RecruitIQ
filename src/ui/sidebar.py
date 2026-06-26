import streamlit as st
import json
from config.scoring import MATCH_WEIGHTS

def render_sidebar():
    """
    Renders the left sidebar for RecruitIQ following a guided 5-step workflow.
    Returns a dictionary of the inputs.
    """
    st.sidebar.title("🎯 RecruitIQ Workflow")
    
    # -------------------------------------------------------------
    # Step 1: Job Description
    # -------------------------------------------------------------
    st.sidebar.markdown("### 1️⃣ Job Description")
    jd_file = st.sidebar.file_uploader("Upload JD (.txt)", type=["txt"])
    jd_text = None
    if jd_file:
        jd_text = jd_file.read().decode("utf-8")
        st.sidebar.success("JD Loaded", icon="✅")
    else:
        st.sidebar.caption("Will use sample JD if empty.")
        
    st.sidebar.divider()
    
    # -------------------------------------------------------------
    # Step 2: Candidate Dataset
    # -------------------------------------------------------------
    st.sidebar.markdown("### 2️⃣ Candidate Dataset")
    candidates_file = st.sidebar.file_uploader("Upload Candidates (.json)", type=["json"])
    candidates_data = None
    if candidates_file:
        candidates_data = json.load(candidates_file)
        st.sidebar.success(f"{len(candidates_data)} Profiles Loaded", icon="✅")
    else:
        st.sidebar.caption("Will use sample_candidates.json if empty.")
        
    st.sidebar.divider()
    
    # -------------------------------------------------------------
    # Step 3: Hiring Priorities
    # -------------------------------------------------------------
    st.sidebar.markdown("### 3️⃣ Hiring Priorities (Optional)")
    with st.sidebar.expander("Adjust AI Weights"):
        st.markdown(
            "<small>Fine-tune the ranking engine. "
            "Total should approximate 1.0.</small>", 
            unsafe_allow_html=True
        )
        exp_weight = st.slider("Experience", 0.0, 1.0, float(MATCH_WEIGHTS["experience"]), 0.05)
        skill_weight = st.slider("Skills", 0.0, 1.0, float(MATCH_WEIGHTS["skills"]), 0.05)
        career_weight = st.slider("Career", 0.0, 1.0, float(MATCH_WEIGHTS["career"]), 0.05)
        behav_weight = st.slider("Behaviour", 0.0, 1.0, float(MATCH_WEIGHTS["behaviour"]), 0.05)
        rec_weight = st.slider("Recruiter", 0.0, 1.0, float(MATCH_WEIGHTS["recruiter"]), 0.05)
        sem_weight = st.slider("Semantic", 0.0, 1.0, float(MATCH_WEIGHTS["semantic"]), 0.05)
        
        total_weight = exp_weight + skill_weight + career_weight + behav_weight + rec_weight + sem_weight
        st.caption(f"**Total Weight:** {total_weight:.2f}")
        if abs(total_weight - 1.0) > 0.01:
            st.warning("Warning: Total weight should ideally be 1.0")
            
    weights_override = {
        "experience": exp_weight,
        "skills": skill_weight,
        "career": career_weight,
        "behaviour": behav_weight,
        "recruiter": rec_weight,
        "semantic": sem_weight
    }
    
    st.sidebar.divider()
    
    # -------------------------------------------------------------
    # Step 4: Run Ranking
    # -------------------------------------------------------------
    st.sidebar.markdown("### 4️⃣ Run AI Ranking")
    run_pressed = st.sidebar.button("🚀 Analyze Candidates", use_container_width=True, type="primary")
    
    st.sidebar.divider()
    
    # -------------------------------------------------------------
    # Step 5: Review Results
    # -------------------------------------------------------------
    st.sidebar.markdown("### 5️⃣ Review Results")
    st.sidebar.caption("Explore the dashboard on the right to view deep-dive analytics and explainable recommendations.")
    
    return {
        "jd_text": jd_text,
        "candidates_data": candidates_data,
        "weights_override": weights_override,
        "run_pressed": run_pressed
    }
