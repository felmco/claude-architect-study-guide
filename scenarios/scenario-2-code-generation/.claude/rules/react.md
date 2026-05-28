---
paths: ["src/components/**/*", "**/*.tsx", "**/*.jsx"]
---

# React Component Conventions

- Functional components only, no class components
- Custom hooks: prefix with `use`, return typed objects not arrays
- Avoid `useEffect` for data fetching — use React Query
- Memoize expensive renders with `React.memo`; avoid premature optimization
- Accessibility: every interactive element needs `aria-*` or semantic HTML
