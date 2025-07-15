# Reddit User Persona Generator

[![Deployed App](https://img.shields.io/badge/Streamlit-Deployed-blue)](https://persona-generator-h5hlkznomy97gnubxn5oks.streamlit.app/)

A tool that generates detailed user personas based on Reddit user activity using AI analysis. This application is deployed on Streamlit Cloud and uses Google's Gemini AI to analyze Reddit user data.

## Live Demo

Try the deployed application at: [https://persona-generator-h5hlkznomy97gnubxn5oks.streamlit.app/](https://persona-generator-h5hlkznomy97gnubxn5oks.streamlit.app/)

## Features

- Extracts user data from Reddit profiles
- Analyzes comments and posts
- Generates detailed user personas
- Cites specific Reddit content for persona characteristics
- Saves output to formatted text files
- Uses Google's Gemini AI for persona generation
- Modern web interface using Streamlit
- Automatic deployment on Streamlit Cloud


## Deployment Instructions

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reddit-persona-web.git
cd reddit-persona-web
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT="script:reddit-persona:v1.0 (by u/your_username)"

# Google AI API key
GOOGLE_API_KEY=your_google_api_key

# Rate limiting settings (in seconds)
REQUEST_DELAY=2
MAX_RETRIES=3
TIMEOUT=30

# Debug mode
DEBUG=True
```

4. Run the application locally:
```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

1. Go to https://streamlit.io/cloud
2. Sign in with your GitHub account
3. Click "New app"
4. Connect your GitHub repository
5. Select your repository
6. Click "Deploy"

Once deployed:

1. Go to your app's settings
2. Navigate to "Secrets"
3. Add these environment variables:
   - `GOOGLE_API_KEY`: Your Google AI API key
   - `REDDIT_CLIENT_ID`: Your Reddit client ID
   - `REDDIT_CLIENT_SECRET`: Your Reddit client secret
   - `REDDIT_USER_AGENT`: Your Reddit user agent string

## Usage

1. Visit the deployed Streamlit app
2. Enter a Reddit profile URL in the format:
   - https://www.reddit.com/user/username/
   - or just the username
3. Click "Generate Persona"
4. The app will:
   - Fetch user data from Reddit
   - Generate a detailed persona using AI
   - Save the output to a text file
   - Display the persona with citations

## Technical Details

- Frontend: Streamlit
- Backend: Python
- AI: Google's Gemini
- Data Extraction: PRAW
- Environment Management: python-dotenv
- Follows PEP-8 coding standards
- Includes error handling and rate limiting

## Project Structure

```
reddit-persona-web/
├── app.py              # Main Streamlit application
├── persona_generator.py # AI-based persona generation
├── scraper.py          # Reddit data scraping
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (gitignored)
├── .env.example        # Example environment variables
└── output/            # Directory for generated persona files
```

## License

This project is your property and is intended for evaluation purposes only.
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```
GOOGLE_API_KEY=your_google_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT="script:reddit_persona_generator:1.0 (by /u/your_username)"
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. In the web interface:
   - Enter a Reddit profile URL (e.g., https://www.reddit.com/user/kojied/)
   - Click "Generate Persona"
   - The app will:
     - Fetch user data from Reddit
     - Generate a detailed persona using AI
     - Save the output to a text file in the `output` directory

## Sample Outputs

The repository includes sample persona outputs for the test users:
- kojied
- Hungry-Move-6603

These can be found in the `output` directory.

## Project Structure

- `app.py`: Main Streamlit application
- `persona_generator.py`: AI-based persona generation logic
- `scraper.py`: Reddit data scraping functionality
- `requirements.txt`: Project dependencies
- `.env`: Environment variables configuration
- `output/`: Directory for generated persona files

## Technical Details

- Uses PRAW for Reddit API interaction
- Implements error handling and rate limiting
- Uses Google's Gemini AI for persona generation
- Follows PEP-8 coding standards
- Includes proper documentation and comments

## License

This project is your property and is intended for evaluation purposes only.
