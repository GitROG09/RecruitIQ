import streamlit as st

def _badge_html(score: float, max_score: float) -> str:
    # Use relative thresholds
    if max_score == 0:
        return "<span style='color: #ef4444; font-weight: bold;'>🔴 Weak</span>"
        
    ratio = score / max_score
    if ratio >= 0.95:
        return "<span style='color: #10b981; font-weight: bold;'>🟢 Excellent</span>"
    elif ratio >= 0.85:
        return "<span style='color: #3b82f6; font-weight: bold;'>🔵 Strong</span>"
    elif ratio >= 0.70:
        return "<span style='color: #eab308; font-weight: bold;'>🟡 Good</span>"
    else:
        return "<span style='color: #ef4444; font-weight: bold;'>🔴 Weak</span>"

def render_metrics(results, processing_time: float):
    """
    Renders top-level KPIs using custom CSS cards.
    """
    if not results:
        return
        
    total_candidates = len(results)
    avg_score = sum(r.result.overall_score for r in results) / total_candidates if total_candidates else 0
    highest_score = results[0].result.overall_score if total_candidates else 0
    
    is_cached = processing_time < 1.5
    model_status = "Cached" if is_cached else "Loaded"
    first_run = f"{processing_time:.2f}s" if not is_cached else "N/A"
    cached_time = f"{processing_time:.2f}s" if is_cached else "N/A"
    
    html = f"""
    <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
        <div class="stCard" style="flex: 1; text-align: center;">
            <div data-testid="stMetricValue" style="font-size: 2.5rem;">👥 {total_candidates}</div>
            <div data-testid="stMetricLabel" style="font-size: 1rem; color: #64748b; margin-top: 0.5rem;">Candidates Processed</div>
        </div>
        <div class="stCard" style="flex: 1; text-align: center;">
            <div data-testid="stMetricValue" style="font-size: 2.5rem; color: #10b981;">🎯 {highest_score:.1f}%</div>
            <div data-testid="stMetricLabel" style="font-size: 1rem; color: #64748b; margin-top: 0.5rem;">Highest Match</div>
        </div>
        <div class="stCard" style="flex: 1; text-align: center;">
            <div data-testid="stMetricValue" style="font-size: 2.5rem;">📈 {avg_score:.1f}%</div>
            <div data-testid="stMetricLabel" style="font-size: 1rem; color: #64748b; margin-top: 0.5rem;">Average Match</div>
        </div>
        <div class="stCard" style="flex: 1; text-align: center;">
            <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
                <div style="font-size: 0.95rem; color: #f8fafc; text-align: left;">
                    <div style="margin-bottom: 0.2rem;">⏱️ <b>First Run:</b> <span style="color: #94a3b8;">{first_run}</span></div>
                    <div style="margin-bottom: 0.2rem;">⚡ <b>Cached:</b> <span style="color: #10b981;">{cached_time}</span></div>
                    <div>🤖 <b>Model:</b> <span style="color: #60a5fa;">{model_status}</span></div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)

def render_top_candidate_spotlight(results, candidate_dict):
    """
    Highlights the #1 ranked candidate prominently as the hero of the dashboard.
    """
    if not results:
        return
        
    top_cand = results[0].result
    max_score = top_cand.overall_score
    badge = _badge_html(top_cand.overall_score, max_score)
    
    # Extract role and company
    full_cand = candidate_dict.get(top_cand.candidate_id)
    name = getattr(full_cand.profile, 'anonymized_name', top_cand.candidate_id) if full_cand else top_cand.candidate_id
    role = getattr(full_cand.profile, 'current_title', 'Unknown Role') if full_cand else 'Unknown Role'
    company = getattr(full_cand.profile, 'current_company', 'Unknown Company') if full_cand else 'Unknown Company'
    
    # Identify top strengths and primary gap
    sorted_reasoning = sorted(top_cand.reasoning, key=lambda x: x["score"], reverse=True)
    top_strengths = sorted_reasoning[:3]
    primary_gap = sorted_reasoning[-1]
    
    strengths_html = "".join([f"<li style='margin-bottom: 0.5rem;'><strong style='color:#10b981;'>{r['matcher'].capitalize()}</strong>: {r['reason']}</li>" for r in top_strengths])
    gap_html = f"<li><strong style='color:#ef4444;'>{primary_gap['matcher'].capitalize()}</strong>: {primary_gap['reason']}</li>"
    
    recommendation = f"Excellent fit for this role with strong semantic alignment ({top_cand.semantic_score:.1f}%) and proven capabilities across {top_strengths[0]['matcher']} and {top_strengths[1]['matcher']} dimensions. Minor gap identified in {primary_gap['matcher']}."
    
    st.markdown("### 🏆 Top Recommended Candidate")
    
    html = f"""
    <div class="stCard" style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%); border: 1px solid rgba(59, 130, 246, 0.5); margin-bottom: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 1rem;">
            <div>
                <h1 style="margin: 0; color: #f8fafc; font-size: 2.5rem;">{name}</h1>
                <h3 style="margin: 0; color: #94a3b8; font-size: 1.2rem; font-weight: 500;">{role} at {company}</h3>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 3rem; font-weight: 800; color: #f8fafc; line-height: 1;">{top_cand.overall_score:.1f}%</div>
                <div style="font-size: 1.2rem; margin-top: 0.5rem;">{badge}</div>
            </div>
        </div>
        
        <div style="display: flex; gap: 2rem;">
            <div style="flex: 2;">
                <h4 style="color: #cbd5e1; margin-bottom: 0.5rem;">Top Strengths</h4>
                <ul style="color: #94a3b8; padding-left: 1.5rem;">
                    {strengths_html}
                </ul>
                
                <h4 style="color: #cbd5e1; margin-top: 1.5rem; margin-bottom: 0.5rem;">Primary Gap</h4>
                <ul style="color: #94a3b8; padding-left: 1.5rem;">
                    {gap_html}
                </ul>
            </div>
            
            <div style="flex: 1; background: rgba(0,0,0,0.2); padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <h4 style="color: #cbd5e1; margin-top: 0; margin-bottom: 0.5rem;">RecruitIQ Recommendation</h4>
                <p style="color: #94a3b8; line-height: 1.6; font-size: 1.05rem;">
                    {recommendation}
                </p>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <div style="color: #64748b; font-size: 0.9rem;">Semantic Confidence</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #60a5fa;">{top_cand.semantic_score:.1f}%</div>
                </div>
            </div>
        </div>
    </div>
    """
    html_minified = html.replace('\n', '')
    st.markdown(html_minified, unsafe_allow_html=True)
