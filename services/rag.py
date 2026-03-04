from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from services.qdrant import search
from config import settings
from services.rerank import rerank_chunks

llm = ChatOpenAI(
    model=settings.CHAT_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.2
)

def generate_answer(question: str, repo_id: str, chat_history: list = []) -> dict:

    chunks = search(question=question, repo_id=repo_id, top_k=20)
    print(f"Qdrant returned: {len(chunks)} chunks")

    chunks = rerank_chunks(question=question, chunks=chunks, top_k=5)
    print(f"After reranking: {len(chunks)} chunks")

    if not chunks:
        return {
            "answer": "I couldn't find anything relevant in this codebase.",
            "sources": []
        }

    formatted_chunks = "\n\n".join([
        f"File: {chunk['file_path']}\n```\n{chunk['content']}\n```"
        for chunk in chunks
    ])

    system_prompt = f"""
    You are an expert code assistant analyzing a GitHub repository.
    You will be given relevant code chunks from the codebase and a question.

    Rules:
    - Answer based ONLY on the provided code chunks
    - Always mention which file your answer comes from
    - If the answer is not in the chunks, say "I couldn't find that in this codebase"
    - Be concise and technical
    - When showing code, use markdown code blocks

    Context:
    {formatted_chunks}
    """

    messages = [
        SystemMessage(content=system_prompt),
        *chat_history,
        HumanMessage(content=question)
    ]

    response = llm.invoke(messages)

    return {
        "answer": response.content,
        "sources": [
            {
                "file_path": chunk["file_path"],
                "chunk_index": chunk["chunk_index"],
                "score": chunk.get("rerank_score", chunk.get("score", 0))
            }
            for chunk in chunks
        ]
    }