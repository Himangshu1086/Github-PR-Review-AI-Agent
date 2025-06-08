# 🛠️ Setting Up the Project and a Virtual Environment (venv) locally
### Step 1: Create the venv

`python3 -m venv venv`


### Step 2: Activate the venv
macOS/Linux:

bash
`source venv/bin/activate`

### Step 3: Install Dependencies

`pip install -r requirements.txt`

you can then pin the versions with :

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



<br>
<br>


# If you don't want to all of the above Shit : JUST HIT 

`docker compose up --build -d`

### 🚀 And Enjoy

        localhost:8000/docs         ---> for API contract
        localhost:8000/review-pr    ---> for UI