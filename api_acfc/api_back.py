from fastapi import FastAPI
from api_fast_dashboard import dashboard_router

app = FastAPI()
app.include_router(dashboard_router)