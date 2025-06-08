from fastapi import FastAPI
from app import api, ui


app = FastAPI()
app.include_router(api.router)
app.include_router(ui.router)