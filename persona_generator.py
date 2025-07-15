import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class PersonaGenerator:
    def __init__(self, 
                 model: str = "gemini-1.5-flash",
                 fallback_models: List[str] = ["gemini-1.5-flash"],
                 max_retries: int = 3):
        """
        Initialize the PersonaGenerator with Google's Gemini.
        
        Args:
            model: Primary model to use
            fallback_models: List of alternative models to try if primary fails
            max_retries: Maximum number of retries before failing
        """
        # Get API key from Streamlit secrets
        google_api_key = st.secrets.api.GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in secrets")
            
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        self.fallback_models = fallback_models
        self.max_retries = max_retries
    
    def generate_persona(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a persona from Reddit user data with retry logic and fallback models.
        
        Args:
            user_data: Dictionary containing user profile, comments, and posts
            
        Returns:
            Dictionary containing the generated persona text and metadata
        """
        try:
            # Prepare the prompt
            prompt = self._create_prompt(user_data)
            
            # Generate response from Gemini
            response = self._generate_with_fallback(prompt)
            
            # Get the generated persona text
            persona_text = response.text.strip()
            
            # Add metadata
            metadata = {
                'model_used': self.model_name,
                'generated_at': self._get_current_timestamp(),
                'comments_analyzed': len(user_data.get('comments', [])),
                'posts_analyzed': len(user_data.get('posts', []))
            }
            
            # Format the final output with metadata
            final_output = f"""REDDIT USER PERSONA
==================================================

{persona_text}

--------------------------------------------------

ANALYSIS METADATA

Generated using {metadata['model_used']}

Generated at: {metadata['generated_at']}

Comments analyzed: {metadata['comments_analyzed']}

Posts analyzed: {metadata['posts_analyzed']}
"""
            
            return {
                'persona_text': final_output,
                'metadata': metadata
            }
            
        except Exception as e:
            raise Exception(f"Error generating persona: {str(e)}")

    def _generate_with_fallback(self, prompt: str) -> Any:
        """Try generating content with fallback models if primary fails."""
        attempts = 0
        current_model = self.model
        rate_limit_cooldown = 60  # 1 minute cooldown for rate limits
        
        while attempts < self.max_retries:
            try:
                print(f"\nAttempt {attempts + 1}/{self.max_retries} using model: {self.model_name}")
                
                # Generate response with current model
                response = current_model.generate_content([
                    "You are a professional user researcher. Analyze the provided Reddit user data and create a detailed user persona. Be specific and include direct references to the user's comments and posts to support your analysis.",
                    prompt
                ])
                
                return response
                
            except Exception as e:
                attempts += 1
                error_message = str(e)
                print(f"Error: {error_message}")
                
                # Handle rate limit specifically
                if "429" in error_message or "quota" in error_message.lower():
                    raise Exception(
                        "Rate limit exceeded. You've reached the free tier limit of 50 requests per day. "
                        "Please try again tomorrow or consider upgrading to a paid plan at: "
                        "https://ai.google.dev/gemini-api/docs/rate-limits"
                    )
                
                if attempts >= self.max_retries:
                    raise Exception(f"Failed after {self.max_retries} attempts. Last error: {error_message}")
                
                # Try next fallback model if available
                if attempts <= len(self.fallback_models):
                    next_model = self.fallback_models[attempts - 1]
                    print(f"Switching to fallback model: {next_model}")
                    current_model = genai.GenerativeModel(next_model)
                    self.model_name = next_model
                
                # Add exponential backoff
                wait_time = min(2 ** attempts, 30)  # Cap at 30 seconds
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    def _create_prompt(self, user_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for persona generation with citations."""
        from scraper import RedditScraper
        from datetime import datetime
        
        # Format the user activity data
        activity_summary = RedditScraper().format_activity_for_prompt(user_data)
        
        # Get account age if available
        account_age = ""
        if 'profile' in user_data and 'created_utc' in user_data['profile']:
            created = datetime.fromtimestamp(user_data['profile']['created_utc'])
            account_age = f" (Account created: {created.strftime('%Y-%m-%d')})"
            
        username = user_data.get('profile', {}).get('username', 'Unknown')
        
        prompt = f"""
        Analyze the provided Reddit user's activity and generate a comprehensive persona. 
        For EVERY characteristic or claim, include a direct citation from their posts/comments.
        
        USER: {username}{account_age}
        Comments analyzed: {len(user_data.get('comments', []))}
        Posts analyzed: {len(user_data.get('posts', []))}
        
        USER ACTIVITY DATA:
        {activity_summary}
        
        PERSONA FORMAT (FOLLOW EXACTLY):
        
        🧑‍💻 Occupation: 
        - [Detailed description with evidence]
        - "[Direct quote]" – r/[subreddit] [DD/MM/YYYY]
        
        📍 Location: 
        - [Location details with evidence]
        - "[Direct quote]" – r/[subreddit] [DD/MM/YYYY]
        
        🧠 PERSONALITY:
        - [Trait 1] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        - [Trait 2] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        
        💡 MOTIVATIONS:
        - [Motivation 1] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        - [Motivation 2] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        
        🔄 BEHAVIORS & HABITS:
        - [Behavior 1] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        - [Behavior 2] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        
        😤 FRUSTRATIONS:
        - [Frustration 1] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        - [Frustration 2] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        
        🎯 GOALS & NEEDS:
        - [Goal 1] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        - [Goal 2] - [Description]
          - "[Supporting quote]" – r/[subreddit] [DD/MM/YYYY]
        
        📝 EVIDENCE:
        - "[Most representative quote 1]" – r/[subreddit] [DD/MM/YYYY]
        - "[Most representative quote 2]" – r/[subreddit] [DD/MM/YYYY]
        - "[Most representative quote 3]" – r/[subreddit] [DD/MM/YYYY]
        
        CRITICAL INSTRUCTIONS:
        1. FOR EVERY characteristic, include at least one direct quote with source
        2. Format citations as: "[quote]" – r/subreddit [DD/MM/YYYY]
        3. Include the date of each cited post/comment in DD/MM/YYYY format
        4. If a section has no evidence, omit it entirely
        5. Be specific and avoid generic statements
        6. Maintain a neutral, objective tone
        7. Focus on the most significant and well-supported insights
        8. For the EVIDENCE section, choose the 3 most representative quotes
        9. Include context when necessary to understand the quote
        10. Never make assumptions without clear evidence
        
        The user will be verifying the accuracy of your citations, so be precise!
        """
        
        return prompt
    
    def _parse_persona_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the raw text response into a structured persona dictionary.
        
        Args:
            response_text: The raw text response from the AI model
            
        Returns:
            Dictionary containing the persona text and metadata
        """
        try:
            # Clean up the response text
            response_text = response_text.strip()
            
            # If the response is empty, return an error
            if not response_text:
                raise ValueError("Empty response from AI model")
                
            # Return the response as-is in the 'persona_text' field
            return {
                'persona_text': response_text,
                'metadata': {
                    'format': 'text',
                    'parsed_at': self._get_current_timestamp()
                }
            }
            
        except Exception as e:
            # If any error occurs, return the raw text with an error note
            return {
                'persona_text': response_text,
                'metadata': {
                    'error': str(e),
                    'format': 'raw_text',
                    'parsed_at': self._get_current_timestamp()
                },
                'error': f"Error parsing response: {str(e)}"
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
