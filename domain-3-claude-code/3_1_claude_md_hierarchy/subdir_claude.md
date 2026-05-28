# Example: Subdirectory CLAUDE.md (applies to this directory and below)

> **Exam Key:** Place in a subdirectory to apply ONLY when working in that directory.
> This applies to: src/payments/ and all files below it.
> The project-level CLAUDE.md still applies (inherited from parent).
> Directory-level adds ON TOP of project-level rules.

## Payments Module — Specific Conventions

This directory contains PCI-DSS sensitive code. Additional rules apply:

## Security Rules (Payments-Specific)

- NEVER log credit card numbers, CVVs, or full PANs
- Only log last 4 digits: `card_number[-4:]`
- All payment operations must be wrapped in transactions
- Stripe API calls must use idempotency keys

## Stripe Integration

- Use `stripe.PaymentIntent.create()` — never direct charge
- Test mode key: `sk_test_...` (loaded from env, never hardcoded)
- Webhook validation: always verify Stripe signature

## Code Review Checklist for This Directory

Before submitting any PR touching this directory:
- [ ] No card data in logs
- [ ] Idempotency key present on all Stripe calls
- [ ] Transaction wrapping on multi-step operations
- [ ] Webhook signature validation tested

---

**WHY DIRECTORY-LEVEL (vs PROJECT-LEVEL):**
These rules are specific to payments processing and shouldn't clutter
the root CLAUDE.md. Directory-level keeps conventions scoped to where they apply.

Contrast with path rules (.claude/rules/): directory CLAUDE.md applies to a directory tree;
path rules (with glob patterns) can apply to files SCATTERED across the repo (e.g., all test files).
