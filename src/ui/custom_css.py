def inject_custom_css():
    """
    Returns HTML <style> tags to inject custom CSS for a polished, modern SaaS aesthetic.
    """
    return """
    <style>
    /* Card Styling */
    .stCard {
        background-color: rgba(30, 41, 59, 0.5); /* Tailwind Slate 800 with opacity */
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stCard:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Primary Button Gradient */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: opacity 0.2s ease;
    }
    
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
    }
    
    /* Secondary Button Polish */
    .stButton > button[kind="secondary"] {
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: transparent;
    }
    
    .stButton > button[kind="secondary"]:hover {
        border: 1px solid rgba(255, 255, 255, 0.4);
        background-color: rgba(255, 255, 255, 0.05);
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: #f8fafc;
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #94a3b8;
        font-size: 0.9rem;
    }

    /* Hero Section Specific */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: #94a3b8;
        text-align: center;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    
    .feature-chip {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0 0.5rem;
        border-radius: 9999px;
        background-color: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .features-container {
        text-align: center;
        margin-bottom: 4rem;
    }
    </style>
    """
