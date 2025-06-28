from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class AIInsights:
    def __init__(self):
        try:
            # Initialize OpenAI client - it automatically uses OPENAI_API_KEY from environment
            self.client = OpenAI()
            self.enabled = True
            print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None
            self.enabled = False
    
    def explain_violation(self, violation_data: Dict[str, Any]) -> str:
        """Get plain English explanation of a violation"""
        if not self.enabled:
            return "OpenAI API not configured. Add your OPENAI_API_KEY to .env file for AI insights."
        
        try:
            violation_code = violation_data.get('VIOLATION_CODE', 'Unknown')
            violation_desc = violation_data.get('VIOLATION_DESC', 'No description available')
            is_health_based = violation_data.get('IS_HEALTH_BASED_IND', 'N') == 'Y'
            contaminant = violation_data.get('CONTAMINANT_CODE', 'N/A')
            
            prompt = f"""
            Explain this water quality violation in simple terms that a resident would understand:
            
            Violation Code: {violation_code}
            Description: {violation_desc}
            Health-Based: {'Yes' if is_health_based else 'No'}
            Contaminant: {contaminant}
            
            Provide:
            1. What this violation means in plain English
            2. Potential health impacts (if any)
            3. What residents should do
            
            Keep the response concise and avoid technical jargon.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a helpful assistant explaining water quality issues to residents in simple, clear language."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI insight: {str(e)}"
    
    def analyze_system_health(self, system_data: Dict[str, Any]) -> str:
        """Analyze overall health of a water system"""
        if not self.enabled:
            return "OpenAI API not configured. Add your OPENAI_API_KEY to .env file for AI insights."
        
        try:
            system = system_data.get('system', {})
            violations = system_data.get('violations', [])
            site_visits = system_data.get('site_visits', [])
            
            # Count violation types
            health_violations = sum(1 for v in violations if v.get('IS_HEALTH_BASED_IND') == 'Y')
            active_violations = sum(1 for v in violations if v.get('VIOLATION_STATUS') == 'Unaddressed')
            
            prompt = f"""
            Analyze the health of this water system and provide a brief assessment:
            
            System: {system.get('PWS_NAME', 'Unknown')}
            Population Served: {system.get('POPULATION_SERVED_COUNT', 0):,}
            Type: {system.get('PWS_TYPE_CODE', 'Unknown')}
            
            Violations:
            - Total: {len(violations)}
            - Active/Unaddressed: {active_violations}
            - Health-Based: {health_violations}
            
            Recent Site Visits: {len(site_visits)}
            
            Provide:
            1. Overall water quality assessment (Good/Fair/Poor)
            2. Main concerns (if any)
            3. Recommendation for residents
            
            Be direct and helpful. Use simple language.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a water quality expert providing clear assessments for public water systems."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI insight: {str(e)}"
    
    def interpret_lead_copper_results(self, test_results: list) -> str:
        """Interpret lead and copper test results"""
        if not self.enabled:
            return "OpenAI API not configured. Add your OPENAI_API_KEY to .env file for AI insights."
        
        try:
            # EPA action levels
            lead_action_level = 15  # ppb
            copper_action_level = 1300  # ppb
            
            lead_results = [r for r in test_results if r.get('CONTAMINANT_CODE') == '5000']
            copper_results = [r for r in test_results if r.get('CONTAMINANT_CODE') == '5001']
            
            prompt = f"""
            Interpret these lead and copper test results for water quality:
            
            Lead Tests: {len(lead_results)} samples
            Copper Tests: {len(copper_results)} samples
            
            EPA Action Levels:
            - Lead: {lead_action_level} ppb
            - Copper: {copper_action_level} ppb
            
            Recent results show:
            {chr(10).join([f"- {r.get('CONTAMINANT_NAME', 'Unknown')}: {r.get('SAMPLE_MEASURE', 0)} {r.get('UNIT_OF_MEASURE', 'ppb')}" for r in test_results[:5]])}
            
            Provide:
            1. Are the levels safe?
            2. What do these numbers mean for residents?
            3. Any recommended actions?
            
            Use plain language that non-experts can understand.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a water quality expert explaining lead and copper test results to residents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI insight: {str(e)}"
    
    def chat_query(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Answer general questions about water quality"""
        if not self.enabled:
            return "OpenAI API not configured. Add your OPENAI_API_KEY to .env file for AI insights."
        
        try:
            context_str = ""
            if context:
                context_str = f"\nContext: {context}"
            
            messages = [
                {"role": "developer", "content": "You are a helpful assistant for Georgia residents concerned about their drinking water quality. Provide accurate, helpful responses in plain language."},
                {"role": "user", "content": f"{question}{context_str}"}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI response: {str(e)}"
    
    def get_city_insights(self, city_name: str, city_context: str, question: str, violations_data: Any = None) -> str:
        """Get AI insights about water quality in a specific city"""
        if not self.enabled:
            return "OpenAI API not configured. Add your OPENAI_API_KEY to .env file for AI insights."
        
        try:
            # Build detailed context
            violation_details = ""
            if violations_data is not None and not violations_data.empty:
                # Get top violations
                violation_summary = violations_data.groupby('VIOLATION_DESC').size().sort_values(ascending=False).head(5)
                violation_details = f"\n\nTop violations in {city_name}:\n"
                for violation, count in violation_summary.items():
                    violation_details += f"- {violation}: {count} systems\n"
            
            prompt = f"""
            You are a water quality expert providing insights about drinking water in {city_name}, Georgia.
            
            City Data:
            {city_context}
            {violation_details}
            
            User Question: {question}
            
            Provide a helpful, accurate response that:
            1. Directly answers the question
            2. References specific data about {city_name}
            3. Offers practical advice for residents
            4. Uses plain language
            
            Keep the response focused and informative.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a water quality expert assistant helping Georgia residents understand their local drinking water quality. Use the provided data to give specific, helpful insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI insight: {str(e)}"