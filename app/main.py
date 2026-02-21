from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import users, health

app = FastAPI(
    title="Memorum Test API",
    description="A simple API for testing Memorum decision capture",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router, prefix="/users", tags=["users"])
