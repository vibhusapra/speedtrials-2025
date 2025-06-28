# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Codegen Speed Trials challenge repository for building a modern water quality data visualization system. The goal is to transform Georgia's cryptic public drinking water data into an accessible application for three stakeholders: the public, water system operators, and regulators.

## Data Structure

The project includes 10 CSV files in the `/data` directory containing Q1 2025 SDWIS (Safe Drinking Water Information System) data:

- **SDWA_PUB_WATER_SYSTEMS.csv**: Core water system information (key: PWSID + SUBMISSIONYEARQUARTER)
- **SDWA_VIOLATIONS_ENFORCEMENT.csv**: Violations and enforcement actions
- **SDWA_SITE_VISITS.csv**: Inspection data
- **SDWA_FACILITIES.csv**: Individual facility details
- **SDWA_SERVICE_AREAS.csv**: Service area types
- **SDWA_GEOGRAPHIC_AREAS.csv**: Geographic service locations
- **SDWA_LCR_SAMPLES.csv**: Lead and Copper Rule test results
- **SDWA_EVENTS_MILESTONES.csv**: System milestone events
- **SDWA_PN_VIOLATION_ASSOC.csv**: Public notification violations
- **SDWA_REF_CODE_VALUES.csv**: Reference codes and descriptions

Key joining fields:
- `PWSID`: Unique public water system ID (2-letter state code + 7 digits)
- `SUBMISSIONYEARQUARTER`: Fiscal year + quarter (e.g., "2025Q1")

## Development Commands

Once a technology stack is chosen, add the following commands:

### Python/Django Stack
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_water_data  # Custom command to import CSVs

# Development
python manage.py runserver
python manage.py test

# Production
python manage.py collectstatic
gunicorn config.wsgi:application
```

### Node.js/React Stack
```bash
# Setup
npm install
npm run db:setup
npm run data:import

# Development
npm run dev
npm test
npm run lint

# Production
npm run build
npm start
```

### Database Setup
```bash
# PostgreSQL recommended for data integrity
createdb georgia_water
# OR SQLite for simplicity
# Automatic with most frameworks
```

### Hosting
```bash
# Local development with ngrok
ngrok http 3000  # or your port
```

## Architecture Considerations

### Data Ingestion Layer
- Create a robust CSV import system that handles the relational nature of the data
- Validate data integrity during import (foreign key relationships)
- Consider creating database views for common queries

### Database Schema
- Preserve all relationships from the CSV files
- Index on PWSID and SUBMISSIONYEARQUARTER for performance
- Consider denormalizing some data for the public interface

### API Design
- RESTful endpoints for each user type
- `/api/public/systems/{pwsid}` - Public water system info
- `/api/operator/violations` - Operator violation tracking
- `/api/regulator/inspections` - Regulator site visit data

### User Interfaces
1. **Public Interface**: Focus on clarity and accessibility
   - Simple search by location/zip code
   - Clear violation explanations
   - Water quality status indicators

2. **Operator Interface**: Operational efficiency
   - Dashboard with compliance status
   - Violation tracking and resolution
   - Notification management

3. **Regulator Interface**: Comprehensive oversight
   - Site visit scheduling and results
   - System-wide violation trends
   - Quick access during field visits

### Key Features to Implement
- Geographic search/filtering using SDWA_GEOGRAPHIC_AREAS
- Violation severity indicators (IS_HEALTH_BASED_IND)
- Historical trend analysis
- Mobile-responsive design for field use
- Export functionality for reports

## Testing and Validation

### Data Accuracy Tests
```python
# Example: Verify all violations have valid PWSID
def test_violation_pwsid_integrity():
    # All violation PWSID values should exist in PUB_WATER_SYSTEMS
    pass

# Example: Validate date consistency
def test_compliance_date_logic():
    # NON_COMPL_PER_END_DATE should be after NON_COMPL_PER_BEGIN_DATE
    pass
```

### Critical Validations
- Ensure violation counts match between tables
- Verify geographic data completeness
- Test search functionality with real Georgia locations
- Validate that health-based violations are properly highlighted

## Reference Code Decoding

Many fields use codes that need translation via SDWA_REF_CODE_VALUES.csv:
- VIOLATION_CODE
- CONTAMINANT_CODE
- SERVICE_AREA_TYPE_CODE
- ENFORCEMENT_ACTION_TYPE_CODE

Always join with the reference table when displaying data to users.

## Performance Optimization

- Cache frequently accessed data (water system basic info)
- Implement pagination for large result sets
- Consider data partitioning by SUBMISSIONYEARQUARTER
- Use database views for complex queries

## Security Considerations

- Implement proper authentication for operator/regulator interfaces
- Rate limit public API endpoints
- Sanitize all user inputs
- Log access for compliance tracking