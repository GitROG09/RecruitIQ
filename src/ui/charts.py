import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_score_distribution(results):
    """
    Creates a histogram of overall scores.
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
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Overall Score",
        yaxis_title="Count of Candidates",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig

def plot_weight_contribution(weights):
    """
    Creates a donut chart of the current active scoring weights.
    """
    labels = list(weights.keys())
    values = list(weights.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=[label.capitalize() for label in labels], 
        values=values, 
        hole=.5,
        marker=dict(colors=px.colors.qualitative.Pastel)
    )])
    
    fig.update_layout(
        title="Weight Configuration",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark"
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
                gridcolor='rgba(255, 255, 255, 0.2)'
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.2)'
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
