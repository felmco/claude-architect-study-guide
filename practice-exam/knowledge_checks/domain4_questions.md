# Domain 4 Knowledge Check — Prompt Engineering & Structured Output (20%)

10 self-test questions. Answers at the bottom.

---

**Q1.** Your code review prompt says "Only report issues you are highly confident about." After several weeks, developers report that real security vulnerabilities are still being flagged alongside a high rate of false positives for a particular category. What is the most effective fix?

A) Lower the confidence threshold from "high" to "medium"  
B) Add more detailed few-shot examples showing the types of issues to report  
C) Replace the vague confidence instruction with explicit categorical criteria that define exactly which patterns to flag and which to skip  
D) Ask the model to rate each finding 1-10 and filter out anything below 7  

---

**Q2.** You want to guarantee that Claude calls your `extract_invoice` tool rather than responding in prose. Which `tool_choice` configuration achieves this?

A) `{"type": "auto"}`  
B) `{"type": "any"}`  
C) `{"type": "tool", "name": "extract_invoice"}`  
D) `{"type": "none"}`  

---

**Q3.** Your extraction tool has a required `invoice_number` field in its JSON schema. You notice the model frequently invents invoice numbers when they're not present in the document. What schema change fixes this?

A) Add an `example` field to help the model understand the format  
B) Change `invoice_number` from required with type `"string"` to optional with type `["string", "null"]`  
C) Add a stricter regex pattern to the field  
D) Move `invoice_number` to a nested object to isolate it  

---

**Q4.** After implementing tool_use extraction with a strict JSON schema, you notice values that don't sum correctly: `line_items` add up to $195 but `total_amount` says $220. The model isn't making JSON syntax errors. What type of error is this and how do you address it?

A) This is a schema syntax error — tighten the JSON schema constraints  
B) This is a semantic validation error — JSON schema ensures syntax but not semantic consistency; add programmatic post-extraction validation (e.g., compare `line_items_subtotal` to `total_amount`)  
C) This is a model hallucination — use a larger model  
D) This is a temperature issue — lower temperature to 0 for extraction tasks  

---

**Q5.** You use the Message Batches API to process 500 invoice documents overnight. In the morning, 12 documents failed with `"error_type": "overloaded"` and 8 failed with context limit errors. What is the correct handling strategy?

A) Resubmit all 500 documents as a new batch  
B) Resubmit only the 12 `"overloaded"` failures unchanged; for the 8 context limit errors, chunk the documents before resubmitting — identify each by `custom_id`  
C) Resubmit all 20 failed documents unchanged, as transient errors often resolve themselves  
D) Switch to the synchronous API for all 500 documents to avoid batch failures  

---

**Q6.** Your code review prompt uses few-shot examples that demonstrate 4 clear bugs. After deployment, you notice the model consistently flags a common `async/await` pattern in your codebase as a bug, even though it's an accepted convention. How do you fix this with few-shot examples?

A) Add more examples of real bugs to crowd out the false positive  
B) Add a few-shot example that explicitly shows the accepted `async/await` pattern alongside a label of "NOT a bug — accepted convention in this codebase"  
C) Remove all few-shot examples and rely on detailed textual instructions  
D) Add a negative example that shows what NOT to report, but only for this specific pattern  

---

**Q7.** A developer proposes running a nightly batch that generates test cases for every changed file in the repository. The same pipeline also includes pre-merge checks that block PRs until Claude reviews them. She suggests using the Message Batches API for both. What should you tell her?

A) Both workflows are appropriate for the Batch API since they both run automatically  
B) The Batch API is fine for both as long as you poll frequently enough  
C) Use the Batch API for the nightly test generation (non-blocking, latency-tolerant); keep synchronous API for pre-merge checks (blocking — developers wait for the result)  
D) Use the Batch API for pre-merge checks to save costs, and the synchronous API for nightly jobs for reliability  

---

**Q8.** When you retry a failed extraction, you send: `"Here is the original document and the previous extraction. Please fix the errors: [document] [extraction] [error message]"`. The retry still returns the same incorrect value. Under what condition will this pattern NEVER succeed regardless of how many retries you attempt?

A) When the model's temperature is too high  
B) When the required information simply does not exist in the source document — retrying cannot invent data that isn't there  
C) When the JSON schema is too strict  
D) When the error message is too long  

---

**Q9.** You are reviewing a 20-file PR. After running a single-pass analysis, you get contradictory findings: one file's use of `Promise.all` is flagged as a concurrency risk, while an identical pattern in another file gets no comment. What is the structural cause and how do you fix it?

A) The model is non-deterministic — run the same pass multiple times and take the consensus  
B) Single-pass analysis on many files causes attention dilution — split into focused per-file local passes plus a separate cross-file integration pass  
C) Use a higher-tier model that can hold more context  
D) Reduce the PR size requirement to 5 files maximum  

---

**Q10.** Your team generates a weekly technical debt report that takes about 3 hours to process 800 files. A developer suggests switching to the Message Batches API to cut costs. Another developer objects, saying "batch results arrive in random order." Who is correct and why?

A) The objector is right — batch results are not ordered and cannot be matched to inputs  
B) The first developer is right — batch results are returned unordered but each result includes a `custom_id` that matches it to the original request, enabling correlation regardless of arrival order  
C) Both are partially right — use the Batch API only if you process files alphabetically  
D) The objector is right — use the synchronous API to guarantee result ordering  

---

## Answers

1. **C** — Vague confidence instructions don't improve precision. Explicit categorical criteria (flag SQL injection, skip naming style) tell the model exactly what to report, independent of confidence.

2. **C** — Forced tool selection `{"type": "tool", "name": "extract_invoice"}` guarantees that specific tool is called. `"any"` (B) guarantees a tool call but lets the model choose which one.

3. **B** — Making the field optional (`["string", "null"]`) allows the model to return `null` when the value isn't in the document, instead of fabricating one. Required fields pressure the model to invent values.

4. **B** — Strict JSON schema eliminates syntax errors (malformed JSON) but cannot enforce semantic consistency (values must sum correctly). Programmatic post-extraction validation is required for semantic checks.

5. **B** — Resubmit only failed documents identified by `custom_id` — never the whole batch. `"overloaded"` errors are transient and can be resubmitted unchanged. Context limit errors need the document chunked before resubmission.

6. **B** — Few-shot examples work for negative cases too. An explicit "NOT a bug" example for the accepted pattern teaches the model to generalize the distinction, not just memorize the one pattern.

7. **C** — Pre-merge checks are blocking (developer waits) → synchronous API required. Nightly test generation is non-blocking and latency-tolerant → Batch API is appropriate for the 50% cost savings.

8. **B** — Retries with error feedback succeed when the error is a formatting or structural issue the model can fix. When the required information doesn't exist in the source document, no amount of retrying will produce it — the correct fix is making the field nullable.

9. **B** — Attention dilution on 20 files causes inconsistent depth and contradictory findings. Splitting into per-file local passes (consistent depth per file) plus a cross-file integration pass (catches data flow issues) is the correct architecture. Exam Q12.

10. **B** — The first developer is right. Batch results are unordered but each result contains the `custom_id` from the original request. Correlation by `custom_id` is the designed mechanism — result ordering is not a concern.
