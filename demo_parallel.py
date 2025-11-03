#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
병렬 API 호출 시각화 데모
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def simulate_api_call(text: str, task_id: int) -> tuple[int, str]:
    """API 호출 시뮬레이션 (2초 소요)"""
    print(f"  [Task {task_id}] Starting API call...")
    time.sleep(2)  # Gemini API 호출 2초
    print(f"  [Task {task_id}] API call completed")
    return (task_id, f"Summary {task_id}: {text[:30]}...")

def demo_sequential():
    """순차 처리 (Before)"""
    print("=" * 60)
    print("BEFORE: Sequential Processing")
    print("=" * 60)

    tasks = ["Document1", "Document2", "Document3", "Document4", "Document5"]
    start = time.time()

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}] Processing: {task}")
        result = simulate_api_call(task, i)
        results.append(result)

    duration = time.time() - start
    print(f"\nTotal time: {duration:.1f}s")
    print(f"(2s x 5 tasks = 10s)")


def demo_parallel():
    """병렬 처리 (After)"""
    print("\n" + "=" * 60)
    print("AFTER: Parallel Processing")
    print("=" * 60)

    tasks = ["Document1", "Document2", "Document3", "Document4", "Document5"]
    start = time.time()
    results = []

    # ThreadPoolExecutor로 5개 작업 동시 제출
    with ThreadPoolExecutor(max_workers=5) as executor:
        print(f"\n[1] Submitting 5 tasks to ThreadPoolExecutor...")

        future_to_task = {
            executor.submit(simulate_api_call, task, i): i
            for i, task in enumerate(tasks, 1)
        }

        print("[2] All tasks submitted. Waiting for completion...\n")

        # 완료되는 대로 결과 수집
        for future in as_completed(future_to_task):
            result = future.result()
            results.append(result)
            print(f"    Task {result[0]} finished (total results: {len(results)})")

    duration = time.time() - start
    print(f"\nTotal time: {duration:.1f}s")
    print(f"(All 5 tasks in parallel = 2s)")


def main():
    print("\nAPI CALL OPTIMIZATION DEMO\n")

    # Demo 1: Sequential (slow)
    demo_sequential()

    # Demo 2: Parallel (fast)
    demo_parallel()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nKey Points:")
    print("  - Before: 5 API calls in sequence = 10 seconds")
    print("  - After: 5 API calls in parallel = 2 seconds")
    print("  - Speed improvement: 5x faster!")
    print("  - All 5 tasks run at the same time")
    print("  - Results collected as each completes")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
