# Twitter Mentions API

A FastAPI-based backend service that enables users to fetch, store, and respond to Twitter mentions through a secure OAuth 2.0 flow.

## Features

- OAuth 2.0 integration with Twitter (X)
- Automated polling for new mentions
- Secure storage of mentions in database
- API endpoints for retrieving and responding to mentions
- Background job for continuous mention monitoring

## Prerequisites

- Python 3.8+
- MariaDb
- Twitter Developer Account with API access

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd twitter-mentions-api<backend name>
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
# Database
MONGODB_URL=mongodb_url

MONGODB_DB_NAME=db_name

# OpenAI API key
OPENAI_API_KEY=openAI_key

# Twitter API
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_CALLBACK_URL=http://localhost:8000/auth/twitter/callback

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

5. Initialize the database:
- Create a local database with docker or Xampp

- Edit the .env to point to that database

```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```

## License

MIT 

HI PAUL 