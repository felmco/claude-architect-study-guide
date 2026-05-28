"""
Task Statement 4.5: Design efficient batch processing strategies

Key concepts:
- Message Batches API: 50% cost savings, up to 24-hour processing window
- No guaranteed latency SLA — NOT suitable for blocking workflows
- No multi-turn tool calling within a single batch request
- custom_id for correlating request/response pairs
- Resubmit only failed documents (identified by custom_id), not entire batch
- Chunking oversized documents on retry

Exam Q11: Pre-merge check (blocking) + overnight report (non-blocking)
Answer A: Use batch API for overnight report ONLY; keep sync for pre-merge.
"""

import json
import os
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
BATCH_MODEL = "claude-haiku-4-5-20251001"  # Cost-effective for batch processing


# ─── Workflow selection guide ──────────────────────────────────────────────────

def show_batch_vs_sync_decision():
    """When to use Message Batches API vs synchronous API."""
    print("""
Message Batches API — Decision Guide
=====================================

USE BATCH API when:
  ✓ Non-blocking: results are not needed immediately
  ✓ Latency tolerant: 24-hour window is acceptable
  ✓ Large volume: 100s-1000s of documents
  ✓ Cost-sensitive: 50% savings matter
  Examples:
    - Overnight technical debt reports (Exam Q11 ✓)
    - Weekly compliance document audit
    - Nightly test generation for unchanged files
    - Mass historical data extraction

DO NOT USE BATCH API when:
  ✗ Blocking: user/process waits for result
  ✗ Latency-critical: must complete in < minutes
  ✗ Multi-turn tool calling required within one request
  Examples:
    - Pre-merge code review check (Exam Q11 ✗)
    - Real-time customer support response
    - Interactive document extraction
    - Any workflow where a developer is waiting

BATCH API CHARACTERISTICS:
  - 50% cost savings vs synchronous API
  - Processing time: usually < 1 hour, up to 24 hours
  - No guaranteed latency SLA (cannot use for blocking flows)
  - No multi-turn tool calling within a single request
  - custom_id: correlate requests with responses
  - Poll for completion or use webhooks
""")


# ─── Batch submission pattern ──────────────────────────────────────────────────

def create_batch_requests(documents: list[dict]) -> list[dict]:
    """
    Create batch request objects for multiple documents.
    Each request has a custom_id for tracking and correlation.
    """
    requests = []
    for doc in documents:
        requests.append({
            "custom_id": doc["id"],  # For correlating request/response
            "params": {
                "model": BATCH_MODEL,
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Extract key financial data from this document:\n\n"
                        f"{doc['content'][:2000]}\n\n"  # Chunk if needed
                        f"Return: vendor, total_amount, invoice_date (ISO 8601), invoice_number"
                    ),
                }],
            },
        })
    return requests


def submit_batch(requests: list[dict]) -> Optional[str]:
    """
    Submit a batch request to the Message Batches API.
    Returns the batch_id for polling.
    """
    try:
        print(f"Submitting batch of {len(requests)} requests...")
        batch = client.beta.messages.batches.create(requests=requests)
        print(f"Batch submitted: {batch.id}")
        print(f"Status: {batch.processing_status}")
        return batch.id
    except Exception as e:
        print(f"Batch submission failed: {e}")
        return None


