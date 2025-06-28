import sqlite3
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.getenv('DATABASE_PATH', 'georgia_water.db')
DATA_DIR = Path('data')

def create_database():
    """Create SQLite database and import all CSV files"""
    
    # Remove existing database if it exists
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    # CSV files to import
    csv_files = {
        'pub_water_systems': 'SDWA_PUB_WATER_SYSTEMS.csv',
        'violations_enforcement': 'SDWA_VIOLATIONS_ENFORCEMENT.csv',
        'facilities': 'SDWA_FACILITIES.csv',
        'site_visits': 'SDWA_SITE_VISITS.csv',
        'geographic_areas': 'SDWA_GEOGRAPHIC_AREAS.csv',
        'service_areas': 'SDWA_SERVICE_AREAS.csv',
        'lcr_samples': 'SDWA_LCR_SAMPLES.csv',
        'events_milestones': 'SDWA_EVENTS_MILESTONES.csv',
        'pn_violation_assoc': 'SDWA_PN_VIOLATION_ASSOC.csv',
        'ref_code_values': 'SDWA_REF_CODE_VALUES.csv'
    }
    
    # Import each CSV file
    for table_name, csv_file in csv_files.items():
        csv_path = DATA_DIR / csv_file
        print(f"Importing {csv_file}...")
        
        try:
            df = pd.read_csv(csv_path, low_memory=False)
            
            # Clean column names (remove spaces, special characters)
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Write to SQLite
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✓ Imported {len(df)} rows into {table_name}")
            
        except Exception as e:
            print(f"✗ Error importing {csv_file}: {e}")
    
    # Create indexes for better performance
    print("\nCreating indexes...")
    cursor = conn.cursor()
    
    # Primary indexes
    indexes = [
        "CREATE INDEX idx_pws_pwsid ON pub_water_systems(PWSID)",
        "CREATE INDEX idx_viol_pwsid ON violations_enforcement(PWSID)",
        "CREATE INDEX idx_viol_status ON violations_enforcement(VIOLATION_STATUS)",
        "CREATE INDEX idx_fac_pwsid ON facilities(PWSID)",
        "CREATE INDEX idx_visits_pwsid ON site_visits(PWSID)",
        "CREATE INDEX idx_geo_pwsid ON geographic_areas(PWSID)",
        "CREATE INDEX idx_lcr_pwsid ON lcr_samples(PWSID)",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            print(f"✓ {idx_sql.split()[2]}")
        except Exception as e:
            print(f"✗ Error creating index: {e}")
    
    # Create useful views
    print("\nCreating views...")
    
    # Active violations view
    cursor.execute("""
        CREATE VIEW active_violations AS
        SELECT 
            v.*,
            p.PWS_NAME,
            p.POPULATION_SERVED_COUNT,
            p.CITY_NAME,
            p.STATE_CODE,
            r.VALUE_DESCRIPTION as VIOLATION_DESC
        FROM violations_enforcement v
        JOIN pub_water_systems p ON v.PWSID = p.PWSID
        LEFT JOIN ref_code_values r ON v.VIOLATION_CODE = r.VALUE_CODE 
            AND r.VALUE_TYPE = 'VIOLATION_CODE'
        WHERE v.VIOLATION_STATUS = 'Unaddressed'
    """)
    
    # System summary view
    cursor.execute("""
        CREATE VIEW system_summary AS
        SELECT 
            p.PWSID,
            p.PWS_NAME,
            p.PWS_TYPE_CODE,
            p.POPULATION_SERVED_COUNT,
            p.CITY_NAME,
            p.STATE_CODE,
            p.OWNER_TYPE_CODE,
            COUNT(DISTINCT CASE WHEN v.VIOLATION_STATUS = 'Unaddressed' THEN v.VIOLATION_ID END) as active_violations,
            COUNT(DISTINCT CASE WHEN v.IS_HEALTH_BASED_IND = 'Y' THEN v.VIOLATION_ID END) as health_violations,
            MAX(v.NON_COMPL_PER_BEGIN_DATE) as latest_violation_date
        FROM pub_water_systems p
        LEFT JOIN violations_enforcement v ON p.PWSID = v.PWSID
        GROUP BY p.PWSID
    """)
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database created successfully at {DATABASE_PATH}")
    print_database_stats()

def print_database_stats():
    """Print summary statistics of the imported data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n📊 Database Statistics:")
    print("-" * 40)
    
    # Table row counts
    tables = ['pub_water_systems', 'violations_enforcement', 'facilities', 'site_visits']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count:,} rows")
    
    # Key metrics
    cursor.execute("SELECT COUNT(DISTINCT PWSID) FROM pub_water_systems")
    print(f"\nTotal water systems: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT SUM(POPULATION_SERVED_COUNT) FROM pub_water_systems")
    pop = cursor.fetchone()[0]
    print(f"Total population served: {int(pop):,}" if pop else "Population data not available")
    
    cursor.execute("SELECT COUNT(*) FROM violations_enforcement WHERE VIOLATION_STATUS = 'Unaddressed'")
    print(f"Active violations: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(*) FROM violations_enforcement WHERE IS_HEALTH_BASED_IND = 'Y'")
    print(f"Health-based violations: {cursor.fetchone()[0]:,}")
    
    conn.close()

if __name__ == "__main__":
    create_database()