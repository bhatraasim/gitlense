import cohere
from config import settings

co = cohere.Client(settings.COHERE_API_KEY)

def rerank_chunks(question: str, chunks: list[dict], top_k: int = 5, threshold: float = 0) -> list[dict]:
    if not chunks:
        return []
    
    # send file path + content together — gives Cohere more context
    documents = [
        f"File: {chunk['file_path']}\n\n{chunk['content']}"
        for chunk in chunks
    ]
    # print(f"First document sample: {documents[0][:200]}")  # add this
    
    results = co.rerank(
        model="rerank-english-v3.0",
        query=question,
        documents=documents,
        top_n=top_k,
        return_documents=True
    )
    
    reranked = []
    for r in results.results:
        chunk = chunks[r.index]
        chunk["rerank_score"] = r.relevance_score
        print(f"File: {chunk['file_path']} Score: {r.relevance_score}")  # debug
        reranked.append(chunk)
    
    # sort by score
    reranked = sorted(reranked, key=lambda x: x["rerank_score"], reverse=True)
    
    # only filter if score is truly terrible
    # reranked = [c for c in reranked if c["rerank_score"] > 0.001]
    
    # print(f"Cohere raw results count: {len(results.results)}")
    # for r in results.results:
    #     print(f"  index={r.index} score={r.relevance_score}")


    return reranked[:top_k]