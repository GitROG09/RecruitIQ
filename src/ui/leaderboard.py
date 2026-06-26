import streamlit as st
import pandas as pd
from src.ui.charts import plot_candidate_radar

def get_match_badge(score: float) -> str:
    if score >= 75:
        return "🌟 Excellent"
    elif score >= 50:
        return "👍 Good"
    else:
        return "⚠️ Average"

def render_leaderboard(results):
    """
    Renders the recruiter-friendly leaderboard table.
    """
    if not results:
        return
        
    st.subheader("🏆 Candidate Leaderboard")
    
    # Prepare data for the table
    table_data = []
    for r in results:
        table_data.append({
            "Rank": r.rank,
            "Candidate ID": r.result.candidate_id,
            "Match Quality": get_match_badge(r.result.overall_score),
            "Overall Score": f"{r.result.overall_score:.2f}",
            "Semantic": f"{r.result.semantic_score:.1f}",
            "Experience": f"{r.result.experience_score:.1f}",
            "Skills": f"{r.result.skill_score:.1f}",
        })
        
    df = pd.DataFrame(table_data)
    
    # Display dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

def render_candidate_detail(results):
    """
    Renders the deep-dive panel for a selected candidate.
    """
    if not results:
        return
        
    st.divider()
    st.subheader("🔍 Candidate Deep Dive")
    
    # Candidate selector
    options = {f"Rank {r.rank} - {r.result.candidate_id} (Score: {r.result.overall_score:.2f})": r for r in results}
    selected_option = st.selectbox("Select a candidate to view details:", options.keys())
    
    if not selected_option:
        return
        
    selected_candidate = options[selected_option]
    res = selected_candidate.result
    
    # 1. Top details
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Score", f"{res.overall_score:.2f}")
    col2.metric("Semantic Confidence", f"{res.semantic_score:.2f}")
    col3.metric("Match Quality", get_match_badge(res.overall_score))
    
    st.markdown("### Recruiter Summary")
    # Generate recruiter summary from existing matcher outputs
    # We combine the "reason" fields from the reasoning dictionary
    summary_md = ""
    for entry in res.reasoning:
        matcher_name = entry["matcher"].capitalize()
        reason = entry["reason"]
        score = entry["score"]
        summary_md += f"- **{matcher_name} ({score:.1f}/100):** {reason}\n"
    
    st.info(summary_md)
    
    # 2. Charts and Skills
    col_chart, col_skills = st.columns([1, 1])
    
    with col_chart:
        st.markdown("### Score Breakdown")
        radar_fig = plot_candidate_radar(res)
        st.plotly_chart(radar_fig, use_container_width=True)
        
    with col_skills:
        st.markdown("### Skills Analysis")
        # Extract skills from the reasoning payload
        skill_entry = next((e for e in res.reasoning if e["matcher"] == "skills"), None)
        if skill_entry and "evidence" in skill_entry:
            evidence = skill_entry["evidence"]
            matched = evidence.get("matched_skills", [])
            missing = evidence.get("missing_skills", [])
            
            st.success(f"**Matched ({len(matched)}):** {', '.join(matched) if matched else 'None'}")
            st.error(f"**Missing ({len(missing)}):** {', '.join(missing) if missing else 'None'}")
            
            if "preferred_matched" in evidence and evidence["preferred_matched"]:
                st.info(f"**Preferred Matched:** {', '.join(evidence['preferred_matched'])}")
        else:
            st.write("Skill breakdown not available.")

def render_exports(csv_path, json_path):
    """
    Renders download buttons for the exported reports.
    """
    st.divider()
    st.subheader("📥 Export Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if csv_path and csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download CSV Report",
                    data=f.read(),
                    file_name="ranked_candidates.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
    with col2:
        if json_path and json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download JSON Detail",
                    data=f.read(),
                    file_name="ranked_candidates_detail.json",
                    mime="application/json",
                    use_container_width=True
                )
