import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_score_distribution(results, selected_score=None):
    """
    Creates a histogram of overall scores.
    Optionally highlights the score of a selected candidate with a vertical line.
    """
    scores = [r.result.overall_score for r in results]
    df = pd.DataFrame({"Score": scores})
    
    fig = px.histogram(
        df, 
        x="Score", 
        nbins=20,
        title="Score Distribution",
        color_discrete_sequence=["#3b82f6"], # Tailwind Blue 500
        template="plotly_dark"
    )
    
    # Add vertical line for the selected candidate
    if selected_score is not None:
        fig.add_vline(
            x=selected_score, 
            line_dash="dash", 
            line_color="#10b981", # Tailwind Emerald 500
            annotation_text="Selected", 
            annotation_position="top right"
        )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Overall Score",
        yaxis_title="Count of Candidates",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig

def plot_candidate_radar(match_result):
    """
    Creates a radar chart showing the candidate's scores across the 6 dimensions.
    """
    categories = ['Experience', 'Skills', 'Career', 'Behaviour', 'Recruiter', 'Semantic']
    
    scores = [
        match_result.experience_score,
        match_result.skill_score,
        match_result.career_score,
        match_result.behaviour_score,
        match_result.recruiter_score,
        match_result.semantic_score
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]], # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        name='Candidate',
        line=dict(color='#10b981'), # Tailwind Emerald 500
        fillcolor='rgba(16, 185, 129, 0.4)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='rgba(255, 255, 255, 0.1)'
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.1)'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark"
    )
    
    return fig

def plot_processing_timeline(cache_size, embed_time, rank_time, total_time):
    """
    Creates a horizontal stacked bar chart showing the breakdown of processing time.
    """
    df = pd.DataFrame({
        "Stage": ["Embedding Generation", "Ranking Pipeline"],
        "Time (s)": [embed_time, rank_time],
        "Pipeline": ["AI Processing", "AI Processing"]
    })
    
    fig = px.bar(
        df, 
        y="Pipeline", 
        x="Time (s)", 
        color="Stage", 
        orientation='h',
        title=f"Processing Timeline (Total: {total_time:.2f}s | Cache: {cache_size} items)",
        color_discrete_map={
            "Embedding Generation": "#8b5cf6", # Purple 500
            "Ranking Pipeline": "#f59e0b"      # Amber 500
        },
        template="plotly_dark"
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Time (Seconds)",
        yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode='stack',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    # Hide the y-axis label since there's only one bar
    fig.update_yaxes(showticklabels=False)
    
    return fig
