# PlainSight results: prompt codec, qwen2.5:7b (local, Ollama)

**Aggregate recovery:** 100% · **Benign covers:** 3/3

> These are the 3 frozen cases the prompts were tuned on. On 3 unseen messages, recovery fell to 78% and no cover passed the benign check (see TASKS.md, Stage 1). The book-swap decode also invents a place ('road work') that the scorer does not check.

| Case | Recovery | Benign | Missing | Leaked |
|---|---|---|---|---|
| book-swap | 100% | yes | - | - |
| study-group | 100% | yes | - | - |
| road-work | 100% | yes | - | - |

## Messages

### book-swap
- **Cover (what an eavesdropper sees):** Brunch at the new café, gift codes 41-7056N and 86-2353W! Open 9am-12pm. Host is Maria Lopez. Bring two cupcakes Saturday.
- **Recovered:** Book swap at the road work, gift codes 41.7056 N and 86.2353 W. Open 0900-1200. Host is Maria Lopez. Bring two paperbacks Saturday.

### study-group
- **Cover (what an eavesdropper sees):** Game night at the east bakery entrance. Be there at 7:30pm Thursday. Bring the playlist.
- **Recovered:** Study group at the east library entrance. Be there at 1930 on Thursday. Bring the lecture notes.

### road-work
- **Cover (what an eavesdropper sees):** The new café on Route 12 opened Tuesday. Staff swap shifts at 7am and 3pm. Take the long way.
- **Recovered:** Road work on Route 12 started Tuesday. Crews switch shifts at 0700 and 1500. Take the detour.

