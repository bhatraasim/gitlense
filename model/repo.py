from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class RepoStatus(str, Enum):
    queued      = "queued"
    cloning     = "cloning"
    parsing     = "parsing"
    embedding   = "embedding"
    ready       = "ready"
    failed      = "failed"


class Repo(BaseModel):
    id: Optional[str] = None
    user_id: str                        # who owns this repo
    repo_url: str                       # github url
    repo_name: str                      # e.g. "fastapi"
    status: RepoStatus = RepoStatus.queued
    file_count: int = 0
    chunk_count: int = 0
    error: Optional[str] = None        # store error message if failed
    created_at: datetime = datetime.utcnow()


class RepoResponse(BaseModel):
    """What you return to the frontend"""
    id: str
    repo_url: str
    repo_name: str
    status: str
    file_count: int
    chunk_count: int
    error: Optional[str] = None
    created_at: datetime
