---
paths: ["src/api/**/*", "*/handlers/**/*.py", "*/routes/**/*.py"]
---

# API Handler Conventions (auto-loaded for API files)

These rules apply ONLY when editing files in API/handler directories.

## Request Validation
- All endpoint handlers must validate input with Pydantic before processing
- Return 400 with field-level errors, not 500, for validation failures
- Never pass raw `request.body` to database queries

## Error Response Format
All API errors must return:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "field": "specific_field_if_applicable"
  }
}
```

## Authentication
- Check `request.user.is_authenticated` before any data access
- Log authentication failures with IP but NOT with credentials
- Rate limit: maximum 10 auth attempts per minute per IP

## Async Patterns
- All database calls must be `await`ed — never blocking in async handlers
- Use `asyncio.gather()` for parallel database queries
- Timeout: 30 seconds max per handler execution
