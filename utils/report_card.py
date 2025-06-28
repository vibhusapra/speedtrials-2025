"""
System Report Card Generator
Creates A-F grades for water systems based on violations and compliance
"""

from typing import Dict, List, Tuple
import pandas as pd
from datetime import datetime, timedelta

def calculate_system_grade(system_data: dict) -> Dict[str, any]:
    """
    Calculate A-F grade for a water system based on violations and compliance
    
    Grading criteria:
    - A: No violations in 5 years
    - B: Minor violations only, all resolved
    - C: Some violations, mostly resolved
    - D: Active violations including health-based
    - F: Critical health violations or many unresolved
    
    Args:
        system_data: Dictionary with violations, system info, etc.
    
    Returns:
        Dictionary with grade, score, color, and explanation
    """
    violations = system_data.get('violations', [])
    
    if not violations:
        return {
            'grade': 'A',
            'score': 100,
            'color': 'success',
            'status': 'Excellent',
            'explanation': 'No violations on record',
            'emoji': '🌟'
        }
    
    # Calculate violation metrics
    total_violations = len(violations)
    active_violations = len([v for v in violations if v.get('VIOLATION_STATUS') == 'Unaddressed'])
    health_violations = len([v for v in violations if v.get('IS_HEALTH_BASED_IND') == 'Y'])
    active_health = len([v for v in violations if v.get('VIOLATION_STATUS') == 'Unaddressed' and v.get('IS_HEALTH_BASED_IND') == 'Y'])
    
    # Calculate resolution rate
    resolved = total_violations - active_violations
    resolution_rate = (resolved / total_violations * 100) if total_violations > 0 else 100
    
    # Recent violations (last 2 years)
    recent_violations = 0
    two_years_ago = datetime.now() - timedelta(days=730)
    
    for v in violations:
        try:
            viol_date = pd.to_datetime(v.get('NON_COMPL_PER_BEGIN_DATE'))
            if viol_date and viol_date > two_years_ago:
                recent_violations += 1
        except:
            pass
    
    # Grading logic
    if active_health > 0:
        # Active health violations = automatic D or F
        if active_health >= 3:
            grade = 'F'
            score = 30
            color = 'danger'
            status = 'Critical'
            explanation = f'{active_health} active health-based violations'
            emoji = '🚨'
        else:
            grade = 'D'
            score = 50
            color = 'warning'
            status = 'Poor'
            explanation = f'{active_health} active health violation(s)'
            emoji = '⚠️'
    
    elif active_violations > 0:
        # Active non-health violations
        if active_violations >= 5:
            grade = 'D'
            score = 55
            color = 'warning'
            status = 'Poor'
            explanation = f'{active_violations} active violations'
            emoji = '⚠️'
        else:
            grade = 'C'
            score = 70
            color = 'info'
            status = 'Fair'
            explanation = f'{active_violations} active violation(s)'
            emoji = '📋'
    
    elif recent_violations > 0:
        # Recent but resolved violations
        if resolution_rate >= 90:
            grade = 'B'
            score = 85
            color = 'primary'
            status = 'Good'
            explanation = f'{recent_violations} recent violations, {resolution_rate:.0f}% resolved'
            emoji = '✅'
        else:
            grade = 'C'
            score = 75
            color = 'info'
            status = 'Fair'
            explanation = f'{recent_violations} recent violations, {resolution_rate:.0f}% resolved'
            emoji = '📋'
    
    else:
        # Old violations only
        if total_violations <= 3:
            grade = 'A'
            score = 95
            color = 'success'
            status = 'Excellent'
            explanation = 'Only minor historical violations'
            emoji = '🌟'
        else:
            grade = 'B'
            score = 80
            color = 'primary'
            status = 'Good'
            explanation = f'{total_violations} historical violations, all resolved'
            emoji = '✅'
    
    return {
        'grade': grade,
        'score': score,
        'color': color,
        'status': status,
        'explanation': explanation,
        'emoji': emoji,
        'metrics': {
            'total_violations': total_violations,
            'active_violations': active_violations,
            'health_violations': health_violations,
            'active_health': active_health,
            'resolution_rate': resolution_rate,
            'recent_violations': recent_violations
        }
    }

def get_grade_color_class(grade: str) -> str:
    """Get CSS color class for grade"""
    color_map = {
        'A': 'excellent',  # Green
        'B': 'good',       # Blue
        'C': 'fair',       # Yellow
        'D': 'poor',       # Orange
        'F': 'critical'    # Red
    }
    return color_map.get(grade, 'fair')

def get_improvement_tips(grade_data: dict) -> List[str]:
    """Get improvement tips based on grade"""
    tips = []
    metrics = grade_data.get('metrics', {})
    
    if metrics.get('active_health', 0) > 0:
        tips.append("🚨 Address health-based violations immediately")
    
    if metrics.get('active_violations', 0) > 0:
        tips.append("📋 Resolve all active violations")
    
    if metrics.get('resolution_rate', 100) < 80:
        tips.append("⏰ Improve violation resolution time")
    
    if metrics.get('recent_violations', 0) > 2:
        tips.append("🔍 Increase monitoring to prevent violations")
    
    if not tips:
        tips.append("🌟 Keep up the excellent work!")
    
    return tips