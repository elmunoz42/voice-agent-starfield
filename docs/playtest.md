# Playtest Scenarios - AstroLB-3

## Test Scenarios

### M0 - Basic Voice Loop
- [ ] Console mode voice conversation (30 seconds)
- [ ] Voice detection and turn-taking
- [ ] Response latency under 3 seconds
- [ ] AstroLB-3 responds when addressed by name

### M1 - Knowledge Base
- [ ] Knowledge question with answer verified against source
- [ ] "My records don't show that" response when info not in KB
- [ ] Search returns relevant chunks with source metadata
- [ ] Idempotent ingestion (re-running doesn't duplicate)

### M2 - Progress Journal
- [ ] Log progress and recall across sessions
- [ ] Greeting includes last goal and recent entries
- [ ] Spoiler filter blocks content above current level
- [ ] Setting spoiler level updates filtering

### M3 - Phone Deployment
- [ ] 30-minute session while playing Starfield
- [ ] Push-to-talk button works without looking
- [ ] No false triggers from game audio bleed
- [ ] End-of-speech to first-audio under 2 seconds
- [ ] Agent reconnects after phone screen lock

### M4 - Performance
- [ ] Laptop FPS unaffected with agent running alongside game
- [ ] Vector search completes in under 500ms
- [ ] Agent continues talking if vector store unreachable

---

## Observations

### 2026-10-22 - Project Created
**Status**: M0 built, not tested

- Created project structure
- Implemented basic voice agent with OpenAI STT/LLM/TTS
- AstroLB-3 system prompt written
- Dependencies pinned with uv.lock
- Console, dev, and start modes available

**Next**: Test console mode voice loop and verify latency

---

## Notes

- Only mark scenarios as checked after running them
- Record date, observed behavior, and any issues
- Include model configs used during tests
- Note environment (laptop, phone, cloud worker, etc.)