def poll_batch_until_complete(batch_id: str, max_wait_seconds: int = 300) -> Optional[object]:
    """
    Poll for batch completion.
    In production: use webhooks or schedule a check after expected completion time.
    For overnight batches: check once in the morning (not continuous polling).
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            batch = client.beta.messages.batches.retrieve(batch_id)
            print(f"Status: {batch.processing_status} | "
                  f"Completed: {batch.request_counts.succeeded}/{batch.request_counts.processing}")

            if batch.processing_status == "ended":
                return batch

            time.sleep(5)

        except Exception as e:
            print(f"Poll error: {e}")
            break

    print(f"Batch did not complete within {max_wait_seconds}s timeout")
    return None


def process_batch_results(batch_id: str) -> tuple[list[dict], list[str]]:
    """
    Retrieve and process batch results.
    Returns: (successful_results, failed_custom_ids)

    failed_custom_ids can be resubmitted individually with modifications.
    """
    successful = []
    failed = []

    try:
        for result in client.beta.messages.batches.results(batch_id):
            if result.result.type == "succeeded":
                # Extract text from successful result
                content = result.result.message.content[0].text if result.result.message.content else ""
                successful.append({
                    "custom_id": result.custom_id,
                    "content": content,
                })
            elif result.result.type == "errored":
                # Track failed requests by custom_id for resubmission
                failed.append(result.custom_id)
                error_info = result.result.error
                print(f"  Failed: {result.custom_id} — {error_info}")
    except Exception as e:
        print(f"Error retrieving results: {e}")

    return successful, failed


# ─── Failure handling: resubmit only failed documents ─────────────────────────

def handle_failed_requests(
    failed_ids: list[str],
    original_documents: dict[str, dict],
) -> list[dict]:
    """
    Handle batch failures:
    - Resubmit only the failed documents (not the entire batch)
    - For documents that exceeded context: chunk them before resubmitting
    """
    if not failed_ids:
        print("No failures to handle.")
        return []

    print(f"\nHandling {len(failed_ids)} failures...")
    retry_requests = []

    for custom_id in failed_ids:
        doc = original_documents.get(custom_id)
        if not doc:
            continue

        content = doc["content"]

        # Check if document might have exceeded context limits
        word_count = len(content.split())
        if word_count > 5000:
            # Chunk the document — only process the first half on retry
            mid_point = len(content) // 2
            content = content[:mid_point] + "\n\n[Document truncated to fit context limit]"
            print(f"  Chunking {custom_id}: {word_count} words → {len(content.split())} words")

        retry_requests.append({
            "custom_id": f"{custom_id}-retry",  # Append -retry to distinguish from original
            "params": {
                "model": BATCH_MODEL,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": f"Extract data:\n{content[:2000]}"}],
            },
        })

    return retry_requests


# ─── SLA calculation ───────────────────────────────────────────────────────────

def calculate_batch_frequency(sla_hours: int, batch_max_hours: int = 24) -> dict:
    """
    Given an SLA, calculate how frequently you need to submit batches.

    Example from exam: 30-hour SLA with 24-hour batch processing
    → Must submit every 6 hours (30 - 24 = 6 hour buffer)
    """
    buffer_hours = sla_hours - batch_max_hours

    if buffer_hours <= 0:
        return {
            "viable": False,
            "reason": f"SLA ({sla_hours}h) is less than batch processing time ({batch_max_hours}h)",
            "recommendation": "Use synchronous API instead",
        }

    return {
        "viable": True,
        "submission_frequency_hours": buffer_hours,
        "explanation": (
            f"Submit every {buffer_hours} hours. "
            f"Worst case: submitted at hour 0, processed at hour {batch_max_hours}, "
            f"within {sla_hours}h SLA."
        ),
        "submission_schedule": [
            f"Submit at: {h}:00" for h in range(0, 24, buffer_hours) if h + batch_max_hours <= sla_hours
        ],
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 4.5: Message Batches API — Batch Processing")
    print("=" * 60)

    show_batch_vs_sync_decision()

    print("=== SLA Calculation Examples ===\n")

    print("30-hour SLA, 24h batch max:")
    print(json.dumps(calculate_batch_frequency(30), indent=2))

    print("\n12-hour SLA, 24h batch max:")
    print(json.dumps(calculate_batch_frequency(12), indent=2))

    print("\n48-hour SLA, 24h batch max:")
    print(json.dumps(calculate_batch_frequency(48), indent=2))

    print("\n=== Batch Request Structure ===\n")
    sample_docs = [
        {"id": "doc-001", "content": "INVOICE #001\nVendor: Acme Corp\nTotal: $500.00"},
        {"id": "doc-002", "content": "INVOICE #002\nVendor: Widget Inc\nTotal: $1,250.00"},
    ]

    requests = create_batch_requests(sample_docs)
    print("Sample batch requests (not submitted — would cost money):")
    for req in requests:
        print(f"  custom_id: {req['custom_id']}")
        print(f"  model: {req['params']['model']}")
        print(f"  messages: {len(req['params']['messages'])} message(s)")

    print("\n=== Failure Handling Pattern ===\n")
    sample_failed = ["doc-003"]
    sample_docs_map = {
        "doc-003": {"content": "Very long document " * 3000}  # Would exceed context
    }
    retry_requests = handle_failed_requests(sample_failed, sample_docs_map)
    print(f"Generated {len(retry_requests)} retry requests (with chunking)")

    print("\n" + "=" * 60)
    print("Key: Batch API = 50% savings, up to 24h, no SLA guarantee.")
    print("Pre-merge checks → sync API. Overnight reports → batch API.")


if __name__ == "__main__":
    main()
