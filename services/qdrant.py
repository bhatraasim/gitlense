from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings 
from langchain_qdrant import QdrantVectorStore
from config import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings  # Add this
from config import settings


def get_embeddings():
    # single place to create the embeddings model
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY
    )


def get_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),       # object not string
        url=settings.QDRANT_URL,          # from config, not hardcoded
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION
    )


def search(question : str ,repo_id : str , top_k : int = 5 ) -> list[dict]:
    
    vector_store = get_vector_store()

    repo_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.repo_id",
                match=MatchValue(value=repo_id)
            )
        ]
    )
    results = vector_store.similarity_search_with_score(
        query=question,
        k=top_k,
        filter=repo_filter
    )

    return [
        {
            "file_path": doc.metadata.get("file_path", ""),
            "extension": doc.metadata.get("extension", ""),
            "chunk_index": doc.metadata.get("chunk_index", -1),
            "repo_id": doc.metadata.get("repo_id", ""),
            "content": doc.page_content,
            "score": round(score, 4)  
        }
        for doc , score in results
    ]


def delete_repo(repo_id: str):

    # use raw QdrantClient for bulk deletes — more reliable
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )

    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.repo_id",
                    match=MatchValue(value=repo_id)
                )
            ]
        )
    )