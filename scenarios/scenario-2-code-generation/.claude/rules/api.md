---
paths: ["src/api/**/*", "src/handlers/**/*", "src/routes/**/*"]
---

# API Handler Conventions

- All handlers are `async` functions
- Validate request body with Zod before any business logic
- Return `{data: T}` on success, `{error: string, code: string}` on failure
- Use `logger.error` not `console.error`
- Set appropriate HTTP status codes (400 for validation, 401 for auth, 500 for server)
