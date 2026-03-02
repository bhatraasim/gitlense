from fastapi import FastAPI , Response
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://gitlens-client.netlify.app",  # your exact netlify URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
        }
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