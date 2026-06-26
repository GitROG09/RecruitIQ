import streamlit as st
import json
from config.scoring import MATCH_WEIGHTS

def render_sidebar():
    """
    Renders the left sidebar for RecruitIQ.
    Handles file uploads, interactive what-if weight sliders, and the Run button.
    Returns a dictionary of the inputs.
    """
    st.sidebar.title("🎯 RecruitIQ Setup")
    
    st.sidebar.header("1. Input Data")
    jd_file = st.sidebar.file_uploader("Upload Job Description (TXT)", type=["txt"])
    jd_text = None
    if jd_file:
        jd_text = jd_file.read().decode("utf-8")
    else:
        # Fallback to a default sample JD if none is provided to make testing easier
        st.sidebar.caption("Provide a .txt file, or we'll use a sample JD.")
        
    candidates_file = st.sidebar.file_uploader("Upload Candidates (JSON)", type=["json"])
    candidates_data = None
    if candidates_file:
        candidates_data = json.load(candidates_file)
    else:
        st.sidebar.caption("Provide a .json file, or we'll use sample_candidates.json.")
        
    st.sidebar.divider()
    
    st.sidebar.header("2. What-If Analysis")
    st.sidebar.markdown(
        "<small>Adjust weights to override backend defaults temporarily. "
        "Total must be close to 1.0 (100%).</small>", 
        unsafe_allow_html=True
    )
    
    # Sliders for weights
    exp_weight = st.sidebar.slider("Experience Weight", 0.0, 1.0, float(MATCH_WEIGHTS["experience"]), 0.05)
    skill_weight = st.sidebar.slider("Skills Weight", 0.0, 1.0, float(MATCH_WEIGHTS["skills"]), 0.05)
    career_weight = st.sidebar.slider("Career Weight", 0.0, 1.0, float(MATCH_WEIGHTS["career"]), 0.05)
    behav_weight = st.sidebar.slider("Behaviour Weight", 0.0, 1.0, float(MATCH_WEIGHTS["behaviour"]), 0.05)
    rec_weight = st.sidebar.slider("Recruiter Weight", 0.0, 1.0, float(MATCH_WEIGHTS["recruiter"]), 0.05)
    sem_weight = st.sidebar.slider("Semantic Weight", 0.0, 1.0, float(MATCH_WEIGHTS["semantic"]), 0.05)
    
    total_weight = exp_weight + skill_weight + career_weight + behav_weight + rec_weight + sem_weight
    st.sidebar.caption(f"**Total Weight:** {total_weight:.2f}")
    if abs(total_weight - 1.0) > 0.01:
        st.sidebar.warning("Warning: Total weight should ideally be 1.0")
        
    weights_override = {
        "experience": exp_weight,
        "skills": skill_weight,
        "career": career_weight,
        "behaviour": behav_weight,
        "recruiter": rec_weight,
        "semantic": sem_weight
    }
    
    st.sidebar.divider()
    
    run_pressed = st.sidebar.button("🚀 Run Ranking", use_container_width=True, type="primary")
    
    return {
        "jd_text": jd_text,
        "candidates_data": candidates_data,
        "weights_override": weights_override,
        "run_pressed": run_pressed
    }
