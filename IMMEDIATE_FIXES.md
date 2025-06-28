# Immediate Fixes - Action Plan

## 🚨 Critical Fixes (Do Now)

### 1. ✅ Lead & Copper Tab Fixed
- Fixed tab assignment for all user roles
- Updated contaminant codes from 5000/5001 to PB90/CU90
- **STATUS**: COMPLETE

### 2. Date Parsing Issues
**Problem**: "--->" appears in date fields causing crashes
**Files affected**: 
- utils/visualizations.py
- app.py

**Fix**:
```python
# Add to all date parsing
df['date_column'] = pd.to_datetime(
    df['date_column'].replace('--->', pd.NaT), 
    format='%m/%d/%Y', 
    errors='coerce'
)
```

### 3. Add Last Inspection Date
**Value**: Users want to know when water was last checked
**Implementation**:
```python
# Add to system details view
last_inspection = db.query_df("""
    SELECT 
        MAX(VISIT_DATE) as last_visit,
        VISIT_REASON_CODE,
        DATEDIFF('day', MAX(VISIT_DATE), CURRENT_DATE) as days_ago
    FROM site_visits 
    WHERE PWSID = ?
""", (pwsid,))

# Display as metric
st.metric("Last Inspection", 
    f"{days_ago} days ago",
    delta="Due" if days_ago > 365 else "Current"
)
```

### 4. System Report Cards (A-F Grades)
**Implementation Plan**:
1. Create grading function in utils/
2. Add to search results
3. Show prominently on system details
4. Explain grade factors

**Grading Logic**:
- A: No violations in 5 years
- B: Minor violations only, resolved
- C: Some violations, mostly resolved  
- D: Active violations including health
- F: Critical unresolved health violations

### 5. Import Missing Tables
**Priority Tables**:
1. facilities - Treatment plant data
2. Already have site_visits but not using

**Quick Import**:
```python
# Add to setup_db.py
facilities_df = pd.read_csv('data/SDWA_FACILITIES.csv')
facilities_df.to_sql('facilities', conn, if_exists='replace', index=False)
```

## 🎯 Today's Sprint Plan

### Morning (2 hours)
1. [ ] Fix all date parsing issues
2. [ ] Add last inspection date to system details
3. [ ] Test fixes thoroughly

### Afternoon (3 hours)  
1. [ ] Create report card grading system
2. [ ] Add grades to search results
3. [ ] Import facilities table
4. [ ] Show treatment methods

### Evening (1 hour)
1. [ ] Update documentation
2. [ ] Test all features
3. [ ] Commit changes

## 📊 Quick Win Features

These can be added in <30 minutes each:

1. **Violation Count Badge**
   - Red badge showing active violation count
   - Add to search results

2. **Days Since Last Violation**
   - Positive metric to highlight
   - Shows improvement

3. **Population Affected Percentage**
   - Show % of Georgians affected
   - More impactful than raw numbers

4. **Top 10 Worst Systems**
   - Name and shame list
   - Motivates improvements

5. **Recently Fixed Violations**
   - Celebrate improvements
   - Show progress

## 🔥 High-Impact, Low-Effort Fixes

1. **Add to System Search Results**:
   - Last inspection date
   - Active violation count
   - Population served
   - Letter grade

2. **Add to Homepage**:
   - Statewide statistics
   - Recent improvements
   - Systems needing attention

3. **Add Help Tooltips**:
   - Explain violation codes
   - Define technical terms
   - Link to EPA standards

## 📝 Notes

- Focus on user value, not technical perfection
- Each feature should answer a user question
- Make data actionable, not just visible
- Celebrate improvements, not just problems