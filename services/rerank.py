import cohere
from config import settings

co = cohere.Client(settings.COHERE_API_KEY)

def rerank_chunks(question: str, chunks: list[dict], top_k: int = 5, threshold: float = 0.3) -> list[dict]:

    """
    Reranks the chunks based on their relevance to the query using Cohere's reranking API.
    
    Args:
        chunks (list): A list of text chunks to be reranked.
        query (str): The query string to compare against the chunks.
    
    Returns:
        list: A list of tuples containing the chunk and its relevance score, sorted by relevance.
    """
    documents = [chunk["content"] for chunk in chunks]

    result = co.rerank(
        model='rerank-english-v3.0',
        query=question,
        documents=documents,
        top_n=top_k
    )

    reranked = []

    for r in result.results:
        if r.relevance_score > threshold:
            chunk = chunks[r.index]
            chunk["rerank_score"] = r.relevance_score
            reranked.append(chunk)
    
    return reranked
