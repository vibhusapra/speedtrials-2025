"""
Meme Generator using Black Forest Labs Flux Kontext API
Creates water quality awareness memes with custom captions
"""

import os
import base64
import requests
import time
from typing import Optional, Tuple
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class MemeGenerator:
    """Generate memes using Flux Kontext API"""
    
    def __init__(self):
        self.api_key = os.getenv('BFL_API_KEY')
        self.base_url = "https://api.bfl.ai"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            print("BFL API key not found. Meme generation will use fallback method.")
    
    def image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def base64_to_image(self, base64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        image_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(image_data))
    
    def generate_meme(self, template_path: str, caption: str, position: str = "top") -> Optional[bytes]:
        """
        Generate a meme using Flux Kontext API
        
        Args:
            template_path: Path to meme template image
            caption: Text to add to the meme
            position: Where to place text (top, bottom, both)
        
        Returns:
            Generated meme as bytes or None if failed
        """
        if not self.enabled:
            return self.fallback_generate(template_path, caption, position)
        
        try:
            # Convert image to base64
            image_base64 = self.image_to_base64(template_path)
            
            # Prepare the prompt based on position
            if position == "both" and "|" in caption:
                top_text, bottom_text = caption.split("|", 1)
                prompt = f"Add meme text '{top_text.strip()}' at the top and '{bottom_text.strip()}' at the bottom in white Impact font with black outline"
            elif position == "bottom":
                prompt = f"Add meme text '{caption}' at the bottom in white Impact font with black outline"
            else:  # top
                prompt = f"Add meme text '{caption}' at the top in white Impact font with black outline"
            
            # Create the request
            headers = {
                "Content-Type": "application/json",
                "x-key": self.api_key
            }
            
            data = {
                "prompt": prompt,
                "input_image": image_base64,
                "aspect_ratio": "1:1",
                "safety_tolerance": 2
            }
            
            # Send request to create task
            response = requests.post(
                f"{self.base_url}/v1/flux-kontext-pro",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                return self.fallback_generate(template_path, caption, position)
            
            task_id = response.json().get("id")
            if not task_id:
                print("No task ID received from API")
                return self.fallback_generate(template_path, caption, position)
            
            # Poll for result
            result = self.poll_for_result(task_id)
            if result:
                # Get image URL from result
                if "result" in result and isinstance(result["result"], dict):
                    image_url = result["result"].get("sample", "")
                else:
                    image_url = result.get("sample", "")
                
                if image_url:
                    # Download the generated image
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        return img_response.content
                    else:
                        print(f"Failed to download image: {img_response.status_code}")
                        return self.fallback_generate(template_path, caption, position)
                else:
                    print("No image URL found in API response")
                    return self.fallback_generate(template_path, caption, position)
            
            return self.fallback_generate(template_path, caption, position)
            
        except Exception as e:
            print(f"Error generating meme: {e}")
            return self.fallback_generate(template_path, caption, position)
    
    def poll_for_result(self, task_id: str, max_attempts: int = 30) -> Optional[dict]:
        """Poll for API result"""
        headers = {
            "x-key": self.api_key
        }
        
        for _ in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/v1/get_result",
                    headers=headers,
                    params={"id": task_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "Ready":
                        return result
                    elif status == "Failed":
                        print(f"Task failed: {result.get('error', 'Unknown error')}")
                        return None
                    
                time.sleep(2)  # Wait before next poll
                
            except Exception as e:
                print(f"Error polling result: {e}")
                return None
        
        print("Polling timeout")
        return None
    
    def fallback_generate(self, template_path: str, caption: str, position: str = "top") -> bytes:
        """
        Fallback method using PIL for text overlay
        """
        try:
            from PIL import ImageDraw, ImageFont
            
            # Open the template
            img = Image.open(template_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            
            # Try to use Impact font, fallback to default
            try:
                font_size = int(img.height * 0.1)  # 10% of image height
                font = ImageFont.truetype("Impact.ttf", font_size)
            except:
                # Use default font
                font = ImageFont.load_default()
            
            # Calculate text position
            img_width, img_height = img.size
            
            if position == "both" and "|" in caption:
                top_text, bottom_text = caption.split("|", 1)
                texts = [(top_text.strip(), "top"), (bottom_text.strip(), "bottom")]
            else:
                texts = [(caption, position)]
            
            for text, pos in texts:
                # Get text size
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Calculate position
                x = (img_width - text_width) // 2
                if pos == "top":
                    y = int(img_height * 0.05)
                else:  # bottom
                    y = img_height - text_height - int(img_height * 0.05)
                
                # Draw text with outline effect
                outline_width = 2
                for adj_x in range(-outline_width, outline_width + 1):
                    for adj_y in range(-outline_width, outline_width + 1):
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill="black")
                
                # Draw main text
                draw.text((x, y), text, font=font, fill="white")
            
            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Fallback generation failed: {e}")
            # Return original image if all fails
            with open(template_path, "rb") as f:
                return f.read()
    
    def get_suggested_templates(self, topic: str) -> list:
        """Get suggested meme templates for a given topic"""
        suggestions = {
            "violations": ["drake", "expanding_brain", "astronaut", "two_buttons"],
            "safety": ["change_my_mind", "woman_yelling_at_cat", "surprised_pikachu"],
            "awareness": ["distracted_boyfriend", "is_this_a_pigeon", "one_does_not_simply"],
            "humor": ["mock_spongebob", "arthur_fist", "hide_the_pain_harold"],
            "urgent": ["ackbar", "panik-kalm-panik", "american_chopper_argument"]
        }
        
        return suggestions.get(topic, ["drake", "distracted_boyfriend", "two_buttons"])