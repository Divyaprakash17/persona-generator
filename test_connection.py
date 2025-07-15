import os
import praw
from dotenv import load_dotenv

def test_reddit_connection():
    # Load environment variables
    load_dotenv()
    
    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT')
    )
    
    try:
        # Test connection by fetching a public subreddit
        subreddit = reddit.subreddit('all')
        print(f"Successfully connected to Reddit API!")
        print(f"Testing subreddit: r/{subreddit.display_name}")
        print(f"Subscribers: {subreddit.subscribers:,}")
        
        # Test fetching a user
        user = reddit.redditor('spez')
        print(f"\nTesting user fetch: u/{user.name}")
        print(f"Comment Karma: {user.comment_karma:,}")
        print(f"Link Karma: {user.link_karma:,}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting Tips:")
        print("1. Verify your API credentials are correct")
        print("2. Check that your Reddit account email is verified")
        print("3. Make sure your user agent follows the format: 'script:appname:version (by /u/username)'")
        print("4. Ensure you're not behind a VPN or proxy")
        print("5. Try again in a few minutes in case of rate limiting")

if __name__ == "__main__":
    test_reddit_connection()
