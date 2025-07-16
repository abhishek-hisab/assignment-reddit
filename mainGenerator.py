import json
import google.generativeai as genai
from datetime import datetime
import re
from typing import Dict, List, Any
import os

class RedditPersonaGenerator:
    def __init__(self, api_key: str):
        """Initialize the persona generator with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_reddit_data(self, reddit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Reddit data to extract key insights"""
        
        # Extract basic info
        username = reddit_data.get('username', '')
        posts = reddit_data.get('posts', [])
        comments = reddit_data.get('comments', [])
        
        # Analyze posting patterns
        subreddits = set()
        topics = []
        engagement_style = []
        
        # Process posts
        for post in posts:
            subreddits.add(post.get('subreddit', ''))
            topics.append(post.get('title', ''))
            topics.append(post.get('content', ''))
        
        # Process comments
        for comment in comments:
            engagement_style.append(comment.get('body', ''))
        
        return {
            'username': username,
            'total_posts': len(posts),
            'total_comments': len(comments),
            'subreddits': list(subreddits),
            'content_sample': topics + engagement_style,
            'posts_data': posts,
            'comments_data': comments
        }
    
    def generate_persona_prompt(self, analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive prompt for persona creation"""
        
        # Combine all text content for analysis
        all_content = []
        
        # Add post titles and content
        for post in analysis['posts_data']:
            all_content.append(f"POST: {post.get('title', '')} - {post.get('content', '')}")
        
        # Add comments
        for comment in analysis['comments_data']:
            all_content.append(f"COMMENT: {comment.get('body', '')}")
        
        content_text = "\n".join(all_content[:20])  # Limit to avoid token limits
        
        prompt = f"""
        Based on the following Reddit user data, create a detailed user persona in the style of a professional UX/Marketing persona document. 

        USERNAME: {analysis['username']}
        TOTAL POSTS: {analysis['total_posts']}
        TOTAL COMMENTS: {analysis['total_comments']}
        ACTIVE SUBREDDITS: {', '.join(analysis['subreddits'])}

        CONTENT ANALYSIS:
        {content_text}

        Create a comprehensive persona that includes:

        1. **PERSONA NAME & TAGLINE**: Create a realistic name and one-line description
        
        2. **DEMOGRAPHICS**: 
           - Age range
           - Location (inferred from content)
           - Occupation (based on expertise shown)
           - Education level
        
        3. **PSYCHOGRAPHICS**:
           - Personality traits
           - Values and motivations
           - Lifestyle preferences
           - Communication style
        
        4. **DIGITAL BEHAVIOR**:
           - Social media usage patterns
           - Content consumption habits
           - Online community participation
           - Preferred platforms and tools
        
        5. **PROFESSIONAL PROFILE**:
           - Career focus and expertise
           - Industry knowledge level
           - Professional goals
           - Skills and competencies
        
        6. **PAIN POINTS & FRUSTRATIONS**:
           - Common challenges they face
           - Industry-specific frustrations
           - Information gaps
        
        7. **GOALS & MOTIVATIONS**:
           - Short-term objectives
           - Long-term aspirations
           - What drives their decisions
        
        8. **CONTENT PREFERENCES**:
           - Types of content they engage with
           - Preferred information sources
           - Learning preferences
        
        9. **QUOTE**: A representative quote that captures their voice and perspective
        
        10. **KEY INSIGHTS**: 3-5 bullet points summarizing the most important things to know about this persona
        
        Format the response as a professional persona document with clear sections and actionable insights. Base all conclusions on evidence from their actual Reddit activity and communication style.
        """
        
        return prompt
    
    def generate_persona(self, reddit_data: Dict[str, Any]) -> str:
        """Generate a complete persona from Reddit data"""
        
        try:
            # Analyze the data
            analysis = self.analyze_reddit_data(reddit_data)
            
            # Generate prompt
            prompt = self.generate_persona_prompt(analysis)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Error generating persona: {str(e)}"
    
    def save_persona(self, persona_text: str, filename: str = None):
        """Save persona to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_persona_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(persona_text)
        
        print(f"Persona saved to {filename}")

# Example usage function
def create_persona_from_json(json_file_path: str, api_key: str):
    """Main function to create persona from JSON file"""
    
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        reddit_data = json.load(f)
    
    # Initialize generator
    generator = RedditPersonaGenerator(api_key)
    
    # Generate persona
    print("Generating persona...")
    persona = generator.generate_persona(reddit_data)
    
    # Save persona
    generator.save_persona(persona)
    
    return persona

# Alternative: Direct usage with your existing data
def create_persona_from_data(reddit_data: Dict[str, Any], api_key: str):
    """Create persona directly from dictionary data"""
    
    # Initialize generator
    generator = RedditPersonaGenerator(api_key)
    
    # Generate persona
    print("Generating persona...")
    persona = generator.generate_persona(reddit_data)
    
    # Save persona
    generator.save_persona(persona)
    
    return persona

# Example usage with your provided data
if __name__ == "__main__":
    # Your JSON data (the one you provided)
    sample_data = {
        "username": "Seshat_the_Scribe",
        "profile_url": "https://www.reddit.com/user/Seshat_the_Scribe/",
        "scraped_at": "2025-07-15T23:15:09.544178",
        "posts": [
            {
                "index": 0,
                "title": "1497 Features Lab (free until May 5)",
                "url": "https://www.reddit.com/r/Screenwriting/comments/1cge22d/1497_features_lab_free_until_may_5/",
                "subreddit": "Screenwriting",
                "timestamp": "1 yr. ago",
                "content": "https://deadline.com/2024/04/zoya-akhtar-fawzia-mirza-roshan-sethi-fourth-1497-features-lab-mentors-1235898699/ Zoya Akhtar (The Archies), Fawzia Mirza (Queen of My Dreams) and Roshan Sethi (A Nice Indian Boy) are set to join the 1497 Features Lab as mentors."
            }
            # ... (rest of your data)
        ],
        "comments": [
            # ... (your comments data)
        ],
        "total_posts": 7,
        "total_comments": 7
    }
    
    # Set your Gemini API key
    API_KEY = "YOUR_GEMINI_API_KEY_HERE"
    
    # Create persona
    try:
        persona = create_persona_from_data(sample_data, API_KEY)
        print("\n" + "="*50)
        print("GENERATED PERSONA:")
        print("="*50)
        print(persona)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to:")
        print("1. Install required packages: pip install google-generativeai")
        print("2. Set your Gemini API key")