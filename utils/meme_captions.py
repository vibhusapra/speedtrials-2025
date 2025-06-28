"""
AI-powered meme caption generator for water quality awareness
Uses GPT-4.1 to create contextual, engaging captions
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class MemeCaptionGenerator:
    """Generate water quality meme captions using AI"""
    
    def __init__(self):
        try:
            self.client = OpenAI()
            self.enabled = True
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None
            self.enabled = False
    
    def generate_caption(
        self, 
        template_name: str,
        template_format: str,
        tone: str = "funny",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a meme caption based on template and context
        
        Args:
            template_name: Name of the meme template (e.g., "drake", "distracted_boyfriend")
            template_format: Format description (e.g., "Reject X | Prefer Y")
            tone: Caption tone - funny, educational, sarcastic, urgent
            context: Optional water quality data context
        
        Returns:
            Generated caption text
        """
        if not self.enabled:
            return self.get_fallback_caption(template_name)
        
        try:
            # Build context information
            context_info = ""
            if context:
                if 'violations' in context:
                    context_info += f"\nCurrent violations: {context['violations']}"
                if 'city' in context:
                    context_info += f"\nCity focus: {context['city']}"
                if 'issue' in context:
                    context_info += f"\nMain issue: {context['issue']}"
            
            # Create prompt
            prompt = f"""
            Generate a meme caption for water quality awareness in Georgia.
            
            Meme template: {template_name}
            Format: {template_format}
            Tone: {tone}
            {context_info}
            
            Requirements:
            1. Make it relevant to Georgia water quality issues
            2. Keep it concise and punchy (meme-appropriate length)
            3. Use the specified format structure
            4. Make it shareable and engaging
            5. Include specific water issues when possible (lead, violations, boil advisories)
            
            Examples of good water quality memes:
            - Drake format: "Ignoring boil water advisory | Buying expensive bottled water anyway"
            - Distracted boyfriend: "Me | Clean tap water | That sketchy well water"
            - Two buttons: "Test your water" | "Just hope for the best"
            
            Generate only the caption text, using | to separate parts if needed.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a creative meme caption writer focusing on water quality awareness. Make captions that are funny but informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating caption: {e}")
            return self.get_fallback_caption(template_name)
    
    def generate_batch_captions(
        self,
        template_name: str,
        template_format: str,
        count: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate multiple caption options"""
        if not self.enabled:
            return [self.get_fallback_caption(template_name) for _ in range(count)]
        
        try:
            prompt = f"""
            Generate {count} different meme captions for water quality awareness in Georgia.
            
            Meme template: {template_name}
            Format: {template_format}
            
            Make each caption:
            1. Different in approach (funny, shocking, educational)
            2. Focus on different water issues (lead, bacteria, violations)
            3. Appeal to different audiences
            
            Return each caption on a new line.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "developer", "content": "You are a creative meme caption writer. Generate diverse captions for water quality awareness."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.9
            )
            
            captions = response.choices[0].message.content.strip().split('\n')
            return [cap.strip() for cap in captions if cap.strip()][:count]
            
        except Exception as e:
            print(f"Error generating batch captions: {e}")
            return [self.get_fallback_caption(template_name) for _ in range(count)]
    
    def get_fallback_caption(self, template_name: str) -> str:
        """Fallback captions when AI is not available"""
        fallback_captions = {
            "drake": "Trusting mystery tap water | Getting your water tested",
            "distracted_boyfriend": "Me | Filtered water | That sus tap water",
            "two_buttons": "Check water quality | Live dangerously",
            "expanding_brain": "Drinking tap water | Boiling water | Testing water | Reading water quality reports",
            "woman_yelling_at_cat": "YOUR WATER HAS VIOLATIONS | Me just trying to stay hydrated",
            "surprised_pikachu": "Ignores water warnings | Gets sick | *surprised pikachu*",
            "change_my_mind": "Georgia tap water is fine | Change my mind",
            "is_this_a_pigeon": "Is this safe to drink?",
            "one_does_not_simply": "One does not simply | Trust water without testing",
            "mock_spongebob": "ThE wAtEr Is PeRfEcTlY sAfE"
        }
        
        return fallback_captions.get(template_name, "Check your water quality | Visit our dashboard")
    
    def get_template_formats(self) -> Dict[str, str]:
        """Get format descriptions for each meme template"""
        return {
            "drake": "Reject [bad thing] | Prefer [good thing]",
            "distracted_boyfriend": "[Person] | [New interest] | [Ignored thing]",
            "two_buttons": "[Option 1] | [Option 2]",
            "expanding_brain": "[Basic] | [Smart] | [Genius] | [Galaxy brain]",
            "woman_yelling_at_cat": "[Angry statement] | [Confused response]",
            "surprised_pikachu": "[Action] | [Obvious consequence] | *surprised*",
            "change_my_mind": "[Controversial statement] | Change my mind",
            "is_this_a_pigeon": "[Misidentification] | Is this [wrong thing]?",
            "arthur_fist": "When [frustrating situation]",
            "one_does_not_simply": "One does not simply | [Difficult task]",
            "mock_spongebob": "[Mocking statement in alternating caps]",
            "panik-kalm-panik": "[Bad news] | [Relief] | [Worse news]",
            "american_chopper_argument": "[Statement] | [Counter] | [Escalation] | [More escalation] | [Resolution]",
            "hide_the_pain_harold": "[Painful situation] | *Smiles through pain*",
            "roll_safe": "[Bad logic that sounds smart]"
        }
    
    def get_water_topics(self) -> List[Dict[str, str]]:
        """Get water quality topics for meme generation"""
        return [
            {"id": "lead", "name": "Lead Contamination", "icon": "🚰"},
            {"id": "violations", "name": "Water Violations", "icon": "⚠️"},
            {"id": "boil", "name": "Boil Water Advisories", "icon": "🔥"},
            {"id": "testing", "name": "Water Testing", "icon": "🧪"},
            {"id": "safety", "name": "General Safety", "icon": "🛡️"},
            {"id": "awareness", "name": "Public Awareness", "icon": "📢"},
            {"id": "officials", "name": "Water Officials", "icon": "🏛️"},
            {"id": "bills", "name": "Water Bills vs Quality", "icon": "💰"}
        ]