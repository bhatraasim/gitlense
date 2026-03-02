print("importing github...")
from services.github import clone_repository, get_repo_info
print("importing parser...")
from services.parser import parse_repo
print("importing embedder...")
from services.embedder import embed_documents
print("all imports ok")


import os
import shutil
from bson import ObjectId
from pymongo import MongoClient
from worker.celery_app import celery_app
from config import settings
from services.github import clone_repository, get_repo_info
from services.parser import parse_repo
from services.embedder import embed_documents

# sync mongo client — only for use inside celery tasks
sync_client = MongoClient(settings.MONGODB_URI, tlsAllowInvalidCertificates=True)
sync_db = sync_client[settings.MONGODB_DB_NAME]


def update_status(repo_id: str, status: str, extra: dict = {}):
    """helper to avoid repeating update_one everywhere"""
    sync_db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$set": {"status": status, **extra}}
    )


@celery_app.task(bind=True)
def ingest_repo(self, repo_id: str, repo_url: str):

    clone_path = f"{settings.TEMP_CLONE_DIR}/{repo_id}"

    try:
        # 1. validate repo exists
        repo = sync_db.repos.find_one({"_id": ObjectId(repo_id)})
        if not repo:
            raise ValueError("Repo not found in database")

        # 2. check repo size before cloning
        repo_info = get_repo_info(repo_url=repo_url)
        if repo_info["size"] > settings.MAX_REPO_SIZE_MB * 1000:
            raise ValueError("Repo too large to process")

        # 3. clone
        update_status(repo_id, "cloning")
        clone_repository(repo_url=repo_url, dest_path=clone_path)

        # 4. parse
        update_status(repo_id, "parsing")
        chunks = parse_repo(clone_path)

        # 5. embed
        update_status(repo_id, "embedding")
        chunk_count = embed_documents(chunks, repo_id)

        # 6. done
        update_status(repo_id, "ready", {
            "chunk_count": chunk_count,
            "file_count": len(set(c["file_path"] for c in chunks))
        })

    except Exception as e:
        update_status(repo_id, "failed", {"error": str(e)})
        raise self.retry(exc=e)

    finally:
        # always cleanup — even if something failed
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)