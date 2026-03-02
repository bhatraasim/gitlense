from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth , chat, repos
from config import settings


app = FastAPI(
    version="0.1.0"
)
from config import settings

from fastapi import Request
import logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Origin: {request.headers.get('origin')}")
    print(f"Method: {request.method}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response


#Cors configuration
origins = [
    "http://localhost:5173", # standard vite port
    "https://gitlense-production.up.railway.app/",
    "https://gitlense-production.up.railway.app",
    settings.FRONTEND_URL,
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # temporarily allow all origins to test
    allow_credentials=False,  # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Codebase RAG API", "docs": "/docs"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])