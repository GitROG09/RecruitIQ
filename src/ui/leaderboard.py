import streamlit as st
import pandas as pd
from src.ui.charts import plot_candidate_radar

def get_match_badge_text(score: float, max_score: float) -> str:
    if max_score == 0:
        return "🔴 Weak"
        
    ratio = score / max_score
    if ratio >= 0.95:
        return "🟢 Excellent"
    elif ratio >= 0.85:
        return "🔵 Strong"
    elif ratio >= 0.70:
        return "🟡 Good"
    else:
        return "🔴 Weak"

def render_leaderboard(results, candidate_dict):
    """
    Renders the compact recruiter-friendly leaderboard table.
    """
    if not results:
        return
        
    st.subheader("Leaderboard")
    
    max_score = max((r.result.overall_score for r in results), default=0)
    
    # Prepare data for the table
    table_data = []
    for r in results:
        full_cand = candidate_dict.get(r.result.candidate_id)
        name = getattr(full_cand.profile, 'anonymized_name', r.result.candidate_id) if full_cand else r.result.candidate_id
        role = getattr(full_cand.profile, 'current_title', 'Unknown') if full_cand else 'Unknown'
        table_data.append({
            "Rank": r.rank,
            "Candidate": name,
            "Role": role,
            "Score": f"{r.result.overall_score:.1f}%",
            "Confidence": f"{r.result.semantic_score:.1f}%",
            "Quality": get_match_badge_text(r.result.overall_score, max_score),
        })
        
    df = pd.DataFrame(table_data)
    
    # Display dataframe compactly
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=250
    )

def render_candidate_detail(selected_candidate):
    """
    Renders the deep-dive panel for a selected candidate using a 2-column layout.
    """
    if not selected_candidate:
        return
        
    res = selected_candidate.result
    
    # AI Summary Generation
    summary_sentences = []
    for entry in res.reasoning:
        summary_sentences.append(entry["reason"])
    ai_summary = " ".join(summary_sentences)
    
    # Extract skills
    skill_entry = next((e for e in res.reasoning if e["matcher"] == "skills"), None)
    matched = []
    missing = []
    if skill_entry and "evidence" in skill_entry:
        evidence = skill_entry["evidence"]
        matched = evidence.get("matched_skills", [])
        missing = evidence.get("missing_skills", [])
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.markdown("### Match Scores")
        # Custom HTML for score cards
        scores_html = f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem;">
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Experience</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.experience_score:.1f}%</div>
            </div>
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Skills</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.skill_score:.1f}%</div>
            </div>
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Career</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.career_score:.1f}%</div>
            </div>
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Behaviour</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.behaviour_score:.1f}%</div>
            </div>
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Recruiter</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.recruiter_score:.1f}%</div>
            </div>
            <div class="stCard" style="padding: 0.5rem; text-align: center;">
                <div style="color:#94a3b8; font-size: 0.8rem;">Semantic</div>
                <div style="font-weight: bold; font-size: 1.2rem;">{res.semantic_score:.1f}%</div>
            </div>
        </div>
        """
        st.markdown(scores_html.replace('\n', ''), unsafe_allow_html=True)
        
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        radar_fig = plot_candidate_radar(res)
        st.plotly_chart(radar_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown("### Recruiter Summary")
        summary_html = f"""
        <div class="stCard" style="margin-bottom: 1rem; border-left: 4px solid #3b82f6;">
            <p style="font-size: 1rem; line-height: 1.5; color: #e2e8f0; margin: 0;">
                {ai_summary}
            </p>
        </div>
        """
        st.markdown(summary_html.replace('\n', ''), unsafe_allow_html=True)
        
        # Skills
        st.markdown('<div class="stCard" style="margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom: 0.5rem;'><span style='color: #10b981; font-weight: bold;'>✓ Matched ({len(matched)}):</span> {', '.join(matched) if matched else 'None'}</div>", unsafe_allow_html=True)
        st.markdown(f"<div><span style='color: #ef4444; font-weight: bold;'>✕ Missing ({len(missing)}):</span> {', '.join(missing) if missing else 'None'}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Reasoning Breakdown
        with st.expander("View Detailed Reasoning Breakdown"):
            for entry in sorted(res.reasoning, key=lambda x: x["score"], reverse=True):
                st.markdown(f"**{entry['matcher'].capitalize()} ({entry['score']:.1f}%)**: {entry['reason']}")

def render_exports(csv_path, json_path):
    """
    Renders download buttons for the exported reports with toasts.
    """
    st.divider()
    st.subheader("Exports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if csv_path and csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                btn_csv = st.download_button(
                    label="Download CSV Report",
                    data=f.read(),
                    file_name="ranked_candidates.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="secondary"
                )
                if btn_csv:
                    st.toast("CSV downloaded successfully!", icon="✅")
                
    with col2:
        if json_path and json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                btn_json = st.download_button(
                    label="Download JSON Detail",
                    data=f.read(),
                    file_name="ranked_candidates_detail.json",
                    mime="application/json",
                    use_container_width=True,
                    type="secondary"
                )
                if btn_json:
                    st.toast("JSON downloaded successfully!", icon="✅")
