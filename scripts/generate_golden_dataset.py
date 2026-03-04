import argparse
import json
import time
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, ScrollRequest
import sys
import os

sys.path.append(str(Path(__file__).parent.parent))
from config import settings


llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.OPENAI_API_KEY,
    temperature=0.2
)

qdrant = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)



def get_all_chunks(repo_id:str)->list[dict]:
    chunks = []
    offset = 0

    while True:
        results, next_offset = qdrant.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[FieldCondition(
                        key="metadata.repo_id",
                        match=MatchValue(value=repo_id)
                    )]
                ),
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
        
        for point in results:
            payload = point.payload or {}
            metadata = payload.get("metadata", {})
            chunks.append({
                "file_path": metadata.get("file_path", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "content": payload.get("page_content", "")
            })

        if next_offset is None:
            break

        offset = next_offset
    return chunks

def generate_qa_for_chunks(chunk:dict)->list[dict]:
    """Ask GPT to generate 2 Q&A pairs for a single chunk."""

    if not chunk["content"].strip():
        return []
    
    prompt = f"""You are creating an evaluation dataset for a RAG system that answers questions about code.

    Given this code chunk from file `{chunk['file_path']}`:
    ```
    {chunk['content'][:1500]}
    ```

    Generate exactly 2 question-answer pairs that:
    1. Can be answered DIRECTLY from this code chunk
    2. Are specific and technical (not vague)
    3. Would be realistic questions a developer would ask

    Return ONLY valid JSON in this exact format, nothing else:
    [
    {{
        "question": "...",
        "ground_truth": "..."
    }},
    {{
        "question": "...",
        "ground_truth": "..."
    }}
    ]"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        text = str(response.content).strip()

        # strip markdown code fences if present

        if text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        pairs = json.loads(text)
        return [
            {
                "question": pair["question"],
                "context": chunk["content"],
                "ground_truth": pair["ground_truth"],
                "file_path": chunk["file_path"],
                "chunk_index": chunk["chunk_index"],
            }
            for pair in pairs
            if pair.get("question") and pair.get("ground_truth")
        ]

    except Exception as e:
        print(f"Error processing chunk {chunk['file_path']}:{chunk['chunk_index']}: {e}")
        return []    
                           




def generate_golden_dataset(repo_id:str, output_path:str = "golden_dataset.jsonl"):

    print(f"\n Fetching chunks for repo: {repo_id}")
    chunks = get_all_chunks(repo_id)
    print(f" Found {len(chunks)} chunks")

    if not chunks:
        print("No chunks found. Make sure the repo is ingested.")
        return
    
    dataset = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):

        print(f"\n[{i+1}/{total}] Generating Q&A for: {chunk['file_path']}")
        pairs = generate_qa_for_chunks(chunk)


        for pair in pairs:
            print(f"  Q: {pair['question'][:80]}...")
            dataset.append(pair)

        #to avoid hitting rate limits, sleep for a short time after each request
        time.sleep(0.5)

        #save to golden_dataset.jsonl after each chunk is processed
    output = Path(output_path)
    with open(output_path, "w") as f:
            for item in dataset:
                f.write(json.dumps(item) + "\n")

    print(f"\n Done! Generated {len(dataset)} Q&A pairs")
    print(f" Saved to: {output.absolute()}")
    print(f"\n Sample entry:")
    if dataset:
        print(json.dumps(dataset[0], indent=2))   
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_id", required=True, help="MongoDB repo ID")
    parser.add_argument("--output", default="golden_dataset.jsonl", help="Output file path")
    args = parser.parse_args()

    generate_golden_dataset(repo_id=args.repo_id, output_path=args.output)
    
