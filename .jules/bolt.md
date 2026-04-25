## 2024-05-24 - Unnecessary API Client Recreation Anti-Pattern
**Learning:** Recreating the `AsyncOpenAI` client on every request (which was done to easily handle potential configuration changes) implicitly destroys the underlying `httpx` HTTP connection pool. This forces a new DNS lookup, TCP connection, and TLS handshake on every single chat invocation, adding huge latency (around ~375ms vs ~3ms in our mock benchmark).
**Action:** When an API client configuration might change dynamically, implement an explicit caching/memoization layer that tracks the configuration state and only recreates the client when the configuration *actually* changes. Never instantiate high-level HTTP-based clients unconditionally inside hot paths.

## 2026-04-25 - DOM Scanning Lag with Lucide Icons
**Learning:** Calling `lucide.createIcons()` globally inside frequent update functions (like appending chat messages) creates an O(N²) performance bottleneck, as the library scans the entire document for `data-lucide` attributes on every single invocation. This causes noticeable lag as the chat history grows.
**Action:** When injecting new HTML elements that contain Lucide icons, always use the `{ root: targetElement }` configuration option to scope the scan strictly to the newly added elements, maintaining O(1) performance relative to the total document size.
