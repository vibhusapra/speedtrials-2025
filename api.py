"""
FastAPI wrapper for SDWIS data access
Provides REST endpoints for RFI compliance
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import sqlite3
import pandas as pd
import json
import io
from typing import Optional, List, Dict
from datetime import datetime

app = FastAPI(
    title="Georgia Water Quality API",
    description="REST API for accessing Georgia drinking water data",
    version="1.0.0"
)

DATABASE_PATH = "georgia_water.db"

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "Georgia Water Quality API",
        "version": "1.0.0",
        "endpoints": {
            "water_systems": "/api/pws/{pwsid}",
            "violations": "/api/violations",
            "samples": "/api/samples",
            "export": "/api/export/{data_type}"
        }
    }

@app.get("/api/pws/{pwsid}")
def get_water_system(pwsid: str):
    """Get water system details by PWSID"""
    conn = get_db_connection()
    
    # Get system info
    system_query = """
        SELECT * FROM pub_water_systems WHERE PWSID = ?
    """
    system_df = pd.read_sql_query(system_query, conn, params=(pwsid,))
    
    if system_df.empty:
        raise HTTPException(status_code=404, detail="Water system not found")
    
    # Get violations
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
    violations_df = pd.read_sql_query(violations_query, conn, params=(pwsid,))
    
    # Get recent samples
    samples_query = """
        SELECT * FROM lcr_samples 
        WHERE PWSID = ? 
        ORDER BY SAMPLING_END_DATE DESC
        LIMIT 20
    """
    samples_df = pd.read_sql_query(samples_query, conn, params=(pwsid,))
    
    conn.close()
    
    return {
        "system": system_df.to_dict('records')[0],
        "violations": violations_df.to_dict('records'),
        "recent_samples": samples_df.to_dict('records'),
        "summary": {
            "total_violations": len(violations_df),
            "active_violations": len(violations_df[violations_df['VIOLATION_STATUS'] == 'Unaddressed']),
            "health_violations": len(violations_df[violations_df['IS_HEALTH_BASED_IND'] == 'Y'])
        }
    }

@app.get("/api/violations")
def get_violations(
    status: Optional[str] = None,
    pwsid: Optional[str] = None,
    health_based: Optional[bool] = None,
    limit: int = 100
):
    """Get violations with optional filters"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            v.*,
            p.PWS_NAME,
            p.CITY_NAME,
            p.POPULATION_SERVED_COUNT,
            r.VALUE_DESCRIPTION as VIOLATION_DESC
        FROM violations_enforcement v
        JOIN pub_water_systems p ON v.PWSID = p.PWSID
        LEFT JOIN ref_code_values r ON v.VIOLATION_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'VIOLATION_CODE'
        WHERE 1=1
    """
    
    params = []
    
    if status:
        query += " AND v.VIOLATION_STATUS = ?"
        params.append(status)
    
    if pwsid:
        query += " AND v.PWSID = ?"
        params.append(pwsid)
    
    if health_based is not None:
        query += " AND v.IS_HEALTH_BASED_IND = ?"
        params.append('Y' if health_based else 'N')
    
    query += f" ORDER BY v.NON_COMPL_PER_BEGIN_DATE DESC LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return {
        "count": len(df),
        "violations": df.to_dict('records')
    }

@app.get("/api/samples")
def get_samples(
    pwsid: Optional[str] = None,
    contaminant_code: Optional[str] = None,
    limit: int = 100
):
    """Get lead/copper sample results"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            l.*,
            p.PWS_NAME,
            p.CITY_NAME,
            r.VALUE_DESCRIPTION as CONTAMINANT_NAME
        FROM lcr_samples l
        JOIN pub_water_systems p ON l.PWSID = p.PWSID
        LEFT JOIN ref_code_values r ON l.CONTAMINANT_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'CONTAMINANT_CODE'
        WHERE 1=1
    """
    
    params = []
    
    if pwsid:
        query += " AND l.PWSID = ?"
        params.append(pwsid)
    
    if contaminant_code:
        query += " AND l.CONTAMINANT_CODE = ?"
        params.append(contaminant_code)
    
    query += f" ORDER BY l.SAMPLING_END_DATE DESC LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return {
        "count": len(df),
        "samples": df.to_dict('records')
    }

@app.get("/api/export/{data_type}")
def export_data(
    data_type: str,
    format: str = "csv",
    pwsid: Optional[str] = None
):
    """Export data for QA/QC and bulk downloads"""
    
    if data_type not in ["violations", "samples", "systems", "all"]:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    conn = get_db_connection()
    
    # Build appropriate query based on data type
    if data_type == "violations":
        query = "SELECT * FROM violations_enforcement"
        if pwsid:
            query += f" WHERE PWSID = '{pwsid}'"
    
    elif data_type == "samples":
        query = "SELECT * FROM lcr_samples"
        if pwsid:
            query += f" WHERE PWSID = '{pwsid}'"
    
    elif data_type == "systems":
        query = "SELECT * FROM pub_water_systems"
        if pwsid:
            query += f" WHERE PWSID = '{pwsid}'"
    
    else:  # all
        # This would be multiple queries in production
        query = "SELECT * FROM violations_enforcement LIMIT 1000"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Format response
    if format == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(
            io.BytesIO(stream.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={data_type}_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
        return response
    else:
        return {
            "count": len(df),
            "data": df.to_dict('records')
        }

@app.get("/api/stats")
def get_statistics():
    """Get overall system statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total systems
    cursor.execute("SELECT COUNT(DISTINCT PWSID) FROM pub_water_systems")
    stats['total_systems'] = cursor.fetchone()[0]
    
    # Total population
    cursor.execute("SELECT SUM(POPULATION_SERVED_COUNT) FROM pub_water_systems")
    stats['total_population'] = cursor.fetchone()[0]
    
    # Active violations
    cursor.execute("SELECT COUNT(*) FROM violations_enforcement WHERE VIOLATION_STATUS = 'Unaddressed'")
    stats['active_violations'] = cursor.fetchone()[0]
    
    # Systems with violations
    cursor.execute("""
        SELECT COUNT(DISTINCT PWSID) 
        FROM violations_enforcement 
        WHERE VIOLATION_STATUS = 'Unaddressed'
    """)
    stats['systems_with_violations'] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats

# To run the API:
# uvicorn api:app --reload --port 8000