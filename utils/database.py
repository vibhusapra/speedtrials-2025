import sqlite3
import pandas as pd
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
DATABASE_PATH = os.getenv('DATABASE_PATH', 'georgia_water.db')

class WaterDatabase:
    def __init__(self):
        self.db_path = DATABASE_PATH
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def query_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return results as DataFrame"""
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)
    
    def search_water_systems(self, search_term: str) -> pd.DataFrame:
        """Search water systems by name, PWSID, or location"""
        query = """
        SELECT 
            PWSID,
            PWS_NAME,
            PWS_TYPE_CODE,
            POPULATION_SERVED_COUNT,
            CITY_NAME,
            STATE_CODE,
            OWNER_TYPE_CODE
        FROM pub_water_systems
        WHERE 
            UPPER(PWS_NAME) LIKE UPPER(?) OR 
            UPPER(PWSID) LIKE UPPER(?) OR 
            UPPER(CITY_NAME) LIKE UPPER(?)
        ORDER BY POPULATION_SERVED_COUNT DESC
        LIMIT 100
        """
        search_pattern = f"%{search_term}%"
        return self.query_df(query, (search_pattern, search_pattern, search_pattern))
    
    def get_system_details(self, pwsid: str) -> Dict[str, Any]:
        """Get comprehensive details for a water system"""
        # Basic info
        system_query = """
        SELECT * FROM pub_water_systems WHERE PWSID = ?
        """
        system_df = self.query_df(system_query, (pwsid,))
        
        if system_df.empty:
            return {}
        
        # Violations
        violations_query = """
        SELECT 
            v.*,
            r.VALUE_DESCRIPTION as VIOLATION_DESC
        FROM violations_enforcement v
        LEFT JOIN ref_code_values r ON v.VIOLATION_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'VIOLATION_CODE'
        WHERE v.PWSID = ?
        ORDER BY v.NON_COMPL_PER_BEGIN_DATE DESC
        """
        violations_df = self.query_df(violations_query, (pwsid,))
        
        # Recent site visits
        visits_query = """
        SELECT * FROM site_visits 
        WHERE PWSID = ? 
        ORDER BY VISIT_DATE DESC 
        LIMIT 10
        """
        visits_df = self.query_df(visits_query, (pwsid,))
        
        # Lead/Copper samples
        lcr_query = """
        SELECT * FROM lcr_samples 
        WHERE PWSID = ? 
        ORDER BY SAMPLING_END_DATE DESC
        """
        lcr_df = self.query_df(lcr_query, (pwsid,))
        
        return {
            'system': system_df.to_dict('records')[0],
            'violations': violations_df.to_dict('records'),
            'site_visits': visits_df.to_dict('records'),
            'lead_copper': lcr_df.to_dict('records')
        }
    
    def get_violation_summary(self) -> pd.DataFrame:
        """Get summary of violations by status and type"""
        query = """
        SELECT 
            VIOLATION_STATUS,
            IS_HEALTH_BASED_IND,
            VIOLATION_CATEGORY_CODE,
            COUNT(*) as count
        FROM violations_enforcement
        GROUP BY VIOLATION_STATUS, IS_HEALTH_BASED_IND, VIOLATION_CATEGORY_CODE
        ORDER BY count DESC
        """
        return self.query_df(query)
    
    def get_top_violators(self, limit: int = 20) -> pd.DataFrame:
        """Get water systems with most active violations"""
        query = """
        SELECT 
            p.PWSID,
            p.PWS_NAME,
            p.POPULATION_SERVED_COUNT,
            p.CITY_NAME,
            COUNT(DISTINCT v.VIOLATION_ID) as violation_count,
            COUNT(DISTINCT CASE WHEN v.IS_HEALTH_BASED_IND = 'Y' THEN v.VIOLATION_ID END) as health_violations
        FROM pub_water_systems p
        JOIN violations_enforcement v ON p.PWSID = v.PWSID
        WHERE v.VIOLATION_STATUS = 'Unaddressed'
        GROUP BY p.PWSID
        ORDER BY violation_count DESC
        LIMIT ?
        """
        return self.query_df(query, (limit,))
    
    def get_geographic_summary(self) -> pd.DataFrame:
        """Get violation counts by geographic area"""
        query = """
        SELECT 
            p.CITY_NAME,
            p.STATE_CODE,
            COUNT(DISTINCT p.PWSID) as system_count,
            SUM(p.POPULATION_SERVED_COUNT) as total_population,
            COUNT(DISTINCT v.VIOLATION_ID) as violation_count
        FROM pub_water_systems p
        LEFT JOIN violations_enforcement v ON p.PWSID = v.PWSID 
            AND v.VIOLATION_STATUS = 'Unaddressed'
        WHERE p.CITY_NAME IS NOT NULL
        GROUP BY p.CITY_NAME, p.STATE_CODE
        HAVING system_count > 0
        ORDER BY violation_count DESC
        """
        return self.query_df(query)
    
    def get_lead_copper_summary(self) -> pd.DataFrame:
        """Get summary of lead and copper test results"""
        query = """
        SELECT 
            l.PWSID,
            p.PWS_NAME,
            p.CITY_NAME,
            l.CONTAMINANT_CODE,
            l.SAMPLE_MEASURE,
            l.UNIT_OF_MEASURE,
            l.SAMPLING_END_DATE,
            r.VALUE_DESCRIPTION as CONTAMINANT_NAME
        FROM lcr_samples l
        JOIN pub_water_systems p ON l.PWSID = p.PWSID
        LEFT JOIN ref_code_values r ON l.CONTAMINANT_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'CONTAMINANT_CODE'
        WHERE l.CONTAMINANT_CODE IN ('PB90', 'CU90')  -- Lead and Copper 90th percentile codes
        ORDER BY l.SAMPLING_END_DATE DESC
        """
        return self.query_df(query)
    
    def get_last_inspection(self, pwsid: str) -> dict:
        """Get last inspection date and details for a system"""
        query = """
        SELECT 
            VISIT_DATE as last_visit,
            VISIT_REASON_CODE,
            JULIANDAY('now') - JULIANDAY(
                SUBSTR(VISIT_DATE, 7, 4) || '-' || 
                SUBSTR(VISIT_DATE, 1, 2) || '-' || 
                SUBSTR(VISIT_DATE, 4, 2)
            ) as days_ago,
            VISIT_COMMENTS
        FROM site_visits 
        WHERE PWSID = ?
        ORDER BY VISIT_DATE DESC
        LIMIT 1
        """
        result = self.query_df(query, (pwsid,))
        if not result.empty:
            return result.iloc[0].to_dict()
        return None
    
    def get_active_alerts(self, pwsid: str) -> dict:
        """Get active alerts including critical violations and public notifications"""
        # Get critical active violations
        critical_violations = self.query_df("""
            SELECT 
                v.VIOLATION_CODE,
                v.VIOLATION_CATEGORY_CODE,
                r.VALUE_DESCRIPTION as violation_desc,
                v.IS_HEALTH_BASED_IND,
                v.NON_COMPL_PER_BEGIN_DATE
            FROM violations_enforcement v
            LEFT JOIN ref_code_values r ON v.VIOLATION_CODE = r.VALUE_CODE 
                AND r.VALUE_TYPE = 'VIOLATION_CODE'
            WHERE v.PWSID = ?
                AND v.VIOLATION_STATUS = 'Unaddressed'
                AND (v.IS_HEALTH_BASED_IND = 'Y' 
                     OR v.VIOLATION_CODE IN ('01', '02', '03', '04', '11', '12', '21', '22', '23', '24'))
            ORDER BY v.NON_COMPL_PER_BEGIN_DATE DESC
        """, (pwsid,))
        
        # Get public notifications
        public_notifications = self.query_df("""
            SELECT 
                p.VIOLATION_CODE,
                r.VALUE_DESCRIPTION as notification_type,
                p.NON_COMPL_PER_BEGIN_DATE,
                p.COMPL_PER_END_DATE
            FROM pn_violation_assoc p
            LEFT JOIN ref_code_values r ON p.VIOLATION_CODE = r.VALUE_CODE 
                AND r.VALUE_TYPE = 'VIOLATION_CODE'
            WHERE p.PWSID = ?
                AND p.NON_COMPL_PER_END_DATE >= date('now')
            ORDER BY p.NON_COMPL_PER_BEGIN_DATE DESC
        """, (pwsid,))
        
        # Determine alert level
        alert_level = 'none'
        alerts = []
        
        # Check for critical violations
        if not critical_violations.empty:
            health_violations = critical_violations[critical_violations['IS_HEALTH_BASED_IND'] == 'Y']
            if not health_violations.empty:
                alert_level = 'critical'
                for _, v in health_violations.iterrows():
                    alerts.append({
                        'type': 'Health Violation',
                        'description': v['violation_desc'],
                        'date': v['NON_COMPL_PER_BEGIN_DATE'],
                        'severity': 'critical'
                    })
            else:
                alert_level = 'warning'
                for _, v in critical_violations.iterrows():
                    alerts.append({
                        'type': 'Violation',
                        'description': v['violation_desc'],
                        'date': v['NON_COMPL_PER_BEGIN_DATE'],
                        'severity': 'warning'
                    })
        
        # Add public notifications
        if not public_notifications.empty:
            if alert_level == 'none':
                alert_level = 'info'
            for _, n in public_notifications.iterrows():
                alerts.append({
                    'type': 'Public Notice',
                    'description': n['notification_type'],
                    'date': n['NON_COMPL_PER_BEGIN_DATE'],
                    'severity': 'info'
                })
        
        return {
            'alert_level': alert_level,
            'alerts': alerts,
            'critical_count': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_count': len([a for a in alerts if a['severity'] == 'warning']),
            'info_count': len([a for a in alerts if a['severity'] == 'info'])
        }
    
    def get_treatment_facilities(self, pwsid: str) -> pd.DataFrame:
        """Get treatment facilities for a water system"""
        query = """
        SELECT 
            f.FACILITY_ID,
            f.FACILITY_NAME,
            f.FACILITY_TYPE_CODE,
            r.VALUE_DESCRIPTION as facility_type,
            f.WATER_TYPE_CODE,
            f.IS_SOURCE_IND,
            f.IS_SOURCE_TREATED_IND,
            f.FACILITY_ACTIVITY_CODE
        FROM facilities f
        LEFT JOIN ref_code_values r ON f.FACILITY_TYPE_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'FACILITY_TYPE_CODE'
        WHERE f.PWSID = ?
            AND f.FACILITY_TYPE_CODE IN ('TP', 'WTP', 'CC', 'CH', 'PF', 'ST')
            AND (f.FACILITY_DEACTIVATION_DATE IS NULL OR f.FACILITY_DEACTIVATION_DATE = '')
        ORDER BY f.FACILITY_TYPE_CODE
        """
        return self.query_df(query, (pwsid,))
    
    def get_reference_codes(self, value_type: str) -> pd.DataFrame:
        """Get reference code descriptions"""
        query = """
        SELECT VALUE_CODE, VALUE_DESCRIPTION 
        FROM ref_code_values 
        WHERE VALUE_TYPE = ?
        ORDER BY VALUE_CODE
        """
        return self.query_df(query, (value_type,))