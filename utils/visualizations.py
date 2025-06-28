import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, Dict, Any
import folium

def create_violation_timeline(violations_df: pd.DataFrame) -> go.Figure:
    """Create timeline chart of violations"""
    if violations_df.empty:
        return go.Figure().add_annotation(
            text="No violations found",
            showarrow=False,
            font=dict(size=20)
        )
    
    # Prepare data
    violations_df['BEGIN_DATE'] = pd.to_datetime(violations_df['NON_COMPL_PER_BEGIN_DATE'])
    violations_df['END_DATE'] = pd.to_datetime(violations_df['NON_COMPL_PER_END_DATE'])
    
    # Color by status
    color_map = {
        'Resolved': '#28a745',
        'Addressed': '#ffc107',
        'Unaddressed': '#dc3545',
        'Archived': '#6c757d'
    }
    
    fig = go.Figure()
    
    for status, color in color_map.items():
        df_status = violations_df[violations_df['VIOLATION_STATUS'] == status]
        if not df_status.empty:
            fig.add_trace(go.Scatter(
                x=df_status['BEGIN_DATE'],
                y=df_status['VIOLATION_DESC'],
                mode='markers',
                name=status,
                marker=dict(color=color, size=10),
                text=df_status.apply(lambda x: f"Code: {x['VIOLATION_CODE']}<br>Health-based: {x['IS_HEALTH_BASED_IND']}", axis=1),
                hovertemplate='%{y}<br>%{x}<br>%{text}<extra></extra>'
            ))
    
    fig.update_layout(
        title="Violation Timeline",
        xaxis_title="Date",
        yaxis_title="Violation Type",
        height=500,
        showlegend=True,
        hovermode='closest'
    )
    
    return fig

def create_violation_summary_pie(violations_df: pd.DataFrame) -> go.Figure:
    """Create pie chart of violation status"""
    if violations_df.empty:
        return go.Figure()
    
    status_counts = violations_df['VIOLATION_STATUS'].value_counts()
    
    colors = {
        'Resolved': '#28a745',
        'Addressed': '#ffc107',
        'Unaddressed': '#dc3545',
        'Archived': '#6c757d'
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.3,
        marker=dict(colors=[colors.get(s, '#999') for s in status_counts.index])
    )])
    
    fig.update_layout(
        title="Violations by Status",
        height=400
    )
    
    return fig

