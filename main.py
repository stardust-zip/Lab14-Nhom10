import asyncio
import json
import os
import time

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner


async def run_benchmark_with_results(agent_version: str, dataset: list):
    print(f"Starting Benchmark for {agent_version}...")

    agent = MainAgent(version=agent_version)
    evaluator = RetrievalEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)

    # Chạy song song 5 cases một lúc
    results = await runner.run_all(dataset, batch_size=5)

    summary = {
        "metadata": {
            "version": agent_version,
            "total": len(results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / len(results)
            if results
            else 0,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results)
            / len(results)
            if results
            else 0,
            "mrr": sum(r["ragas"]["retrieval"]["mrr"] for r in results) / len(results)
            if results
            else 0,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results)
            / len(results)
            if results
            else 0,
            "total_cost": sum(r.get("cost", 0.0) for r in results),
        },
    }
    return results, summary


async def main():
    # 0. Load the dataset first
    if not os.path.exists("data/golden_set.jsonl"):
        print(
            "❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước."
        )
        return

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return

    # 1. Fetch BOTH results and summaries (pass the dataset here!)
    v1_results, v1_summary = await run_benchmark_with_results("Agent_V1_Base", dataset)
    v2_results, v2_summary = await run_benchmark_with_results(
        "Agent_V2_Optimized", dataset
    )

    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

    decision = "APPROVE" if delta > 0 else "BLOCK"
    if delta > 0:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

    # 2. Format the combined benchmark results
    combined_results = {"v1": v1_results, "v2": v2_results}

    # 3. Format the combined summary
    combined_summary = {
        "metadata": {
            "total": v1_summary["metadata"]["total"],
            "version": "BASELINE (V1)",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "versions_compared": ["V1", "V2"],
        },
        "metrics": v1_summary["metrics"],
        "regression": {
            "v1": {
                "score": v1_summary["metrics"]["avg_score"],
                "hit_rate": v1_summary["metrics"]["hit_rate"],
                "judge_agreement": v1_summary["metrics"]["agreement_rate"],
            },
            "v2": {
                "score": v2_summary["metrics"]["avg_score"],
                "hit_rate": v2_summary["metrics"]["hit_rate"],
                "judge_agreement": v2_summary["metrics"]["agreement_rate"],
            },
            "decision": decision,
        },
    }

    # 4. Save the combined data
    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(combined_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())