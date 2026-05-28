"""
Task Statement 5.5: Design human review workflows and confidence calibration

Key concepts:
- Aggregate 97% accuracy may mask poor performance on specific segments
- Stratified random sampling of high-confidence extractions for error rate measurement
- Field-level confidence scores calibrated using labeled validation sets
- Validate accuracy by document type AND field before reducing human review
- Route by confidence + document ambiguity to prioritize limited reviewer capacity
"""

import json
import os
import random
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Extraction with field-level confidence scores ─────────────────────────────

EXTRACTION_WITH_CONFIDENCE_TOOL = {
    "name": "extract_with_confidence",
    "description": (
        "Extract invoice data and provide a confidence score (0.0-1.0) for EACH field. "
        "Confidence = how certain you are the extracted value is correct. "
        "Low confidence (< 0.7) when: handwritten text, ambiguous format, conflicting signals."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {"type": ["string", "null"]},
            "vendor_name_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "total_amount": {"type": ["number", "null"]},
            "total_amount_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "invoice_date": {"type": ["string", "null"]},
            "invoice_date_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "document_type": {
                "type": "string",
                "enum": ["invoice", "receipt", "statement", "quote", "unclear"],
            },
            "document_type_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "overall_confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Overall extraction confidence (min of all field confidences)",
            },
            "ambiguity_notes": {
                "type": ["string", "null"],
                "description": "Describe any ambiguous aspects that lowered confidence",
            },
        },
        "required": ["vendor_name_confidence", "total_amount_confidence", "overall_confidence", "document_type"],
    },
}


