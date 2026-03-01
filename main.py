from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
import os


app = FastAPI(
    version="0.1.0"
)
from config import settings




# CORS for your Vite frontend
app.add_middleware(
    CORSMiddleware,
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", ""),
    allow_credentials=True
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Codebase RAG API", "docs": "/docs"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])