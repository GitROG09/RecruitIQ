import streamlit as st

def render_metrics(results, processing_time: float, cache_size: int):
    """
    Renders top-level KPIs for the ranking results.
    """
    if not results:
        return
        
    total_candidates = len(results)
    avg_score = sum(r.result.overall_score for r in results) / total_candidates if total_candidates else 0
    highest_score = results[0].result.overall_score if total_candidates else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Candidates Processed", 
            value=total_candidates,
            delta="Ranked"
        )
        
    with col2:
        st.metric(
            label="Average Score", 
            value=f"{avg_score:.1f}",
            delta=None
        )
        
    with col3:
        st.metric(
            label="Highest Match", 
            value=f"{highest_score:.1f}",
            delta="Top Candidate",
            delta_color="normal"
        )
        
    with col4:
        st.metric(
            label="Performance / Cache", 
            value=f"{processing_time:.2f}s",
            delta=f"{cache_size} Cached Embeddings",
            delta_color="off"
        )
