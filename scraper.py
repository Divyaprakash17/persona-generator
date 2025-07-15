import os
import time
import praw
from dotenv import load_dotenv
from typing import Dict, List, Any
from tqdm import tqdm
from datetime import datetime

class RedditScraper:
    def __init__(self):
        """Initialize the RedditScraper with environment variables and rate limiting."""
        load_dotenv()
        
        # Get Reddit API credentials
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT')
        
        if not all([self.client_id, self.client_secret, self.user_agent]):
            raise ValueError("Missing required Reddit API credentials in environment variables")
        
        # Initialize PRAW Reddit instance with rate limiting
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
            # Add rate limiting settings
            requestor_kwargs={
                'session': None,  # Let PRAW handle the session
                'timeout': 30,    # 30 second timeout
            },
            # Enable read-only mode (we don't need write access)
            check_for_async=False,
            # Add retry settings
            retry_on_timeout=True,
            retry_on_server_error=3
        )
        
        # Add a small delay between requests
        import time
        self._last_request_time = 0
        self._min_request_interval = 2  # 2 seconds between requests
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        import time
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()
    
    def get_user_data(self, username: str, comment_limit: int = 100, post_limit: int = 50) -> Dict[str, Any]:
        """
        Fetch user data including profile, comments, and posts.
        
        Args:
            username: Reddit username (without u/)
            comment_limit: Maximum number of comments to fetch (default: 100)
            post_limit: Maximum number of posts to fetch (default: 50)
            
        Returns:
            Dictionary containing user data, comments, and posts
            
        Raises:
            Exception: If there's an error fetching user data
        """
        try:
            if not username:
                raise ValueError("Username cannot be empty")
                
            self._rate_limit()
            # Remove u/ if present in username and clean it
            username = str(username).replace('u/', '').replace('/u/', '').strip()
            
            if not username:
                raise ValueError("Invalid username format")
                
            # Get Redditor object with error handling
            try:
                redditor = self.reddit.redditor(username)
                # Test if user exists by checking if we can access any attribute
                _ = getattr(redditor, 'comment_karma', None)
                if _ is None:
                    # If we can't access attributes, the user might not exist or is private
                    raise Exception(f"Unable to access user 'u/{username}'. The profile may not exist or is private.")
            except Exception as e:
                error_msg = str(e).lower()
                if '404' in error_msg or 'not found' in error_msg:
                    raise Exception(f"User 'u/{username}' not found")
                elif '403' in error_msg or 'forbidden' in error_msg:
                    raise Exception("Access forbidden. The user's profile might be private or you may be rate limited.")
                elif '401' in error_msg:
                    raise Exception("Authentication failed. Please check your Reddit API credentials.")
                raise Exception(f"Error accessing user profile: {str(e)}")
            
            # Get user profile information with safe attribute access
            user_info = {
                'username': username,
                'created_utc': getattr(redditor, 'created_utc', getattr(redditor, 'created', 0)),
                'comment_karma': getattr(redditor, 'comment_karma', 0),
                'link_karma': getattr(redditor, 'link_karma', 0),
                'has_verified_email': getattr(redditor, 'has_verified_email', False),
                'is_gold': getattr(redditor, 'is_gold', False),
                'is_mod': getattr(redditor, 'is_mod', False),
                'is_employee': getattr(redditor, 'is_employee', False)
            }
            
            # Get user comments and posts
            comments = self._get_user_comments(redditor, comment_limit)
            posts = self._get_user_posts(redditor, post_limit)
            
            return {
                'profile': user_info,
                'comments': comments,
                'posts': posts,
                'metadata': {
                    'comments_analyzed': len(comments),
                    'posts_analyzed': len(posts),
                    'generated_at': datetime.utcnow().isoformat(),
                    'model_used': 'gemini-1.5-flash'
                }
            }
            
        except Exception as e:
            raise Exception(f"Error fetching user data: {str(e)}")
    
    def _get_user_comments(self, redditor, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch user comments with improved error handling and retries.
        
        Args:
            redditor: PRAW Redditor object
            limit: Maximum number of comments to fetch
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        attempts = 0
        max_attempts = 5  # Increased from 3 to 5
        
        while len(comments) < limit and attempts < max_attempts:
            try:
                # Get a fresh generator each attempt with increased limit
                fetch_limit = min(limit * 2, 100)  # Fetch more to account for filtering
                comment_gen = redditor.comments.new(limit=fetch_limit)
                
                for comment in tqdm(comment_gen, 
                                 desc=f"Fetching comments (attempt {attempts + 1}/{max_attempts})", 
                                 unit="comment",
                                 total=limit,
                                 leave=False):
                    try:
                        # Skip removed or deleted comments
                        if (not hasattr(comment, 'body') or 
                            not comment.body or 
                            comment.body in ['[removed]', '[deleted]']):
                            continue
                            
                        comments.append({
                            'id': getattr(comment, 'id', ''),
                            'body': comment.body,
                            'subreddit': getattr(comment.subreddit, 'display_name', 'unknown') if hasattr(comment, 'subreddit') else 'unknown',
                            'score': getattr(comment, 'score', 0),
                            'created_utc': getattr(comment, 'created_utc', 0),
                            'permalink': f"https://reddit.com{getattr(comment, 'permalink', '')}",
                            'is_submitter': getattr(comment, 'is_submitter', False)
                        })
                        
                        # Break if we've reached the limit
                        if len(comments) >= limit:
                            break
                            
                        # Add a small delay between requests
                        time.sleep(0.5)
                            
                    except Exception as e:
                        print(f"Warning: Error processing comment: {str(e)}")
                        continue
                        
                # If we got all requested comments, we're done
                if len(comments) >= limit or attempts >= max_attempts - 1:
                    break
                    
            except Exception as e:
                print(f"Warning: Error in comment fetch attempt {attempts + 1}: {str(e)}")
                
            attempts += 1
            if attempts < max_attempts:
                retry_delay = 5 * attempts  # Exponential backoff
                print(f"Retrying in {retry_delay} seconds... ({attempts}/{max_attempts-1})")
                time.sleep(retry_delay)
    
        print(f"Fetched {len(comments)}/{limit} comments")
        return comments[:limit]

    def _get_user_posts(self, redditor, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch user posts with improved error handling and retries.
        
        Args:
            redditor: PRAW Redditor object
            limit: Maximum number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        posts = []
        attempts = 0
        max_attempts = 5  # Increased from 3 to 5
        
        while len(posts) < limit and attempts < max_attempts:
            try:
                # Get a fresh generator each attempt with increased limit
                fetch_limit = min(limit * 2, 100)  # Fetch more to account for filtering
                post_gen = redditor.submissions.new(limit=fetch_limit)
                
                for submission in tqdm(post_gen, 
                                    desc=f"Fetching posts (attempt {attempts + 1}/{max_attempts})", 
                                    unit="post",
                                    total=limit,
                                    leave=False):
                    try:
                        # Skip removed or deleted posts
                        if (not hasattr(submission, 'title') or 
                            not submission.title or 
                            submission.title in ['[removed]', '[deleted]']):
                            continue
                            
                        posts.append({
                            'id': getattr(submission, 'id', ''),
                            'title': submission.title,
                            'selftext': getattr(submission, 'selftext', ''),
                            'subreddit': getattr(submission.subreddit, 'display_name', 'unknown') if hasattr(submission, 'subreddit') else 'unknown',
                            'score': getattr(submission, 'score', 0),
                            'num_comments': getattr(submission, 'num_comments', 0),
                            'created_utc': getattr(submission, 'created_utc', 0),
                            'permalink': f"https://reddit.com{getattr(submission, 'permalink', '')}",
                            'url': getattr(submission, 'url', '')
                        })
                        
                        # Break if we've reached the limit
                        if len(posts) >= limit:
                            break
                            
                        # Add a small delay between requests
                        time.sleep(0.5)
                            
                    except Exception as e:
                        print(f"Warning: Error processing post: {str(e)}")
                        continue
                        
                # If we got all requested posts, we're done
                if len(posts) >= limit or attempts >= max_attempts - 1:
                    break
                    
            except Exception as e:
                print(f"Warning: Error in post fetch attempt {attempts + 1}: {str(e)}")
                
            attempts += 1
            if attempts < max_attempts:
                retry_delay = 5 * attempts  # Exponential backoff
                print(f"Retrying in {retry_delay} seconds... ({attempts}/{max_attempts-1})")
                time.sleep(retry_delay)
        
        print(f"Fetched {len(posts)}/{limit} posts")
        return posts[:limit]

    def format_activity_for_prompt(self, user_data: Dict[str, Any]) -> str:
        """
        Format user activity data for the prompt with timestamps and proper formatting.
        
        Args:
            user_data: Dictionary containing user data from Reddit API
            
        Returns:
            Formatted string with user activity data
        """
        output = []
        
        # Add profile info if available
        if 'profile' in user_data:
            profile = user_data['profile']
            output.append(f"USER: u/{profile.get('username', 'unknown')}")
            if 'created_utc' in profile and profile['created_utc']:
                created = datetime.fromtimestamp(profile['created_utc'])
                output.append(f"Account created: {created.strftime('%d/%m/%Y')} ({self._get_relative_time(created)})")
            output.append(f"Karma: {profile.get('comment_karma', 0)} comment, {profile.get('link_karma', 0)} post")
            output.append("\n")
        
        # Add comments if available
        if 'comments' in user_data and user_data['comments']:
            output.append("=== RECENT COMMENTS ===\n")
            for i, comment in enumerate(user_data['comments'][:15], 1):  # Show more comments for better analysis
                body = comment.get('body', '').strip()
                if not body:
                    continue
                    
                subreddit = comment.get('subreddit', 'unknown')
                created_utc = comment.get('created_utc', 0)
                date_str = datetime.fromtimestamp(created_utc).strftime('%d/%m/%Y') if created_utc else 'Unknown date'
                
                # Format comment with metadata
                output.append(f"--- Comment in r/{subreddit} on {date_str} ---")
                output.append(f'"{self._truncate_text(body, 300)}"')  # Truncate long comments
                output.append("")
            
        # Add posts if available
        if 'posts' in user_data and user_data['posts']:
            output.append("\n=== RECENT POSTS ===\n")
            for i, post in enumerate(user_data['posts'][:10], 1):  # Show more posts for better analysis
                title = post.get('title', '').strip()
                body = post.get('selftext', '').strip()
                if not (title or body):
                    continue
                    
                subreddit = post.get('subreddit', 'unknown')
                created_utc = post.get('created_utc', 0)
                date_str = datetime.fromtimestamp(created_utc).strftime('%d/%m/%Y') if created_utc else 'Unknown date'
                
                # Format post with metadata
                output.append(f"--- Post in r/{subreddit} on {date_str} ---")
                output.append(f'Title: "{title}"')
                if body:
                    output.append(f'Content: "{self._truncate_text(body, 200)}..."')
                output.append("")
        
        return '\n'.join(output)
    
    def _truncate_text(self, text: str, max_length: int = 200) -> str:
        """Truncate text to a maximum length, adding ellipsis if needed."""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    def _get_relative_time(self, dt: datetime) -> str:
        """Get relative time from a datetime object."""
        now = datetime.now()
        diff = now - dt
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days ago"
        elif hours > 0:
            return f"{hours} hours ago"
        elif minutes > 0:
            return f"{minutes} minutes ago"
        else:
            return f"{seconds} seconds ago"
