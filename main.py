from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth , chat, repos
from config import settings


app = FastAPI(
    version="0.1.0"
)
from config import settings



#Cors configuration
origins = [
    "http://localhost:5173", # standard vite port
    settings.FRONTEND_URL,
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Critical: Allows POST, OPTIONS, PUT, DELETE
    allow_headers=["*"], # Critical: Allows Content-Type and Authorization headers
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