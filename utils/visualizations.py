import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
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
    
    # Prepare data with error handling for invalid dates
    # Handle different date formats and invalid values
    violations_df['BEGIN_DATE'] = pd.to_datetime(
        violations_df['NON_COMPL_PER_BEGIN_DATE'], 
        format='%m/%d/%Y', 
        errors='coerce'
    )
    violations_df['END_DATE'] = pd.to_datetime(
        violations_df['NON_COMPL_PER_END_DATE'].replace('--->', pd.NaT), 
        format='%m/%d/%Y', 
        errors='coerce'
    )
    
    # Remove rows with invalid begin dates
    violations_df = violations_df.dropna(subset=['BEGIN_DATE'])
    
    # Color by status
    color_map = {
        'Resolved': '#28a745',
        'Addressed': '#ffc107',
        'Unaddressed': '#dc3545',
        'Archived': '#6c757d'
    }
    
    fig = go.Figure()
    
    # Group violations by type and status to show counts
    violation_counts = violations_df.groupby(['VIOLATION_DESC', 'VIOLATION_STATUS']).size().reset_index(name='count')
    
    for status, color in color_map.items():
        df_status = violations_df[violations_df['VIOLATION_STATUS'] == status]
        if not df_status.empty:
            # Get count for each violation type
            counts_by_type = df_status.groupby('VIOLATION_DESC').size()
            
            fig.add_trace(go.Scatter(
                x=df_status['BEGIN_DATE'],
                y=df_status['VIOLATION_DESC'],
                mode='markers',
                name=f"{status} ({len(df_status)})",
                marker=dict(color=color, size=10),
                hoverinfo='skip'  # Disable hover
            ))
    
    # Add text annotations for violation counts
    for violation_type in violations_df['VIOLATION_DESC'].unique():
        count = len(violations_df[violations_df['VIOLATION_DESC'] == violation_type])
        fig.add_annotation(
            x=violations_df[violations_df['VIOLATION_DESC'] == violation_type]['BEGIN_DATE'].max(),
            y=violation_type,
            text=f" ({count})",
            showarrow=False,
            xanchor='left',
            font=dict(size=10, color='black')
        )
    
    fig.update_layout(
        title="Violation Timeline",
        xaxis_title="Date",
        yaxis_title="Violation Type",
        height=500,
        showlegend=True,
        hovermode=False  # Disable hover mode
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
    
    # Sort by violation count to show worst offenders
    df = top_violators_df.sort_values('violation_count', ascending=True).tail(15)
    
    # Create labels with just the water system name
    df['label'] = df['PWS_NAME']
    
    # Calculate non-health violations
    df['non_health_violations'] = df['violation_count'] - df['health_violations']
    
    fig = go.Figure()
    
    # Add bars for non-health violations (base)
    fig.add_trace(go.Bar(
        name='Other Violations',
        y=df['label'],
        x=df['non_health_violations'],
        orientation='h',
        marker_color='lightblue',
        text=df['non_health_violations'].apply(lambda x: str(x) if x > 0 else ''),
        textposition='inside',
        hovertemplate='%{x} non-health violations<extra></extra>'
    ))
    
    # Add bars for health violations (stacked on top)
    fig.add_trace(go.Bar(
        name='Health-Based Violations',
        y=df['label'],
        x=df['health_violations'],
        orientation='h',
        marker_color='#dc3545',
        text=df['health_violations'].apply(lambda x: str(x) if x > 0 else ''),
        textposition='inside',
        hovertemplate='%{x} health violations<extra></extra>'
    ))
    
    # Add total count annotations at the end of each bar
    for idx, row in df.iterrows():
        fig.add_annotation(
            x=row['violation_count'] + 2,
            y=row['label'],
            text=f"Total: {row['violation_count']}",
            showarrow=False,
            font=dict(size=10, color='black'),
            xanchor='left'
        )
    
    fig.update_layout(
        title="Water Systems with Most Violations",
        xaxis_title="Number of Violations",
        yaxis_title="",
        height=600,
        barmode='stack',  # Changed to stack mode
        showlegend=True,
        margin=dict(l=250, r=80),  # Space for labels and totals
        xaxis=dict(range=[0, df['violation_count'].max() * 1.15])  # Extra space for total labels
    )
    
    return fig

def create_lead_copper_scatter(lcr_df: pd.DataFrame) -> go.Figure:
    """Create scatter plot of lead and copper levels over time"""
    if lcr_df.empty:
        return go.Figure()
    
    # Convert dates with error handling
    lcr_df['SAMPLING_DATE'] = pd.to_datetime(
        lcr_df['SAMPLING_END_DATE'].replace('--->', pd.NaT), 
        format='%m/%d/%Y', 
        errors='coerce'
    )
    
    # Remove rows with invalid dates
    lcr_df = lcr_df.dropna(subset=['SAMPLING_DATE'])
    
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
    lead_df = lcr_df[lcr_df['CONTAMINANT_CODE'] == 'PB90']
    if not lead_df.empty:
        fig.add_trace(
            go.Scatter(
                x=lead_df['SAMPLING_DATE'],
                y=lead_df['SAMPLE_MEASURE'],
                mode='markers',
                name='Lead Samples',
                marker=dict(color='blue', size=8),
                hovertemplate='%{y} ppb<extra></extra>'
            ),
            row=1, col=1
        )
        # Add action level line
        fig.add_hline(y=lead_action, line_dash="dash", line_color="red",
                      annotation_text="EPA Action Level (15 ppb)", row=1, col=1)
    
    # Copper data
    copper_df = lcr_df[lcr_df['CONTAMINANT_CODE'] == 'CU90']
    if not copper_df.empty:
        fig.add_trace(
            go.Scatter(
                x=copper_df['SAMPLING_DATE'],
                y=copper_df['SAMPLE_MEASURE'],
                mode='markers',
                name='Copper Samples',
                marker=dict(color='orange', size=8),
                hovertemplate='%{y} ppb<extra></extra>'
            ),
            row=2, col=1
        )
        # Add action level line
        fig.add_hline(y=copper_action, line_dash="dash", line_color="red",
                      annotation_text="EPA Action Level (1300 ppb)", row=2, col=1)
    
    fig.update_yaxes(title_text="Lead (ppb)", row=1, col=1)
    fig.update_yaxes(title_text="Copper (ppb)", row=2, col=1)
    fig.update_xaxes(title_text="Sampling Date", row=2, col=1)
    
    fig.update_layout(
        title="Lead and Copper Test Results",
        height=700,
        showlegend=True
    )
    
    return fig

def create_geographic_heatmap(geo_summary_df: pd.DataFrame, use_log_scale: bool = False) -> go.Figure:
    """Create choropleth map of violations by city"""
    if geo_summary_df.empty:
        return go.Figure()
    
    # Calculate additional metrics
    df = geo_summary_df.head(50).copy()  # Top 50 cities
    df['violations_per_system'] = (df['violation_count'] / df['system_count']).round(1)
    df['violations_per_1k_pop'] = ((df['violation_count'] / df['total_population']) * 1000).round(2)
    
    # Handle NaN values
    df['violations_per_system'] = df['violations_per_system'].fillna(0)
    
    # Use violation count directly for color - simpler and more intuitive
    # The size already represents count, so color can too
    min_violations = df['violation_count'].min()
    max_violations = df['violation_count'].max()
    
    # Create treemap - use violation_count for sizing, violations_per_system for color
    fig = go.Figure(go.Treemap(
        labels=df['CITY_NAME'],
        parents=['Georgia'] * len(df),
        values=df['violation_count'],
        text=[f"<b>{city}</b><br>{count} violations" for city, count in zip(df['CITY_NAME'], df['violation_count'])],
        textinfo="text",
        marker=dict(
            colorscale=[
                [0, 'white'],
                [0.1, '#fee5d9'],
                [0.2, '#fcbba1'],
                [0.3, '#fc9272'],
                [0.4, '#fb6a4a'],
                [0.5, '#ef3b2c'],
                [0.6, '#cb181d'],
                [0.7, '#a50f15'],
                [0.8, '#67000d'],
                [1.0, '#3f0000']
            ],
            cmin=min_violations,
            cmax=max_violations,
            colorbar=dict(
                title="Total<br>Violations",
                titleside="right",
                tickmode='linear',
                tick0=0,
                dtick=max(1, (max_violations - min_violations) / 5)
            ),
            colors=df['violation_count']
        ),
        customdata=df[['system_count', 'total_population', 'violations_per_system', 'violations_per_1k_pop']].values,
        hovertemplate='<b>%{label}</b><br>' +
                      'Total Violations: %{value}<br>' +
                      'Water Systems: %{customdata[0]}<br>' +
                      'Population: %{customdata[1]:,.0f}<br>' +
                      'Avg per System: %{customdata[2]}<br>' +
                      'Per 1k Population: %{customdata[3]}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Violations by City (Size & Color = Total Violations)",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
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