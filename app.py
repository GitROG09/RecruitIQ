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
from src.ui.metrics import render_metrics
from src.ui.charts import plot_score_distribution, plot_weight_contribution
from src.ui.leaderboard import render_leaderboard, render_candidate_detail, render_exports

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
    
    # 1. Parse JD
    job = JobFactory.create(jd_text)
    
    # 2. Parse Candidates
    candidates = [CandidateFactory.create(c) for c in candidates_data]
    
    # 3. Precompute embeddings (Semantic Cache)
    with st.spinner("Initializing AI Models & Pre-computing embeddings..."):
        for c in candidates:
            SemanticMatcher.precompute_candidate_embedding(c)
    
    cache_size = SemanticMatcher.cache_size()
    
    # 4. Patch Weights
    # We update the imported module's dictionary so the HybridMatcher sees it.
    original_weights = config.scoring.MATCH_WEIGHTS.copy()
    config.scoring.MATCH_WEIGHTS.update(weights_override)
    
    # 5. Hybrid Matching
    matcher = HybridMatcher()
    results = []
    
    progress_bar = st.progress(0, text="Matching candidates...")
    
    for i, candidate in enumerate(candidates):
        fv = CandidateAnalyzer(candidate).build_feature_vector()
        result = matcher.match(candidate, fv, job)
        results.append(result)
        progress_bar.progress((i + 1) / len(candidates), text=f"Matching {candidate.candidate_id}...")
        
    progress_bar.empty()
    
    # Restore original weights just in case
    config.scoring.MATCH_WEIGHTS.update(original_weights)
    
    # 6. Rank
    engine = RankingEngine()
    ranked = engine.rank(results)
    
    # 7. Write Exports
    writer = OutputWriter()
    export_paths = writer.write(ranked)
    
    processing_time = time.time() - start_time
    
    return ranked, export_paths, processing_time, cache_size

def main():
    st.title("🎯 RecruitIQ Ranking Engine")
    
    # Initialize session state
    if "ranked_results" not in st.session_state:
        st.session_state.ranked_results = None
        st.session_state.export_paths = None
        st.session_state.processing_time = 0.0
        st.session_state.cache_size = 0
        st.session_state.active_weights = None

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
        ranked, paths, p_time, c_size = run_pipeline(jd_text, candidates_data, weights_override)
        
        st.session_state.ranked_results = ranked
        st.session_state.export_paths = paths
        st.session_state.processing_time = p_time
        st.session_state.cache_size = c_size

    # Display results if available
    if st.session_state.ranked_results:
        st.divider()
        
        # Top KPIs
        render_metrics(
            st.session_state.ranked_results, 
            st.session_state.processing_time, 
            st.session_state.cache_size
        )
        
        st.divider()
        
        # Charts
        col_dist, col_weight = st.columns([2, 1])
        with col_dist:
            fig_dist = plot_score_distribution(st.session_state.ranked_results)
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with col_weight:
            if st.session_state.active_weights:
                fig_weight = plot_weight_contribution(st.session_state.active_weights)
                st.plotly_chart(fig_weight, use_container_width=True)
                
        # Leaderboard
        render_leaderboard(st.session_state.ranked_results)
        
        # Detail Panel
        render_candidate_detail(st.session_state.ranked_results)
        
        # Export
        if st.session_state.export_paths:
            render_exports(
                st.session_state.export_paths.get("csv"), 
                st.session_state.export_paths.get("json")
            )
    else:
        st.info("Upload data and click 'Run Ranking' in the sidebar to view the dashboard.")

if __name__ == "__main__":
    main()
