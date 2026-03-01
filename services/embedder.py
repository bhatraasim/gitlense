from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings 
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from config import settings



def chunks_to_documents(chunks: list[dict]) -> list[Document]:
   """
    Convert our parser dicts into LangChain Document objects
    Document has two fields: page_content (the text) and metadata (everything else)
    """
   
   return [
      Document(
         page_content = chunk["chunk_text"],
            metadata = {
               "file_path": chunk["file_path"],
                "extension": chunk["extension"],
                "chunk_index": chunk["chunk_index"],
                "repo_id": chunk.get("repo_id", ""),
            }
      )

      for chunk in chunks
   ]

def embed_documents(chunks: list[dict], repo_id: str) -> int:
    """
    Takes all chunks from parse_repo(), embeds them, stores in Qdrant.
    Returns number of chunks stored.
    """
    # Create embeddings
    embeddings_model = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,       # text-embedding-3-small
        api_key=settings.OPENAI_API_KEY
    )

    
   # 2. attach repo_id to every chunk before converting
    for chunk in chunks:
        chunk["repo_id"] = repo_id
    
     # 3. convert dicts → LangChain Documents
    documents = chunks_to_documents(chunks)

    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings_model,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
        force_recreate=False       # don't wipe existing data
    )

    return len(documents)
