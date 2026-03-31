# chatty
Chatty Backend experimentation

# Local Setup
```bash
# However you like to set Python 3.11 and poetry 2.2.0
cd app
poetry install

# To run the local server (from app directory)
poetry run python run.py

# To see lovely docs in your browser:
# http://localhost:8000/docs
```

# Testing
```bash
# Unit tests
cd app  # if needed  
poetry run pytest -W ignore

# Basic RestAPI smoke test with server running locally, from /app
poetry run pytest .\tests_smoke\smoke_test.py

# Basic SocketIO smoke test with server running locally, from /app
poetry run pytest .\tests_smoke\smoke_socketio.py
```

# To Do / To Discuss:
- dockerize
- basic github actions
- OpenAPI spec generation
- CORS approach
- infra as code approach, incl implied terraform dependency graph
- CI/CD approach
- auth/authz approach
- db migration instrumentation
- config / env var management
- exposing service to front-end layer
- auto scaling, load testing, etc..
- cloud spend management
- general SDLC at this stage of maturity
