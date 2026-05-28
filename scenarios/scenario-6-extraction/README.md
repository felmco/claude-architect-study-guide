# Scenario 6: Structured Data Extraction

**Primary Domains:** 4 (Prompt Engineering), 5 (Context & Reliability)

**Exam questions:** Based on Scenario 6 questions (not in the 12 sample questions — scenarios are drawn randomly)

---

## The System

Document extraction pipeline:
- Forced tool_use extraction with nullable fields
- Pydantic validation + retry with error feedback
- Confidence-based human review routing
- Message Batches API for bulk processing

---

## Sequence Diagram: Extraction + Validation + Routing

```mermaid
sequenceDiagram
    participant App
    participant Claude
    participant Pydantic
    participant Queue

    App->>Claude: Extract(document, tool_choice=forced)
    Claude-->>App: tool_use{invoice_data}
    App->>Pydantic: validate(invoice_data)
    
    alt Validation passes
        Pydantic-->>App: InvoiceExtraction(validated)
        alt Confidence >= 0.90
            App->>Queue: auto_process queue
        else Confidence 0.70-0.89
            App->>Queue: human_review (low priority)
        else Confidence < 0.70
            App->>Queue: human_review (urgent)
        end
    else Validation fails
        Pydantic-->>App: ValidationError
        App->>Claude: Retry with: doc + failed_extraction + errors
        Claude-->>App: Corrected extraction
        App->>Pydantic: validate(corrected)
    end
```

---

## Files

| File | Purpose |
|------|---------|
| `extractor.py` | Tool_use extraction with nullable fields |
| `validator.py` | Pydantic validation + retry loop |
| `batch_processor.py` | Message Batches API bulk processing |
| `schemas/document_schema.json` | Full JSON schema |
