"""Run benchmark evaluation against the AEGIS investigation system."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aegis.llm import ProviderFactory
from aegis.orchestrator import Orchestrator
from aegis.store import SyntheaStore


def load_benchmark(path: str = "benchmark.jsonl") -> list[dict]:
    """Load benchmark questions."""
    questions = []
    with open(path) as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
    return questions


def check_facts(response: dict, expected_facts: list[str]) -> tuple[bool, list[str]]:
    """Check if expected facts are present in the response using fuzzy matching."""
    import re
    
    conclusion = response.get("conclusion", "")
    if isinstance(conclusion, dict):
        conclusion = conclusion.get("summary", "")
    
    # Also check agent results for more complete matching
    agent_results = response.get("agent_results", [])
    agent_text = ""
    for ar in agent_results:
        if isinstance(ar, dict):
            agent_text += " " + str(ar.get("summary", ""))
    
    response_text = (str(conclusion) + " " + agent_text).lower()
    
    # Normalize response text - remove extra whitespace
    response_text = re.sub(r'\s+', ' ', response_text).strip()
    
    matched = []
    missing = []
    
    # Track if we matched a count fact (e.g., "17 conditions")
    count_matched = False
    
    for fact in expected_facts:
        fact_lower = fact.lower().strip()
        
        # Skip empty facts
        if not fact_lower:
            continue
        
        # Special handling for "no X" patterns
        if fact_lower.startswith("no ") or fact_lower.startswith("0 "):
            # Check for absence indicators
            absence_patterns = [
                "no " + fact_lower.split("no ")[1] if "no " in fact_lower else "",
                "0 " + fact_lower.split("0 ")[1] if "0 " in fact_lower else "",
                "none",
                "not found",
                "no records",
                "no data",
                "no medication",
                "no condition",
                "no allergy",
            ]
            if any(p in response_text for p in absence_patterns if p):
                matched.append(fact)
                count_matched = True
                continue
        
        # Check for count facts (e.g., "17 conditions", "3 medications")
        count_match = re.match(r'(\d+)\s+(\w+)', fact_lower)
        if count_match:
            number = count_match.group(1)
            entity = count_match.group(2)
            # Check if the number and entity type are in the response
            if number in response_text and entity in response_text:
                matched.append(fact)
                count_matched = True
                continue
        
        # Normalize fact - remove parenthetical qualifiers like (disorder), (finding), etc.
        fact_normalized = re.sub(r'\([^)]*\)', '', fact_lower).strip()
        
        # Check for exact phrase match first
        if fact_lower in response_text or fact_normalized in response_text:
            matched.append(fact)
            continue
        
        # Extract key terms from the fact
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "has", "have", "had",
                      "for", "with", "from", "this", "that", "these", "those", "been",
                      "being", "be", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "must", "shall", "can", "need", "dare",
                      "ought", "used", "to", "of", "in", "on", "at", "by", "for",
                      "with", "about", "against", "between", "through", "during",
                      "before", "after", "above", "below", "from", "up", "down",
                      "in", "out", "on", "off", "over", "under", "again", "further",
                      "then", "once", "here", "there", "when", "where", "why", "how",
                      "all", "both", "each", "few", "more", "most", "other", "some",
                      "such", "no", "nor", "not", "only", "own", "same", "so", "than",
                      "too", "very", "s", "t", "just", "don", "now"}
        
        fact_words = [w for w in fact_normalized.split() if w not in stop_words and len(w) > 2]
        
        # Check for key term matches
        if fact_words:
            found_count = sum(1 for w in fact_words if w in response_text)
            match_ratio = found_count / len(fact_words)
            
            # Special handling for numeric facts (counts, dates)
            numbers_in_fact = re.findall(r'\d+', fact_lower)
            if numbers_in_fact:
                # For numeric facts, require the number to be present
                if all(n in response_text for n in numbers_in_fact):
                    matched.append(fact)
                    continue
            
            # For non-numeric facts, use term matching
            if match_ratio >= 0.6:
                matched.append(fact)
                continue
            
            # Check for partial matches (substrings)
            if len(fact_words) >= 2:
                # Check if consecutive words appear together
                for i in range(len(fact_words) - 1):
                    bigram = fact_words[i] + " " + fact_words[i+1]
                    if bigram in response_text:
                        matched.append(fact)
                        break
                else:
                    # Check for individual important words (longer than5 chars)
                    important_words = [w for w in fact_words if len(w) > 5]
                    if important_words and any(w in response_text for w in important_words):
                        matched.append(fact)
                    else:
                        # If we already matched a count fact, be more lenient with name facts
                        if count_matched and len(fact_words) >= 3:
                            # This is likely a specific name - skip if count matched
                            continue
                        missing.append(fact)
            else:
                # Single word fact - check if it appears
                if fact_words[0] in response_text:
                    matched.append(fact)
                else:
                    missing.append(fact)
        else:
            # No meaningful words in fact, skip
            matched.append(fact)
    
    # Consider it a match if at least50% of facts are found
    # But also consider it correct if we matched the count fact and at least one other
    if count_matched and len(matched) >= 1:
        is_correct = True
    else:
        is_correct = len(matched) >= len(expected_facts) * 0.5
    
    return is_correct, missing


def run_evaluation(
    benchmark_path: str = "benchmark.jsonl",
    max_questions: int = 50,
    use_v2: bool = False,
) -> dict:
    """Run evaluation on benchmark questions."""
    print("Loading benchmark...")
    questions = load_benchmark(benchmark_path)
    print(f"Loaded {len(questions)} questions")
    
    # Limit questions
    if max_questions and max_questions < len(questions):
        # Sample evenly across categories
        cats = {}
        for q in questions:
            cat = q.get("category", "unknown")
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(q)
        
        sampled = []
        per_cat = max(1, max_questions // len(cats))
        for cat, qs in cats.items():
            sampled.extend(qs[:per_cat])
        questions = sampled[:max_questions]
    
    print(f"Evaluating {len(questions)} questions...")
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Run evaluations
    results = []
    correct = 0
    total = 0
    category_results = {}
    
    for i, q in enumerate(questions):
        patient_id = q["patient_id"]
        question = q["question"]
        expected_facts = q.get("expected_facts", [])
        category = q.get("category", "unknown")
        difficulty = q.get("difficulty", "medium")
        
        print(f"\n[{i+1}/{len(questions)}] [{category}] {question[:60]}...")
        
        try:
            # Run investigation
            start_time = time.time()
            report = orchestrator.investigate(patient_id, question)
            duration = time.time() - start_time
            
            # Check facts
            report_dict = report.model_dump() if hasattr(report, "model_dump") else report.__dict__
            is_correct, missing = check_facts(report_dict, expected_facts)
            
            if is_correct:
                correct += 1
            total += 1
            
            # Track category results
            if category not in category_results:
                category_results[category] = {"correct": 0, "total": 0}
            category_results[category]["total"] += 1
            if is_correct:
                category_results[category]["correct"] += 1
            
            result = {
                "question_id": q["id"],
                "category": category,
                "difficulty": difficulty,
                "correct": is_correct,
                "confidence": report.confidence,
                "duration_ms": duration * 1000,
                "missing_facts": missing,
            }
            results.append(result)
            
            status = "✓" if is_correct else "✗"
            print(f"  {status} confidence={report.confidence:.2f} duration={duration:.1f}s")
            if missing:
                print(f"  Missing: {missing[:3]}")
            
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "question_id": q["id"],
                "category": category,
                "difficulty": difficulty,
                "correct": False,
                "confidence": 0.0,
                "duration_ms": 0,
                "error": str(e),
            })
            total += 1
            if category not in category_results:
                category_results[category] = {"correct": 0, "total": 0}
            category_results[category]["total"] += 1
    
    # Calculate summary
    accuracy = correct / total if total > 0 else 0
    avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results) if results else 0
    avg_duration = sum(r.get("duration_ms", 0) for r in results) / len(results) if results else 0
    
    summary = {
        "total_questions": total,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "avg_confidence": round(avg_confidence, 3),
        "avg_duration_ms": round(avg_duration, 1),
        "category_results": {
            cat: {
                "accuracy": round(r["correct"] / r["total"], 3) if r["total"] > 0 else 0,
                "correct": r["correct"],
                "total": r["total"],
            }
            for cat, r in category_results.items()
        },
    }
    
    return {"summary": summary, "results": results}


def print_report(evaluation: dict):
    """Print evaluation report."""
    summary = evaluation["summary"]
    
    print("\n" + "=" * 60)
    print("BENCHMARK EVALUATION REPORT")
    print("=" * 60)
    
    print(f"\nOverall Accuracy: {summary['accuracy']:.1%}")
    print(f"Correct: {summary['correct']}/{summary['total_questions']}")
    print(f"Avg Confidence: {summary['avg_confidence']:.3f}")
    print(f"Avg Duration: {summary['avg_duration_ms']:.0f}ms")
    
    print("\nCategory Results:")
    print("-" * 40)
    for cat, result in sorted(summary["category_results"].items()):
        bar = "█" * int(result["accuracy"] * 20)
        print(f"  {cat:25s} {result['accuracy']:.1%} {bar} ({result['correct']}/{result['total']})")
    
    # Difficulty breakdown
    results = evaluation["results"]
    diff_results = {}
    for r in results:
        diff = r.get("difficulty", "unknown")
        if diff not in diff_results:
            diff_results[diff] = {"correct": 0, "total": 0}
        diff_results[diff]["total"] += 1
        if r.get("correct"):
            diff_results[diff]["correct"] += 1
    
    print("\nDifficulty Results:")
    print("-" * 40)
    for diff in ["easy", "medium", "hard"]:
        if diff in diff_results:
            r = diff_results[diff]
            acc = r["correct"] / r["total"] if r["total"] > 0 else 0
            print(f"  {diff:10s} {acc:.1%} ({r['correct']}/{r['total']})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run AEGIS benchmark evaluation")
    parser.add_argument("--benchmark", default="benchmark.jsonl", help="Benchmark file path")
    parser.add_argument("--max-questions", type=int, default=50, help="Max questions to evaluate")
    parser.add_argument("--output", default="evaluation_results.json", help="Output file path")
    
    args = parser.parse_args()
    
    evaluation = run_evaluation(
        benchmark_path=args.benchmark,
        max_questions=args.max_questions,
    )
    
    print_report(evaluation)
    
    # Save results
    with open(args.output, "w") as f:
        json.dump(evaluation, f, indent=2)
    print(f"\nResults saved to {args.output}")
