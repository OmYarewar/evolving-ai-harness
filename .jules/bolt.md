## 2024-05-24 - Unnecessary API Client Recreation Anti-Pattern
**Learning:** Recreating the `AsyncOpenAI` client on every request (which was done to easily handle potential configuration changes) implicitly destroys the underlying `httpx` HTTP connection pool. This forces a new DNS lookup, TCP connection, and TLS handshake on every single chat invocation, adding huge latency (around ~375ms vs ~3ms in our mock benchmark).
**Action:** When an API client configuration might change dynamically, implement an explicit caching/memoization layer that tracks the configuration state and only recreates the client when the configuration *actually* changes. Never instantiate high-level HTTP-based clients unconditionally inside hot paths.

## 2026-04-25 - DOM Scanning Lag with Lucide Icons
**Learning:** Calling `lucide.createIcons()` globally inside frequent update functions (like appending chat messages) creates an O(N²) performance bottleneck, as the library scans the entire document for `data-lucide` attributes on every single invocation. This causes noticeable lag as the chat history grows.
**Action:** When injecting new HTML elements that contain Lucide icons, always use the `{ root: targetElement }` configuration option to scope the scan strictly to the newly added elements, maintaining O(1) performance relative to the total document size.

## 2026-04-26 - O(N) Serialization Bottleneck in Monolithic JSON Files
**Learning:** Saving the entire state of an application to a single `memory.json` file on every chat message creates an O(N) performance bottleneck. As the total size of all chat sessions combined grows, updating the JSON file introduces massive I/O and JSON serialization overhead, causing a noticeable UI lag during streaming and messaging on larger datasets (e.g., from <1ms per operation to ~100ms when handling 200 sessions).
**Action:** Transition away from monolithic state files when dealing with collections of discrete datasets. Instead, adopt a file-per-record storage model (e.g., `data/sessions/<session_id>.json`) where appending new data only triggers serialization and I/O for the specific affected record, resolving the bottleneck and retaining an O(1) performance profile.

## 2026-04-27 - Security vs Formatting with DOMPurify
**Learning:** Using `DOMPurify.sanitize` is necessary to prevent XSS vulnerabilities, particularly from dynamically parsed user input or third-party interactions. However, when formatting complex internal tool structures manually via HTML (e.g. `<details>` and `<summary>`), `DOMPurify` might strip out tags if they are not explicitly permitted via `ADD_TAGS`, breaking intended UI structures.
**Action:** Always ensure that when manually building safe internal HTML structures using semantic tags, you pass `ADD_TAGS` arrays to `DOMPurify` (e.g. `{ADD_TAGS: ['details', 'summary']}`) to preserve functional layouts without compromising security against malicious payloads.
