from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from celery.result import AsyncResult
from routers.auth import get_current_user
from services.database import db
from services.qdrant import delete_repo as delete_qdrant_vectors
from model.repo import Repo
from worker.tasks import ingest_repo as ingest_repo_task  # aliased
from worker.celery_app import celery_app

router = APIRouter()


class IngestRequest(BaseModel):
    repo_url: str


@router.post("/ingest")
async def ingest(request: IngestRequest, user=Depends(get_current_user)):

    # 1. validate github URL
    if not request.repo_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    # 2. check not already ingested by this user
    existing = await db.repos.find_one({
        "user_id": str(user["_id"]),
        "repo_url": request.repo_url
    })
    if existing:
        raise HTTPException(status_code=400, detail="Repository already ingested")

    # 3. create repo document
    repo_doc = Repo(
        user_id=str(user["_id"]),
        repo_url=request.repo_url,
        repo_name=request.repo_url.split("/")[-1],
        status="queued",
        file_count=0,
        chunk_count=0,
        error=None,
        created_at=datetime.utcnow()
    )

    result = await db.repos.insert_one(repo_doc.model_dump(exclude={"id"}))
    repo_id = str(result.inserted_id)

    # 4. fire celery task
    
    task = ingest_repo_task.delay(repo_id, request.repo_url)# type: ignore

    # 5. store task_id in mongo so status endpoint can find it
    await db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$set": {"task_id": task.id}}
    )

    return {
        "repo_id": repo_id,
        "task_id": task.id,
        "status": "queued"
    }


@router.get("/status/{repo_id}")
async def repo_status(repo_id: str, user=Depends(get_current_user)):

    repo = await db.repos.find_one({
        "_id": ObjectId(repo_id),
        "user_id": str(user["_id"])
    })
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    # get celery state using stored task_id
    task_result = AsyncResult(repo["task_id"], app=celery_app)

    return {
        "task_id": repo["task_id"],
        "celery_state": task_result.state,
        "repo_status": repo["status"],
        "file_count": repo["file_count"],
        "chunk_count": repo["chunk_count"],
        "error": repo.get("error")
    }


@router.get("/")
async def get_repos(user=Depends(get_current_user)):
    repos = await db.repos.find(
        {"user_id": str(user["_id"])}
    ).to_list(100)

    # convert ObjectId to string
    for repo in repos:
        repo["_id"] = str(repo["_id"])

    return repos


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str, user=Depends(get_current_user)):

    repo = await db.repos.find_one({
        "_id": ObjectId(repo_id),
        "user_id": str(user["_id"])
    })
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    # delete from qdrant
    delete_qdrant_vectors(repo_id)

    # delete from mongo
    await db.repos.delete_one({"_id": ObjectId(repo_id)})

    return {"message": "Repository deleted successfully"}