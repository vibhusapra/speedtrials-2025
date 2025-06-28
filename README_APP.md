# 💧 Georgia Water Quality Dashboard

A modern, interactive web application for exploring Georgia's drinking water quality data. Built for the Codegen Speed Trials 2025 challenge.

## 🚀 Features

### Core Functionality
- **🔍 Smart Search**: Find water systems by name, PWSID, or city
- **📊 Interactive Visualizations**: Explore violations, trends, and water quality metrics
- **🧪 Lead & Copper Analysis**: Track contamination levels with EPA action thresholds
- **🤖 AI Insights**: Get plain English explanations powered by Claude AI
- **📈 Water Quality Scoring**: Instant assessment of system health (0-100 score)

### Key Dashboards

1. **Overview Dashboard**
   - Top violating water systems
   - Violation status breakdown
   - Geographic distribution of issues

2. **System Search**
   - Detailed system profiles
   - Violation timelines
   - Site visit history
   - Water quality scorecard

3. **Violations Analysis**
   - Category breakdowns
   - Health impact assessment
   - Most common violations

4. **Lead & Copper Monitoring**
   - Time series analysis
   - EPA threshold comparisons
   - High-risk system identification

5. **AI Assistant**
   - Natural language Q&A
   - System health analysis
   - Violation explanations

## 🛠️ Tech Stack

- **Backend**: Python, SQLite
- **Frontend**: Streamlit
- **Visualization**: Plotly
- **AI**: Anthropic Claude API
- **Data**: 10 CSV files from Georgia SDWIS

## 📦 Installation

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/speedtrials-2025.git
cd speedtrials-2025
```

2. Run the setup script:
```bash
./run.sh
```

This will:
- Create a virtual environment
- Install dependencies
- Set up the database
- Launch the app

### Manual Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up database:
```bash
python setup_database.py
```

4. Configure AI (optional):
   - Get API key from [Anthropic](https://console.anthropic.com/)
   - Edit `.env` file: `ANTHROPIC_API_KEY=your_key_here`

5. Run the app:
```bash
streamlit run app.py
```

## 🌐 Hosting with ngrok

For demo/judging purposes:

```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Configure (one-time)
ngrok config add-authtoken YOUR_TOKEN

# Share your app
ngrok http 8501
```

## 📊 Data Overview

The app processes 238,726 rows of water quality data including:
- 5,633 water systems
- 151,377 violations
- 14,855 health-based violations
- 1,234 currently unaddressed violations

## 🎯 User Types Supported

1. **Public**: Simple search, clear violation explanations, health alerts
2. **Operators**: Compliance tracking, violation management, site visit history
3. **Regulators**: Geographic analysis, priority queues, field-ready mobile interface

## 🔑 Key Files

- `app.py` - Main Streamlit application
- `setup_database.py` - Database initialization
- `utils/database.py` - Database queries and operations
- `utils/visualizations.py` - Chart generation
- `utils/claude_insights.py` - AI integration
- `.env` - Configuration (API keys)

## 💡 Usage Tips

1. **Search**: Try "Atlanta", "GA0670000", or any city name
2. **Scores**: 90+ (Good), 70-89 (Fair), <70 (Poor)
3. **AI Chat**: Ask questions like "What is a Stage 2 DBP violation?"
4. **Filters**: Click on charts to drill down into data

## 🏁 Competition Notes

Built for the Codegen Speed Trials 2025 to replace Georgia's outdated water quality viewer. Focuses on:
- Modern, intuitive interface
- Mobile-responsive design
- AI-powered insights
- Real-time data exploration

## 📝 License

Created for educational/competition purposes using public data from Georgia EPD.