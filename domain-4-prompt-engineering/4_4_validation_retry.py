"""
Task Statement 4.4: Implement validation, retry, and feedback loops

Key concepts:
- Retry-with-error-feedback: append specific errors to prompt on retry
- When retries succeed: format mismatches, structural errors
- When retries FAIL: information simply absent from source document
- detected_pattern field for tracking false positive sources
- calculated_total vs stated_total for semantic discrepancy detection
"""

import json
import os
from typing import Optional, Any
from dotenv import load_dotenv
import anthropic
from pydantic import BaseModel, Field, field_validator, model_validator

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")

MAX_RETRIES = 2


# ─── Pydantic models for validation ───────────────────────────────────────────

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

    @field_validator("total")
    @classmethod
    def total_must_match(cls, v, info):
        if "quantity" in info.data and "unit_price" in info.data:
            expected = info.data["quantity"] * info.data["unit_price"]
            if abs(v - expected) > 0.01:
                raise ValueError(
                    f"Line item total ${v:.2f} does not match "
                    f"quantity ({info.data['quantity']}) × price (${info.data['unit_price']:.2f}) = ${expected:.2f}"
                )
        return v


class InvoiceExtraction(BaseModel):
    vendor_name: str
    invoice_number: Optional[str] = None
    total_amount: float
    stated_subtotal: Optional[float] = None  # What the document claims the subtotal is
    calculated_subtotal: Optional[float] = None  # Sum of line items (we compute this)
    line_items: Optional[list[LineItem]] = None
    currency: str = "USD"
    conflict_detected: bool = False  # True when stated vs calculated totals disagree

    @model_validator(mode="after")
    def check_semantic_consistency(self) -> "InvoiceExtraction":
        """Semantic validation: do numbers add up?"""
        if self.line_items:
            calc = sum(item.total for item in self.line_items)
            self.calculated_subtotal = round(calc, 2)

            if self.stated_subtotal and abs(self.stated_subtotal - calc) > 0.01:
                self.conflict_detected = True

        return self


# ─── Extraction tool ───────────────────────────────────────────────────────────

EXTRACT_TOOL = {
    "name": "extract_invoice_data",
    "description": "Extract invoice data with line items. Compute stated_subtotal from document text and line_items from individual entries.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "invoice_number": {"type": ["string", "null"]},
            "total_amount": {"type": "number"},
            "stated_subtotal": {"type": ["number", "null"]},
            "line_items": {
                "type": ["array", "null"],
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"},
                    },
                    "required": ["description", "quantity", "unit_price", "total"],
                },
            },
            "currency": {"type": "string", "default": "USD"},
        },
        "required": ["vendor_name", "total_amount"],
    },
}


# ─── Extraction with retry ─────────────────────────────────────────────────────

def extract_with_retry(document: str) -> tuple[Optional[InvoiceExtraction], list[str]]:
    """
    Extract invoice data with validation-retry loop.

    Returns: (validated_result_or_None, list_of_errors_encountered)

    On retry: include original doc + failed extraction + specific errors.
    This guides the model toward correct extraction on the next attempt.
    """
    errors_log = []
    messages = [{
        "role": "user",
        "content": f"Extract structured invoice data from this document:\n\n{document}",
    }]

    for attempt in range(MAX_RETRIES + 1):
        print(f"\n  Extraction attempt {attempt + 1}/{MAX_RETRIES + 1}")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_invoice_data"},
            messages=messages,
        )

        raw_data = None
        for block in response.content:
            if block.type == "tool_use":
                raw_data = block.input
                break

        if raw_data is None:
            errors_log.append("No tool call made")
            continue

        # Pydantic validation
        try:
            result = InvoiceExtraction(**raw_data)
            print(f"  ✓ Validation passed on attempt {attempt + 1}")

            # Check for semantic conflicts (not caught by schema)
            if result.conflict_detected:
                print(f"  ⚠ Semantic conflict: stated subtotal ≠ calculated subtotal")
                print(f"    Stated: ${result.stated_subtotal}, Calculated: ${result.calculated_subtotal}")

            return result, errors_log

        except Exception as e:
            error_msg = str(e)
            errors_log.append(f"Attempt {attempt + 1}: {error_msg}")
            print(f"  ✗ Validation failed: {error_msg[:100]}")

            if attempt < MAX_RETRIES:
                # Retry with error feedback — key pattern
                # Include: original doc + failed extraction + specific errors
                retry_content = f"""The previous extraction had validation errors. Please fix them.

ORIGINAL DOCUMENT:
{document}

PREVIOUS EXTRACTION (with errors):
{json.dumps(raw_data, indent=2)}

SPECIFIC VALIDATION ERRORS:
{error_msg}

Fix these specific issues and return corrected extraction."""

                # Append to conversation for context
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": retry_content})

    print(f"  ✗ All {MAX_RETRIES + 1} attempts failed")
    return None, errors_log


