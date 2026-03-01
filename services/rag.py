from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from services.qdrant import search
from config import settings


def generate_answer(question: str, repo_id :str , chat_history) -> dict:

    chunks = search(question=question, repo_id=repo_id, top_k=5)
    if not chunks:
        return {
            "answer": "I couldn't find anything relevant in this codebase.",
            "sources": []
        }
    llm = ChatOpenAI(
        model=settings.CHAT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2
        ) 

    formatted_chunks = "\n\n".join(
        [
            f"File: {chunk['file_path']} (score: {chunk['score']})\n```\n{chunk['content']}\n```"
            for chunk in chunks
        ]
    )


    system_prompt = f""""
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
        HumanMessage(content=question)
    ]

    response = llm.invoke(messages)
    answer = response.content
    return {

        "answer": answer,           # the LLM's response string
        "sources": [                # the chunks used, for frontend citations
            {
                "file_path": chunk["file_path"],
                "chunk_index": chunk["chunk_index"],
                "score": chunk["score"]
            }
            for chunk in chunks
        ]
    }