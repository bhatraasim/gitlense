"""
Ragas Evaluation Script for GitLense RAG Pipeline

Usage:
    uv run python scripts/evaluate.py --dataset golden_dataset.jsonl --repo_id <repo_id>

Output:
    evaluation_results.json — scores for each metric
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config import settings

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from datasets import Dataset

from services.rag import generate_answer


# ── clients

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.OPENAI_API_KEY,
    temperature=0
)

embeddings = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    api_key=settings.OPENAI_API_KEY
)

# wrap for ragas
ragas_llm = LangchainLLMWrapper(llm)
ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)


# ── load golden dataset
def load_golden_dataset(path: str) -> list[dict]:
    dataset = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                dataset.append(json.loads(line))
    return dataset


# ── run RAG pipeline on each question 

def run_rag_pipeline(questions: list[str], repo_id: str) -> list[dict]:
    """Run each question through your actual RAG pipeline."""
    

    results = []
    total = len(questions)

    for i, question in enumerate(questions):
        print(f"[{i+1}/{total}] Running RAG for: {question[:70]}...")
        try:
            result = generate_answer(
                question=question,
                repo_id=repo_id,
                chat_history=[]
            )
            results.append({
                "question": question,
                "answer": result["answer"],
                "contexts": [s.get("content", "") for s in result["sources"]]
            })
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "question": question,
                "answer": "",
                "contexts": []
            })

    return results


# ── build ragas dataset ────────────────────────────────────────────────────────

def build_ragas_dataset(
    golden: list[dict],
    rag_results: list[dict]
) -> Dataset:

    rows = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
    }

    for golden_item, rag_result in zip(golden, rag_results):
        rows["question"].append(golden_item["question"])
        rows["answer"].append(rag_result["answer"])
        rows["contexts"].append(rag_result["contexts"]) # original chunk as context
        rows["ground_truth"].append(golden_item["ground_truth"])

    return Dataset.from_dict(rows)


# ── main ──────────────────────────────────────────────────────────────────────

def run_evaluation(dataset_path: str, repo_id: str, sample_size: int = 20):

    print(f"\n Loading golden dataset from: {dataset_path}")
    golden = load_golden_dataset(dataset_path)
    print(f" Loaded {len(golden)} Q&A pairs")

    # sample to keep costs low — 20 questions costs ~$0.10
    if len(golden) > sample_size:
        import random
        random.seed(42)
        golden = random.sample(golden, sample_size)
        print(f" Sampled {sample_size} pairs for evaluation")

    print(f"\n Running RAG pipeline on {len(golden)} questions...")
    questions = [item["question"] for item in golden]
    rag_results = run_rag_pipeline(questions, repo_id)

    print(f"\n Building Ragas dataset...")
    ragas_dataset = build_ragas_dataset(golden, rag_results)

    print(f"\n Running Ragas evaluation...")
    print(" This will take 2-3 minutes and cost ~$0.10 in OpenAI credits\n")

    results = evaluate(
        dataset=ragas_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )

    # ── print results ─────────────────────────────────────────────────────────

    print("\n" + "="*50)
    print(" EVALUATION RESULTS")
    print("="*50)

    scores = results.to_pandas() # type: ignore

    metrics = {
        "faithfulness":       float(scores["faithfulness"].mean()),
        "answer_relevancy":   float(scores["answer_relevancy"].mean()),
        "context_precision":  float(scores["context_precision"].mean()),
        "context_recall":     float(scores["context_recall"].mean()),
    }

    for metric, score in metrics.items():
        bar = "█" * int(score * 20)
        print(f"  {metric:<22} {score:.3f}  {bar}")

    overall = sum(metrics.values()) / len(metrics)
    print(f"\n  {'Overall Score':<22} {overall:.3f}")
    print("="*50)

    # ── save results ──────────────────────────────────────────────────────────

    output = {
        "timestamp": datetime.now().isoformat(),
        "repo_id": repo_id,
        "sample_size": sample_size,
        "metrics": metrics,
        "overall": overall,
        "per_question": scores.to_dict(orient="records")
    }

    output_path = "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n Full results saved to: {output_path}")
    print("\n What the scores mean:")
    print("  faithfulness      — did the answer stick to the retrieved context?")
    print("  answer_relevancy  — did the answer actually address the question?")
    print("  context_precision — were the retrieved chunks actually relevant?")
    print("  context_recall    — did we retrieve all chunks needed to answer?")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="golden_dataset.jsonl")
    parser.add_argument("--repo_id", required=True)
    parser.add_argument("--sample", type=int, default=20, help="Number of Q&A pairs to evaluate")
    args = parser.parse_args()

    run_evaluation(
        dataset_path=args.dataset,
        repo_id=args.repo_id,
        sample_size=args.sample
    )

