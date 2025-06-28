#!/usr/bin/env python3
"""Test script to verify new features"""

from utils.database import WaterDatabase
from utils.ai_insights import AIInsights

print("Testing new features...")

# Test database city query
db = WaterDatabase()
print("\n1. Testing city data query:")
city_data = db.query_df("""
    SELECT 
        p.CITY_NAME,
        COUNT(DISTINCT p.PWSID) as system_count,
        SUM(p.POPULATION_SERVED_COUNT) as total_population,
        COUNT(DISTINCT v.VIOLATION_ID) as total_violations
    FROM pub_water_systems p
    LEFT JOIN violations_enforcement v ON p.PWSID = v.PWSID
    WHERE UPPER(p.CITY_NAME) LIKE '%ATLANTA%'
    GROUP BY p.CITY_NAME
""")
print(f"Found {len(city_data)} cities matching 'ATLANTA'")
if not city_data.empty:
    print(city_data.head())

# Test AI city insights
print("\n2. Testing AI city insights:")
ai = AIInsights()
if ai.enabled:
    response = ai.get_city_insights(
        city_name="Atlanta",
        city_context="Water Systems: 5, Population: 500,000, Active Violations: 10",
        question="What are the main water quality concerns?",
        violations_data=None
    )
    print(f"AI Response: {response[:200]}...")
else:
    print("AI not enabled - check OPENAI_API_KEY")

# Test city search detection
print("\n3. Testing city search detection:")
test_searches = ["Atlanta", "GA0670000", "123456", "Columbus"]
for term in test_searches:
    is_city = term and not term.startswith('GA') and not term[0].isdigit()
    print(f"'{term}' -> City search: {is_city}")

print("\nAll tests completed!")