import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

from utils.database import WaterDatabase
from utils.visualizations import (
    create_violation_timeline,
    create_violation_summary_pie,
    create_population_impact_bar,
    create_lead_copper_scatter,
    create_geographic_heatmap,
    create_system_scorecard
)
from utils.claude_insights import ClaudeInsights

# Page config
st.set_page_config(
    page_title="Georgia Water Quality Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and AI
@st.cache_resource
def init_resources():
    return WaterDatabase(), ClaudeInsights()

db, ai = init_resources()

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .score-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px;
    }
    .good { background-color: #d4edda; color: #155724; }
    .fair { background-color: #fff3cd; color: #856404; }
    .poor { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("💧 Georgia Water Quality Dashboard")
st.markdown("**Explore drinking water quality data for Georgia's public water systems**")

# Sidebar
with st.sidebar:
    st.header("🔍 Search & Filter")
    
    # Search box
    search_term = st.text_input(
        "Search by system name, PWSID, or city:",
        placeholder="e.g., Atlanta, GA0670000"
    )
    
    # Quick stats
    st.markdown("---")
    st.subheader("📊 Quick Stats")
    
    # Get summary stats
    summary = db.query_df("""
        SELECT 
            COUNT(DISTINCT PWSID) as total_systems,
            SUM(POPULATION_SERVED_COUNT) as total_population,
            COUNT(DISTINCT CASE WHEN PWS_TYPE_CODE = 'CWS' THEN PWSID END) as community_systems
        FROM pub_water_systems
    """).iloc[0]
    
    violations_summary = db.query_df("""
        SELECT 
            COUNT(CASE WHEN VIOLATION_STATUS = 'Unaddressed' THEN 1 END) as active_violations,
            COUNT(CASE WHEN IS_HEALTH_BASED_IND = 'Y' THEN 1 END) as health_violations
        FROM violations_enforcement
    """).iloc[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Water Systems", f"{summary['total_systems']:,}")
        st.metric("Active Violations", f"{violations_summary['active_violations']:,}")
    with col2:
        st.metric("Population Served", f"{int(summary['total_population']):,}")
        st.metric("Health Violations", f"{violations_summary['health_violations']:,}")

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Overview", 
    "🔍 System Search", 
    "📊 Violations Analysis",
    "🧪 Lead & Copper",
    "🤖 AI Insights"
])

with tab1:
    st.header("Georgia Water Quality Overview")
    
    # Top violators
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚠️ Systems with Most Active Violations")
        top_violators = db.get_top_violators(15)
        if not top_violators.empty:
            fig = create_population_impact_bar(top_violators)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Violation Status Breakdown")
        all_violations = db.query_df("SELECT VIOLATION_STATUS FROM violations_enforcement")
        if not all_violations.empty:
            fig = create_violation_summary_pie(all_violations)
            st.plotly_chart(fig, use_container_width=True)
    
    # Geographic distribution
    st.subheader("🗺️ Violations by Location")
    geo_summary = db.get_geographic_summary()
    if not geo_summary.empty:
        fig = create_geographic_heatmap(geo_summary)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Search Water Systems")
    
    if search_term:
        # Search results
        results = db.search_water_systems(search_term)
        
        if not results.empty:
            st.success(f"Found {len(results)} water systems")
            
            # Display results
            selected_pwsid = st.selectbox(
                "Select a water system to view details:",
                options=results['PWSID'].tolist(),
                format_func=lambda x: f"{results[results['PWSID']==x]['PWS_NAME'].iloc[0]} ({x})"
            )
            
            if selected_pwsid:
                # Get detailed information
                system_details = db.get_system_details(selected_pwsid)
                
                if system_details:
                    # System scorecard
                    scorecard = create_system_scorecard(system_details)
                    
                    # Display score
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.markdown(f"""
                        <div class="score-card {scorecard['color']}">
                            <h1 style="font-size: 48px; margin: 0;">{scorecard['score']}</h1>
                            <h3>Water Quality Score: {scorecard['status']}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # System info
                    st.subheader("📋 System Information")
                    system_info = system_details['system']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Population Served", f"{int(system_info.get('POPULATION_SERVED_COUNT', 0)):,}")
                        st.metric("System Type", system_info.get('PWS_TYPE_CODE', 'Unknown'))
                    with col2:
                        st.metric("Location", f"{system_info.get('CITY_NAME', 'Unknown')}, {system_info.get('STATE_CODE', 'GA')}")
                        st.metric("Owner Type", system_info.get('OWNER_TYPE_CODE', 'Unknown'))
                    with col3:
                        st.metric("Active Violations", len([v for v in system_details['violations'] if v['VIOLATION_STATUS'] == 'Unaddressed']))
                        st.metric("Total Violations", len(system_details['violations']))
                    
                    # Violations timeline
                    if system_details['violations']:
                        st.subheader("📅 Violation History")
                        violations_df = pd.DataFrame(system_details['violations'])
                        fig = create_violation_timeline(violations_df)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Violations table
                        with st.expander("View Violation Details"):
                            display_cols = ['NON_COMPL_PER_BEGIN_DATE', 'VIOLATION_DESC', 'VIOLATION_STATUS', 'IS_HEALTH_BASED_IND']
                            st.dataframe(violations_df[display_cols], use_container_width=True)
                    
                    # Site visits
                    if system_details['site_visits']:
                        st.subheader("🔍 Recent Site Visits")
                        visits_df = pd.DataFrame(system_details['site_visits'])
                        st.dataframe(visits_df[['VISIT_DATE', 'VISIT_REASON_CODE', 'VISIT_COMMENTS']].head(5))
        else:
            st.warning("No water systems found matching your search.")
    else:
        st.info("Enter a search term above to find water systems.")

with tab3:
    st.header("Violations Analysis")
    
    # Violation trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Violation Categories")
        viol_categories = db.query_df("""
            SELECT 
                VIOLATION_CATEGORY_CODE,
                COUNT(*) as count
            FROM violations_enforcement
            WHERE VIOLATION_STATUS = 'Unaddressed'
            GROUP BY VIOLATION_CATEGORY_CODE
            ORDER BY count DESC
        """)
        
        if not viol_categories.empty:
            fig = px.bar(viol_categories, x='VIOLATION_CATEGORY_CODE', y='count',
                        title="Active Violations by Category")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Health-Based vs Non-Health-Based")
        health_summary = db.query_df("""
            SELECT 
                CASE WHEN IS_HEALTH_BASED_IND = 'Y' THEN 'Health-Based' ELSE 'Non-Health-Based' END as type,
                COUNT(*) as count
            FROM violations_enforcement
            WHERE VIOLATION_STATUS = 'Unaddressed'
            GROUP BY IS_HEALTH_BASED_IND
        """)
        
        if not health_summary.empty:
            fig = px.pie(health_summary, values='count', names='type',
                        title="Health Impact of Active Violations",
                        color_discrete_map={'Health-Based': '#dc3545', 'Non-Health-Based': '#ffc107'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Most common violations
    st.subheader("Most Common Violations")
    common_violations = db.query_df("""
        SELECT 
            v.VIOLATION_CODE,
            r.VALUE_DESCRIPTION as VIOLATION_DESC,
            COUNT(*) as count
        FROM violations_enforcement v
        LEFT JOIN ref_code_values r ON v.VIOLATION_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'VIOLATION_CODE'
        WHERE v.VIOLATION_STATUS = 'Unaddressed'
        GROUP BY v.VIOLATION_CODE, r.VALUE_DESCRIPTION
        ORDER BY count DESC
        LIMIT 20
    """)
    
    if not common_violations.empty:
        st.dataframe(common_violations, use_container_width=True)

with tab4:
    st.header("Lead & Copper Analysis")
    
    # Get lead/copper data
    lcr_data = db.get_lead_copper_summary()
    
    if not lcr_data.empty:
        # Create scatter plot
        fig = create_lead_copper_scatter(lcr_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Lead Statistics")
            lead_data = lcr_data[lcr_data['CONTAMINANT_CODE'] == '5000']
            if not lead_data.empty:
                st.metric("Total Lead Tests", len(lead_data))
                st.metric("Systems Tested", lead_data['PWSID'].nunique())
                st.metric("Samples Above 15 ppb", len(lead_data[lead_data['SAMPLE_MEASURE'] > 15]))
        
        with col2:
            st.subheader("Copper Statistics")
            copper_data = lcr_data[lcr_data['CONTAMINANT_CODE'] == '5001']
            if not copper_data.empty:
                st.metric("Total Copper Tests", len(copper_data))
                st.metric("Systems Tested", copper_data['PWSID'].nunique())
                st.metric("Samples Above 1300 ppb", len(copper_data[copper_data['SAMPLE_MEASURE'] > 1300]))
        
        # Recent high results
        st.subheader("⚠️ Recent High Results")
        high_results = lcr_data[
            ((lcr_data['CONTAMINANT_CODE'] == '5000') & (lcr_data['SAMPLE_MEASURE'] > 15)) |
            ((lcr_data['CONTAMINANT_CODE'] == '5001') & (lcr_data['SAMPLE_MEASURE'] > 1300))
        ].sort_values('SAMPLING_END_DATE', ascending=False).head(10)
        
        if not high_results.empty:
            display_cols = ['PWS_NAME', 'CITY_NAME', 'CONTAMINANT_NAME', 'SAMPLE_MEASURE', 'UNIT_OF_MEASURE', 'SAMPLING_END_DATE']
            st.dataframe(high_results[display_cols], use_container_width=True)
    else:
        st.info("No lead and copper test data available.")

with tab5:
    st.header("🤖 AI-Powered Insights")
    
    if ai.enabled:
        st.success("Claude AI is connected and ready to help!")
        
        # Chat interface
        st.subheader("Ask About Water Quality")
        
        user_question = st.text_area(
            "Ask a question about Georgia's water quality:",
            placeholder="e.g., What does a Stage 2 Disinfectants violation mean? Is lead in water dangerous?",
            height=100
        )
        
        if st.button("Get Answer", type="primary"):
            if user_question:
                with st.spinner("Thinking..."):
                    response = ai.chat_query(user_question)
                    st.markdown("### Answer:")
                    st.write(response)
        
        # System analysis
        st.markdown("---")
        st.subheader("System Analysis")
        
        analysis_pwsid = st.text_input(
            "Enter PWSID for AI analysis:",
            placeholder="e.g., GA0670000"
        )
        
        if st.button("Analyze System"):
            if analysis_pwsid:
                with st.spinner("Analyzing..."):
                    system_data = db.get_system_details(analysis_pwsid)
                    if system_data:
                        analysis = ai.analyze_system_health(system_data)
                        st.markdown("### AI Analysis:")
                        st.write(analysis)
                    else:
                        st.error("System not found.")
    else:
        st.warning("""
        🔐 **Claude AI not configured**
        
        To enable AI-powered insights:
        1. Get an API key from [Anthropic](https://console.anthropic.com/)
        2. Add it to your `.env` file: `ANTHROPIC_API_KEY=your_key_here`
        3. Restart the app
        
        AI features include:
        - Plain English explanations of violations
        - Water quality assessments
        - Personalized recommendations
        - Interactive Q&A about water safety
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Data Source: Georgia Environmental Protection Division - Q1 2025 SDWIS Export</p>
    <p>Built for the Codegen Speed Trials 2025 🏁</p>
</div>
""", unsafe_allow_html=True)