def create_population_impact_bar(top_violators_df: pd.DataFrame) -> go.Figure:
    """Create bar chart showing population impacted by violations"""
    if top_violators_df.empty:
        return go.Figure()
    
    # Sort by population to show biggest impact
    df = top_violators_df.sort_values('POPULATION_SERVED_COUNT', ascending=True).tail(15)
    
    fig = go.Figure()
    
    # Add bars for total violations
    fig.add_trace(go.Bar(
        name='Total Violations',
        y=df['PWS_NAME'],
        x=df['violation_count'],
        orientation='h',
        marker_color='lightblue',
        text=df['violation_count'],
        textposition='auto',
    ))
    
    # Add bars for health violations
    fig.add_trace(go.Bar(
        name='Health-Based Violations',
        y=df['PWS_NAME'],
        x=df['health_violations'],
        orientation='h',
        marker_color='red',
        text=df['health_violations'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Water Systems with Most Violations",
        xaxis_title="Number of Violations",
        yaxis_title="Water System",
        height=600,
        barmode='overlay',
        showlegend=True
    )
    
    return fig

def create_lead_copper_scatter(lcr_df: pd.DataFrame) -> go.Figure:
    """Create scatter plot of lead and copper levels over time"""
    if lcr_df.empty:
        return go.Figure()
    
    # Convert dates
    lcr_df['SAMPLING_DATE'] = pd.to_datetime(lcr_df['SAMPLING_END_DATE'])
    
    # EPA action levels
    lead_action = 15  # ppb
    copper_action = 1300  # ppb
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Lead Levels', 'Copper Levels'),
        shared_xaxes=True,
        vertical_spacing=0.1
    )
    
    # Lead data
    lead_df = lcr_df[lcr_df['CONTAMINANT_CODE'] == '5000']
    if not lead_df.empty:
        fig.add_trace(
            go.Scatter(
                x=lead_df['SAMPLING_DATE'],
                y=lead_df['SAMPLE_MEASURE'],
                mode='markers',
                name='Lead Samples',
                marker=dict(color='blue', size=8),
                text=lead_df['PWS_NAME'],
                hovertemplate='%{text}<br>Lead: %{y} ppb<br>Date: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
        # Add action level line
        fig.add_hline(y=lead_action, line_dash="dash", line_color="red",
                      annotation_text="EPA Action Level", row=1, col=1)
    
    # Copper data
    copper_df = lcr_df[lcr_df['CONTAMINANT_CODE'] == '5001']
    if not copper_df.empty:
        fig.add_trace(
            go.Scatter(
                x=copper_df['SAMPLING_DATE'],
                y=copper_df['SAMPLE_MEASURE'],
                mode='markers',
                name='Copper Samples',
                marker=dict(color='orange', size=8),
                text=copper_df['PWS_NAME'],
                hovertemplate='%{text}<br>Copper: %{y} ppb<br>Date: %{x}<extra></extra>'
            ),
            row=2, col=1
        )
        # Add action level line
        fig.add_hline(y=copper_action, line_dash="dash", line_color="red",
                      annotation_text="EPA Action Level", row=2, col=1)
    
    fig.update_yaxes(title_text="Lead (ppb)", row=1, col=1)
    fig.update_yaxes(title_text="Copper (ppb)", row=2, col=1)
    fig.update_xaxes(title_text="Sampling Date", row=2, col=1)
    
    fig.update_layout(
        title="Lead and Copper Test Results",
        height=700,
        showlegend=True
    )
    
    return fig

def create_geographic_heatmap(geo_summary_df: pd.DataFrame) -> go.Figure:
    """Create choropleth map of violations by city"""
    if geo_summary_df.empty:
        return go.Figure()
    
    # Create treemap as alternative to geographic map
    fig = px.treemap(
        geo_summary_df.head(50),  # Top 50 cities
        path=[px.Constant("Georgia"), 'CITY_NAME'],
        values='violation_count',
        color='violation_count',
        hover_data=['system_count', 'total_population'],
        color_continuous_scale='Reds',
        title="Violations by City"
    )
    
    fig.update_layout(height=600)
    
    return fig

def create_system_scorecard(system_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create metrics for a water system scorecard"""
    system = system_data.get('system', {})
    violations = system_data.get('violations', [])
    
    # Calculate metrics
    total_violations = len(violations)
    active_violations = sum(1 for v in violations if v.get('VIOLATION_STATUS') == 'Unaddressed')
    health_violations = sum(1 for v in violations if v.get('IS_HEALTH_BASED_IND') == 'Y')
    
    # Calculate score (100 = perfect, 0 = worst)
    score = 100
    score -= active_violations * 10  # -10 for each active violation
    score -= health_violations * 5   # Additional -5 for health violations
    score = max(0, min(100, score))  # Keep between 0-100
    
    # Determine status
    if score >= 90:
        status = "Good"
        color = "green"
    elif score >= 70:
        status = "Fair"
        color = "yellow"
    else:
        status = "Poor"
        color = "red"
    
    return {
        'score': score,
        'status': status,
        'color': color,
        'metrics': {
            'Population Served': f"{int(system.get('POPULATION_SERVED_COUNT', 0)):,}",
            'Total Violations': total_violations,
            'Active Violations': active_violations,
            'Health-Based Violations': health_violations,
            'System Type': system.get('PWS_TYPE_CODE', 'Unknown'),
            'Owner Type': system.get('OWNER_TYPE_CODE', 'Unknown')
        }
    }