# ─── When retries will and won't help ─────────────────────────────────────────

def demonstrate_retry_limitations():
    """
    Shows two cases:
    1. Retry succeeds: format mismatch (model can fix with feedback)
    2. Retry fails: information simply absent (no amount of retrying helps)
    """
    print("\n=== When Retries Succeed vs When They Don't ===\n")

    print("SUCCEEDS: Format mismatch — model can fix with feedback")
    print("  Error: 'total must be a number, got string \"$1,250.00\"'")
    print("  Retry feedback: 'total_amount should be numeric (1250.00), not string'")
    print("  Result: Model returns 1250.00 on next attempt ✓")
    print()

    print("SUCCEEDS: Structural error — model can restructure with feedback")
    print("  Error: 'line_items must be array, got single object'")
    print("  Retry feedback: 'line_items should be a list even if only one item'")
    print("  Result: Model wraps in list on next attempt ✓")
    print()

    print("FAILS: Information absent from source")
    print("  Error: 'invoice_number is required but None'")
    print("  Document: Simple invoice with no invoice number")
    print("  Retry feedback: Doesn't help — the information doesn't exist in the document")
    print("  Resolution: Make invoice_number optional (nullable) OR route to human review")
    print()

    print("KEY INSIGHT: Before retrying, ask 'Is the information in the source?'")
    print("If yes → retry with feedback. If no → fix schema (nullable) or human review.")


# ─── detected_pattern field for false positive tracking ───────────────────────

def demonstrate_detected_pattern_tracking():
    """
    Adding detected_pattern field to findings enables systematic analysis
    of which code constructs trigger dismissals.
    """
    print("\n=== detected_pattern Field for False Positive Tracking ===\n")

    finding_schema = {
        "name": "report_code_finding",
        "description": "Report a code issue found during review",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "issue": {"type": "string"},
                "file": {"type": "string"},
                "line": {"type": "number"},
                "suggested_fix": {"type": "string"},
                # KEY: detected_pattern enables false positive analysis
                "detected_pattern": {
                    "type": "string",
                    "description": (
                        "The specific code pattern that triggered this finding. "
                        "E.g., 'f-string in SQL query', 'bare except clause', "
                        "'mutable default argument'. Used to analyze which patterns "
                        "generate high false-positive rates."
                    ),
                },
            },
            "required": ["severity", "issue", "file", "line", "detected_pattern"],
        },
    }

    example_finding = {
        "severity": "high",
        "issue": "Potential SQL injection via f-string",
        "file": "src/queries.py",
        "line": 42,
        "suggested_fix": "Use parameterized queries",
        "detected_pattern": "f-string in db.execute() call",  # ← trackable
    }

    print("Finding with detected_pattern field:")
    print(json.dumps(example_finding, indent=2))
    print()
    print("When developers dismiss this finding, the pattern 'f-string in db.execute()'")
    print("can be analyzed: 'Is this pattern causing 80% dismissals in our codebase?'")
    print("If yes → add few-shot example showing when f-strings in SQL ARE acceptable")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 4.4: Validation-Retry Loops with Error Feedback")
    print("=" * 60)

    # Test 1: Valid invoice (should pass on first attempt)
    print("\n--- Test 1: Valid invoice ---")
    valid_invoice = """
    INVOICE #INV-2025-042
    Vendor: Acme Corp

    Line Items:
    - Widget A × 10 units @ $12.50 = $125.00
    - Widget B × 5 units @ $24.99 = $124.95

    Subtotal: $249.95
    Tax (8%): $20.00
    Total Due: $269.95
    """
    result, errors = extract_with_retry(valid_invoice)
    if result:
        print(f"Vendor: {result.vendor_name}")
        print(f"Total: ${result.total_amount}")
        print(f"Conflict detected: {result.conflict_detected}")
    print(f"Errors: {errors}")

    demonstrate_retry_limitations()
    demonstrate_detected_pattern_tracking()


if __name__ == "__main__":
    main()