def extract_with_confidence(document: str) -> Optional[dict]:
    """Extract data with field-level confidence scores."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=[EXTRACTION_WITH_CONFIDENCE_TOOL],
        tool_choice={"type": "tool", "name": "extract_with_confidence"},
        messages=[{"role": "user", "content": f"Extract data:\n\n{document}"}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return None


# ─── Review routing logic ──────────────────────────────────────────────────────

CONFIDENCE_THRESHOLDS = {
    "auto_approve": 0.90,    # Route to auto-processing (no human review)
    "low_priority_review": 0.75,  # Review but not urgent
    "high_priority_review": 0.60,  # Needs prompt human review
    "reject_for_review": 0.0,  # Always needs human review (< high_priority_review)
}


def route_extraction(extraction: dict) -> dict:
    """
    Route an extraction to the appropriate review queue based on confidence.

    Limited human reviewer capacity → prioritize by confidence + document type.
    """
    overall = extraction.get("overall_confidence", 0)
    doc_type = extraction.get("document_type", "unclear")
    ambiguity = extraction.get("ambiguity_notes")

    # Document type affects routing
    is_ambiguous_type = doc_type == "unclear"
    has_ambiguity = bool(ambiguity)

    if overall >= CONFIDENCE_THRESHOLDS["auto_approve"] and not is_ambiguous_type:
        return {
            "route": "auto_process",
            "priority": None,
            "reason": f"High confidence ({overall:.2f}), clear document type",
        }

    elif overall >= CONFIDENCE_THRESHOLDS["low_priority_review"]:
        priority = "high" if (is_ambiguous_type or has_ambiguity) else "low"
        return {
            "route": "human_review",
            "priority": priority,
            "reason": f"Moderate confidence ({overall:.2f})" + (
                f" + ambiguity: {ambiguity[:50]}" if has_ambiguity else ""
            ),
        }

    else:
        return {
            "route": "human_review",
            "priority": "urgent",
            "reason": f"Low confidence ({overall:.2f}) — needs careful review",
        }


# ─── Stratified sampling for accuracy measurement ─────────────────────────────

def stratified_sample_audit(
    extractions: list[dict],
    sample_rate_high_confidence: float = 0.05,
    sample_rate_low_confidence: float = 1.0,
) -> list[dict]:
    """
    Stratified random sampling for ongoing error rate measurement.

    Why: Aggregate 97% accuracy can mask 0% accuracy on specific segments.
    Need to sample high-confidence extractions to detect novel error patterns.

    Sample rates:
    - High confidence: 5% random sample (catch drift and novel patterns)
    - Low confidence: 100% (already going to human review)
    - Specific document types: higher sample rate for known-problematic types
    """
    audit_queue = []

    for extraction in extractions:
        confidence = extraction.get("overall_confidence", 0)
        doc_type = extraction.get("document_type", "unclear")

        # Low confidence → always audit
        if confidence < 0.80:
            audit_queue.append({**extraction, "audit_reason": "low_confidence"})

        # High confidence → random sample to catch drift
        elif random.random() < sample_rate_high_confidence:
            audit_queue.append({**extraction, "audit_reason": "stratified_sample"})

        # Problematic document types → higher sample rate
        elif doc_type in ["statement", "unclear"] and random.random() < 0.20:
            audit_queue.append({**extraction, "audit_reason": "problematic_doc_type_sample"})

    return audit_queue


# ─── Segment accuracy analysis ────────────────────────────────────────────────

def analyze_accuracy_by_segment(results: list[dict]) -> dict:
    """
    Analyze accuracy by document type and field to identify hidden failures.

    Aggregate accuracy (97%) is misleading if one segment performs at 50%.
    """
    by_doc_type = {}
    by_field = {"vendor_name": [], "total_amount": [], "invoice_date": []}

    for r in results:
        doc_type = r.get("document_type", "unknown")
        if doc_type not in by_doc_type:
            by_doc_type[doc_type] = {"correct": 0, "total": 0}

        # Simulate accuracy check (in production: compare to labeled ground truth)
        is_correct = r.get("simulated_correct", True)
        by_doc_type[doc_type]["total"] += 1
        if is_correct:
            by_doc_type[doc_type]["correct"] += 1

        # Field-level confidence as proxy for accuracy
        for field in by_field.keys():
            conf_key = f"{field}_confidence"
            if conf_key in r:
                by_field[field].append(r[conf_key])

    segment_accuracies = {}
    for doc_type, counts in by_doc_type.items():
        if counts["total"] > 0:
            segment_accuracies[doc_type] = {
                "accuracy": counts["correct"] / counts["total"],
                "sample_size": counts["total"],
            }

    field_confidence_averages = {
        field: sum(scores) / len(scores) if scores else None
        for field, scores in by_field.items()
    }

    return {
        "segment_accuracies": segment_accuracies,
        "field_confidence_averages": field_confidence_averages,
        "flag_low_segments": [
            (doc_type, data["accuracy"])
            for doc_type, data in segment_accuracies.items()
            if data["accuracy"] < 0.90
        ],
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.5: Human Review Workflows and Confidence Calibration")
    print("=" * 60)

    test_documents = [
        ("Clear invoice", "INVOICE #001\nAcme Corp\nTotal: $500.00\nDate: 2025-05-28"),
        ("Ambiguous doc", "Statement of Account\nTotal Balance: $1,250\nDue: see attached"),
        ("Handwritten note", "reciept from store for stuff bought = about $45 (approx)"),
    ]

    print("\n=== Extraction with Field-Level Confidence ===\n")
    extractions = []
    for label, doc in test_documents:
        print(f"Document: {label}")
        extraction = extract_with_confidence(doc)
        if extraction:
            print(f"  Overall confidence: {extraction.get('overall_confidence', 'N/A'):.2f}")
            print(f"  Document type: {extraction.get('document_type', 'N/A')}")
            routing = route_extraction(extraction)
            print(f"  Routing: {routing['route']} (priority: {routing['priority']})")
            print(f"  Reason: {routing['reason'][:80]}")
            extraction["simulated_correct"] = extraction.get("overall_confidence", 0) > 0.8
            extractions.append(extraction)
        print()

    print("\n=== Stratified Sampling for Audit ===\n")
    # Simulate 100 extractions
    synthetic = [
        {"overall_confidence": random.uniform(0.6, 0.99), "document_type": random.choice(["invoice", "receipt", "statement"]),
         "vendor_name_confidence": random.uniform(0.7, 0.99), "total_amount_confidence": random.uniform(0.6, 0.99),
         "invoice_date_confidence": random.uniform(0.5, 0.99), "simulated_correct": random.random() > 0.05}
        for _ in range(100)
    ]
    audit_queue = stratified_sample_audit(synthetic)
    print(f"100 extractions → {len(audit_queue)} selected for audit ({len(audit_queue)}%)")
    reasons = {}
    for item in audit_queue:
        r = item.get("audit_reason", "unknown")
        reasons[r] = reasons.get(r, 0) + 1
    print(f"By reason: {reasons}")

    print("\n=== Segment Accuracy Analysis ===\n")
    analysis = analyze_accuracy_by_segment(synthetic)
    print("Accuracy by document type:")
    for doc_type, data in analysis["segment_accuracies"].items():
        print(f"  {doc_type}: {data['accuracy']:.0%} (n={data['sample_size']})")
    if analysis["flag_low_segments"]:
        print(f"\n⚠ Low-accuracy segments: {analysis['flag_low_segments']}")
        print("  Action: increase human review for these segments before automating")


if __name__ == "__main__":
    main()
