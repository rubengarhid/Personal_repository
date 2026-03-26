"""
Streamlit Frontend for CV-LinkedIn Comparator
Provides user interface for uploading CV and LinkedIn profile export as files.
"""

import streamlit as st
import requests
from typing import Dict

# Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="CV-LinkedIn Comparator",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #0066cc;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good      { color: #ffc107; font-weight: bold; }
    .score-poor      { color: #dc3545; font-weight: bold; }
    .skill-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    .skill-common   { background-color: #28a745; color: white; }
    .skill-cv       { background-color: #007bff; color: white; }
    .skill-linkedin { background-color: #0077b5; color: white; }
    </style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def display_skills(skills_data: Dict):
    """Display skills comparison with badges."""
    st.subheader("🎯 Skills Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**✅ Common Skills**")
        common = skills_data.get('common', [])
        if common:
            for skill in common:
                st.markdown(f"<span class='skill-badge skill-common'>{skill}</span>", unsafe_allow_html=True)
        else:
            st.info("No common skills found")
    
    with col2:
        st.markdown("**📄 CV Only**")
        cv_only = skills_data.get('cv_only', [])
        if cv_only:
            for skill in cv_only:
                st.markdown(f"<span class='skill-badge skill-cv'>{skill}</span>", unsafe_allow_html=True)
        else:
            st.success("All CV skills are on LinkedIn!")
    
    with col3:
        st.markdown("**💼 LinkedIn Only**")
        linkedin_only = skills_data.get('linkedin_only', [])
        if linkedin_only:
            for skill in linkedin_only:
                st.markdown(f"<span class='skill-badge skill-linkedin'>{skill}</span>", unsafe_allow_html=True)
        else:
            st.success("All LinkedIn skills are on CV!")
    
    match_rate = skills_data.get('match_rate', 0)
    st.progress(match_rate / 100)
    st.caption(f"Skills Match Rate: {match_rate:.1f}%")


def main():
    """Main Streamlit application."""
    
    st.markdown("<h1 class='main-header'>📄 CV vs LinkedIn Comparator</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='sub-header'>Compare your CV with your LinkedIn profile export to ensure consistency</p>",
        unsafe_allow_html=True
    )
    
    # Check API status
    with st.spinner("Checking API connection..."):
        api_healthy = check_api_health()
    
    if not api_healthy:
        st.error("⚠️ Backend API is not running. Please start the backend server first.")
        st.code("python -m uvicorn backend.main:app --reload", language="bash")
        return
    
    st.success("✅ Connected to backend API")
    st.divider()
    
    # Input section
    st.header("📝 Upload Your Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Upload CV")
        cv_file = st.file_uploader(
            "Upload your CV (PDF or DOCX)",
            type=['pdf', 'docx'],
            key="cv_uploader",
            help="Upload your CV in PDF or DOCX format"
        )
        if cv_file:
            st.success(f"✅ {cv_file.name}")
            st.caption(f"Size: {cv_file.size / 1024:.1f} KB")
    
    with col2:
        st.subheader("2️⃣ Upload LinkedIn Profile Export")
        linkedin_file = st.file_uploader(
            "Upload your LinkedIn profile PDF or DOCX",
            type=['pdf', 'docx'],
            key="linkedin_uploader",
            help=(
                "Export your LinkedIn profile as a PDF: "
                "go to your profile → More → Save to PDF. "
                "Then upload that file here."
            )
        )
        if linkedin_file:
            st.success(f"✅ {linkedin_file.name}")
            st.caption(f"Size: {linkedin_file.size / 1024:.1f} KB")
    
    st.divider()
    
    if st.button("🔍 Compare CV and LinkedIn", type="primary", use_container_width=True):
        
        if not cv_file:
            st.error("❌ Please upload a CV file")
            return
        
        if not linkedin_file:
            st.error("❌ Please upload your LinkedIn profile export")
            return
        
        with st.spinner("🔄 Analysing and comparing… This may take a moment."):
            try:
                files = {
                    'cv_file':       (cv_file.name,       cv_file.getvalue(),       cv_file.type),
                    'linkedin_file': (linkedin_file.name, linkedin_file.getvalue(), linkedin_file.type),
                }
                
                response = requests.post(
                    f"{API_URL}/compare",
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Analysis Complete!")
                    st.divider()
                    
                    # Overall Score
                    st.header("📊 Overall Match Score")
                    overall_score = result['overall_score']
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.metric(
                            label="Match Score",
                            value=f"{overall_score:.1f}%",
                            delta="Excellent!" if overall_score >= 80 else ("Needs improvement" if overall_score < 60 else "Good")
                        )
                        st.progress(overall_score / 100)
                    
                    st.divider()
                    
                    # Section Scores
                    st.header("📋 Section Breakdown")
                    section_cols = st.columns(3)
                    sections = result['section_scores']
                    
                    for idx, (section, emoji) in enumerate(zip(
                        ['experience', 'skills', 'education'],
                        ['💼', '🎯', '🎓']
                    )):
                        with section_cols[idx]:
                            score = sections.get(section, 0)
                            st.metric(label=f"{emoji} {section.title()}", value=f"{score:.1f}%")
                            st.progress(score / 100)
                    
                    st.divider()
                    
                    # Skills Analysis
                    display_skills(result['skills_comparison'])
                    
                    st.divider()
                    
                    # Recommendations
                    st.header("💡 Recommendations")
                    for rec in result.get('recommendations', []):
                        if '✅' in rec:
                            st.success(rec)
                        elif '❌' in rec:
                            st.error(rec)
                        else:
                            st.warning(rec)
                    
                    # Discrepancies
                    if result.get('discrepancies'):
                        st.divider()
                        st.header("⚠️ Discrepancies Detected")
                        for disc in result['discrepancies']:
                            severity = disc['severity']
                            section  = disc['section']
                            score    = disc['score']
                            if severity == 'high':
                                st.error(f"**{section.title()}**: Low match ({score*100:.1f}%) – Significant differences detected")
                            else:
                                st.warning(f"**{section.title()}**: Moderate match ({score*100:.1f}%) – Some differences found")
                    
                    with st.expander("🔍 View Raw JSON Response"):
                        st.json(result)
                
                else:
                    st.error(f"❌ Error {response.status_code}")
                    st.json(response.json())
            
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend API. Please ensure it's running.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.exception(e)
    
    # Footer
    st.divider()
    st.caption("💡 **Tip**: Export your LinkedIn profile as PDF (profile page → More → Save to PDF) for best parsing results.")
    
    # Sidebar
    with st.sidebar:
        st.header("📖 How to Use")
        st.markdown("""
        1. **Upload your CV** in PDF or DOCX format.
        2. **Export your LinkedIn profile**:
           - Go to your LinkedIn profile
           - Click **More** → **Save to PDF**
           - Upload the downloaded PDF here
        3. **Click Compare** to analyse both documents.
        4. **Review results** and recommendations.
        
        ### Score Interpretation
        - **80-100 %** Excellent match ✅
        - **60-79 %**  Good match ⚠️
        - **0-59 %**   Needs improvement ❌
        """)
        
        st.divider()
        st.header("ℹ️ About")
        st.markdown("""
        Uses local sentence-transformers for semantic comparison.
        No data is sent to external services – fully private.
        """)


if __name__ == "__main__":
    main()
