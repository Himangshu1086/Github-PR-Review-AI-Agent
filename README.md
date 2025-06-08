# 🛠️ Setting Up a Virtual Environment (venv)
### Step 1: Create the venv

`python3 -m venv venv`


### Step 2: Activate the venv
macOS/Linux:

bash
`source venv/bin/activate`

### Step 3: Install Dependencies

`pip install -r requirements.txt`

Then freeze the installed packages:

bash

`pip freeze > requirements.txt`

### Step 4: To Deactivate the venv
When done:

bash

`deactivate`


## Start Redis (Docker)

`docker run -d -p 6379:6379 redis`


## Start the python server

`uvicorn app.main:app --reload`

## Start the celery worker

`celery -A app.worker.celery_app worker --loglevel=info`



## Access the UI

`localhost:8000/review-pr`