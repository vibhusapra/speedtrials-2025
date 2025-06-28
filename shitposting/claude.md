# Meme Generation Guide for Claude

## Overview
This guide helps future Claude instances understand and maintain the Georgia Water Quality meme generation system.

## Purpose
The meme generator serves to:
1. Spread awareness about water quality issues in Georgia
2. Make complex water data accessible through humor
3. Engage younger audiences who might ignore traditional warnings
4. Create shareable content that drives traffic to the dashboard

## System Architecture

### Components
1. **Meme Templates** (`/shitposting/memes/`)
   - 200+ meme template images
   - Each template has specific format requirements
   - Templates chosen for water quality messaging potential

2. **Caption Generator** (`utils/meme_captions.py`)
   - Uses GPT-4.1 to create contextual captions
   - Adapts to current water quality data
   - Multiple tone options: funny, educational, urgent, sarcastic

3. **Image Generator** (`utils/meme_generator.py`)
   - Integrates with Black Forest Labs Flux Kontext API
   - Fallback to PIL for local text overlay
   - Handles various meme text positions

4. **UI Integration** (Meme Generator tab in `app.py`)
   - Template gallery with preview
   - AI suggestion interface
   - One-click generation
   - Download functionality

## Meme Strategy

### Effective Water Quality Memes
1. **Relatable Situations**
   - "When the water tastes funny but you're too lazy to check"
   - "Me pretending the water is fine | The 5 active violations"

2. **Educational Through Humor**
   - Use expanding brain for violation severity levels
   - Drake format for good vs bad water practices

3. **Call to Action**
   - "Change my mind" format with water facts
   - Two buttons showing difficult choices

### Caption Guidelines
- Keep text concise (meme attention span is 2 seconds)
- Use specific Georgia references when possible
- Balance humor with actual information
- Include actionable advice subtly

## API Integration

### Black Forest Labs (Flux Kontext)
- Endpoint: `https://api.bfl.ai/flux-kontext-pro`
- Adds text to images with natural integration
- Requires base64 encoded images
- 10-minute URL expiration for results

### Key Parameters
```python
{
    "prompt": "Add meme text '{caption}' in white Impact font with black outline",
    "input_image": base64_string,
    "aspect_ratio": "1:1",
    "safety_tolerance": 2
}
```

## Common Issues & Solutions

### Problem: API Rate Limits
- Solution: Implement caching for popular memes
- Fallback to local PIL text overlay

### Problem: Inappropriate Content
- Solution: Pre-filter captions through OpenAI moderation
- Maintain whitelist of safe topics

### Problem: Text Readability
- Solution: Always use white text with black outline
- Adjust font size based on text length

## Maintenance Tasks

### Weekly
- Review generated memes for quality
- Update caption prompts based on current events
- Check API usage and costs

### Monthly
- Add new meme templates as they trend
- Analyze engagement metrics
- Update water quality context data

## Example Workflows

### Generate Violation Awareness Meme
1. User selects "Drake" template
2. AI suggests: "Drinking water without checking | Checking our dashboard first"
3. Flux Kontext adds text with proper positioning
4. User downloads and shares

### Create Urgent Warning Meme
1. Select "Panik-Kalm-Panik" template
2. Context: Active boil water advisory
3. AI generates: "Water looks clear | It's been boiled | You forgot to boil it"
4. Enhanced with warning colors

## Best Practices

1. **Test locally first** - Use fallback generator during development
2. **Monitor API costs** - Flux Kontext charges per generation
3. **Keep captions fresh** - Update based on current water issues
4. **Respect the memes** - Don't force serious messages into incompatible formats
5. **Track engagement** - See which memes get shared most

## Future Enhancements

1. **Auto-post to social media** - Schedule memes based on water quality changes
2. **User submissions** - Let community create water memes
3. **Meme contests** - Engagement campaigns
4. **Regional targeting** - City-specific meme campaigns
5. **Animated memes** - GIF support for more impact

Remember: The goal is awareness through humor. If a meme makes someone check their water quality, it worked!