from fastapi import FastAPI
from app.routes import health, auth

app = FastAPI(title="Orçamento AI Backend")

app.include_router(health.router)
app.include_router(auth.router)

