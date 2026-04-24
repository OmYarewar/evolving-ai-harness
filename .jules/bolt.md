## 2024-05-24 - Unnecessary API Client Recreation Anti-Pattern
**Learning:** Recreating the `AsyncOpenAI` client on every request (which was done to easily handle potential configuration changes) implicitly destroys the underlying `httpx` HTTP connection pool. This forces a new DNS lookup, TCP connection, and TLS handshake on every single chat invocation, adding huge latency (around ~375ms vs ~3ms in our mock benchmark).
**Action:** When an API client configuration might change dynamically, implement an explicit caching/memoization layer that tracks the configuration state and only recreates the client when the configuration *actually* changes. Never instantiate high-level HTTP-based clients unconditionally inside hot paths.

## 2024-04-24 - O(N^2) DOM Scanning Anti-Pattern
**Learning:** Calling `lucide.createIcons()` globally without specifying a root element scans the entire DOM for elements with `data-lucide` attributes. When called inside functions that frequently append new elements (like chat messages), it causes O(N^2) complexity and severe lag as the document grows.
**Action:** Always scope `lucide.createIcons()` by passing a specific `{ root: targetElement }` configuration object pointing to the newly injected container instead of scanning the whole document.
