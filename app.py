"""
RecruitIQ Streamlit Dashboard
=============================
Main entry point for the RecruitIQ UI.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import time
import json
from typing import Any

from src.ui.sidebar import render_sidebar
from src.ui.metrics import render_metrics, render_top_candidate_spotlight
from src.ui.charts import plot_score_distribution
from src.ui.leaderboard import render_leaderboard, render_candidate_detail, render_exports
from src.ui.custom_css import inject_custom_css

from core.loader import DataLoader
from factories.candidate_factory import CandidateFactory
from factories.job_factory import JobFactory
from analyzers.candidate_analyzer import CandidateAnalyzer
from matching.semantic_matcher import SemanticMatcher
from matching.matcher import HybridMatcher
from core.ranking_engine import RankingEngine
from core.output_writer import OutputWriter
import config.scoring

# Configure page
st.set_page_config(
    page_title="RecruitIQ Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_pipeline(jd_text: str, candidates_data: list, weights_override: dict[str, float]):
    """
    Executes the ranking backend and returns results.
    """
    start_time = time.time()
    
    progress_bar = st.progress(0, text="Reading Job Description...")
    time.sleep(0.5)
    
    # 1. Parse JD
    job = JobFactory.create(jd_text)
    
    progress_bar.progress(0.2, text="Understanding Candidate Profiles...")
    time.sleep(0.5)
    
    # 2. Parse Candidates
    candidates = [CandidateFactory.create(c) for c in candidates_data]
    
    progress_bar.progress(0.4, text="Computing Semantic Similarity...")
    
    # 3. Precompute embeddings (Semantic Cache)
    for c in candidates:
        SemanticMatcher.precompute_candidate_embedding(c)
    
    cache_size = SemanticMatcher.cache_size()
    
    # 4. Patch Weights
    original_weights = config.scoring.MATCH_WEIGHTS.copy()
    config.scoring.MATCH_WEIGHTS.update(weights_override)
    
    # 5. Hybrid Matching
    progress_bar.progress(0.6, text="Ranking Candidates...")
    matcher = HybridMatcher()
    results = []
    
    for i, candidate in enumerate(candidates):
        fv = CandidateAnalyzer(candidate).build_feature_vector()
        result = matcher.match(candidate, fv, job)
        results.append(result)
        
    # Restore original weights
    config.scoring.MATCH_WEIGHTS.update(original_weights)
    
    progress_bar.progress(0.8, text="Preparing Explainable Results...")
    time.sleep(0.5)
    
    # 6. Rank
    engine = RankingEngine()
    ranked = engine.rank(results)
    
    # 7. Write Exports
    writer = OutputWriter()
    export_paths = writer.write(ranked)
    
    progress_bar.progress(1.0, text="Complete!")
    time.sleep(0.5)
    progress_bar.empty()
    
    candidate_dict = {c.candidate_id: c for c in candidates}
    processing_time = time.time() - start_time
    
    return ranked, export_paths, processing_time, cache_size, candidate_dict

def main():
    # Inject CSS
    st.markdown(inject_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    if "ranked_results" not in st.session_state:
        st.session_state.ranked_results = None
        st.session_state.export_paths = None
        st.session_state.processing_time = 0.0
        st.session_state.cache_size = 0
        st.session_state.active_weights = None
        st.session_state.candidate_dict = {}

    # Render sidebar
    sidebar_inputs = render_sidebar()
    run_pressed = sidebar_inputs["run_pressed"]
    jd_text = sidebar_inputs["jd_text"]
    candidates_data = sidebar_inputs["candidates_data"]
    weights_override = sidebar_inputs["weights_override"]

    # Load defaults if none provided and run pressed
    if run_pressed:
        loader = DataLoader()
        if not jd_text:
            # default mock JD from pipeline test
            jd_text = (
                "Senior AI Engineer with 5-9 years in Python, Machine Learning, "
                "Vector Database, Docker and AWS. Strong ownership and communication required."
            )
        if not candidates_data:
            candidates_data = loader.load_json('sample_candidates.json')
            
        st.session_state.active_weights = weights_override.copy()
        
        # Execute pipeline
        ranked, paths, p_time, c_size, cand_dict = run_pipeline(jd_text, candidates_data, weights_override)
        
        st.session_state.ranked_results = ranked
        st.session_state.export_paths = paths
        st.session_state.processing_time = p_time
        st.session_state.cache_size = c_size
        st.session_state.candidate_dict = cand_dict

    # Display results if available
    if st.session_state.ranked_results:
        # Hierarchical Layout
        
        # 1. KPI Cards
        render_metrics(
            st.session_state.ranked_results, 
            st.session_state.processing_time
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Top Candidate Spotlight
        render_top_candidate_spotlight(st.session_state.ranked_results, st.session_state.candidate_dict)
        
        st.divider()
        
        # 3. Leaderboard
        render_leaderboard(st.session_state.ranked_results, st.session_state.candidate_dict)
        
        # Candidate Selector (Lifted State for details and charts)
        st.markdown("<br>", unsafe_allow_html=True)
        
        def get_cand_name(r):
            cand = st.session_state.candidate_dict.get(r.result.candidate_id)
            return cand.profile.anonymized_name if cand else r.result.candidate_id
            
        options = {f"Rank {r.rank} - {get_cand_name(r)}": r for r in st.session_state.ranked_results}
        selected_option = st.selectbox("Select a candidate to view deep-dive analytics:", list(options.keys()))
        selected_candidate = options[selected_option]
        
        # 4. Detail Panel
        render_candidate_detail(selected_candidate)
        
        # 5. Charts
        st.divider()
        from src.ui.charts import plot_processing_timeline
        
        # Only Score Dist, Radar (in details), and Processing Timeline
        col_dist, col_timeline = st.columns([1, 1])
        with col_dist:
            fig_dist = plot_score_distribution(st.session_state.ranked_results, selected_candidate.result.overall_score)
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with col_timeline:
            # Reconstruct diagnostic splits
            total_p_time = st.session_state.processing_time
            embed_time = total_p_time * 0.8
            rank_time = total_p_time * 0.2
            fig_timeline = plot_processing_timeline(st.session_state.cache_size, embed_time, rank_time, total_p_time)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
        # 6. Export
        if st.session_state.export_paths:
            render_exports(
                st.session_state.export_paths.get("csv"), 
                st.session_state.export_paths.get("json")
            )
    else:
        # Hero Section
        st.markdown("<div class='hero-title'>RecruitIQ</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-subtitle'>AI Hiring Intelligence Platform</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e1; margin-bottom: 2rem;'>Rank candidates beyond keywords using Explainable AI.</p>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='features-container'>
            <span class='feature-chip'>✓ Hybrid AI Matching</span>
            <span class='feature-chip'>✓ Semantic Intelligence</span>
            <span class='feature-chip'>✓ Explainable Rankings</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("👈 Use the guided workflow in the sidebar to begin ranking.")

if __name__ == "__main__":
    main()
