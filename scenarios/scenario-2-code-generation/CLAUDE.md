# Team Coding Standards — E-Commerce Platform

## React Components (functional style with hooks)
- Use functional components only — no class components
- State management: `useState` for local, Zustand for shared state
- Fetch data with `useQuery` (React Query) — no raw `fetch` in components
- Props: always define a TypeScript interface, never `any`

## API Handlers (async/await with structured error handling)
- All handlers are async functions
- Wrap handler body in try/catch; return `{error: ..., statusCode: N}` objects
- Log errors with `logger.error(err, {context: 'handler-name'})` — no `console.error`
- Validate request body with Zod before any business logic

## Database Models (repository pattern)
- All DB access goes through repository classes — no raw queries in handlers
- Repository methods return `Result<T, DbError>` — never throw
- Use transactions for operations that touch more than one table

@import .claude/rules/react.md
@import .claude/rules/api.md
@import .claude/rules/tests.md
