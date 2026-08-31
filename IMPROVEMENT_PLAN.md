# AEGIS Improvement & Testing Plan

> Comprehensive plan to improve every aspect of the system, ensure MiniMax LLM works correctly, and run an extensive testing campaign.

---

## Phase 1: Audit Current State (✅ Done)

### Findings

#### Ghost Pages Found
- `/analytics` — 404 (sidebar parent nav with no page)
- `/analytics/evaluation` — empty body (data fetch failing)
- `/analytics/benchmark` — empty body (data fetch failing)

#### Broken Backend Endpoints
- `/v3/evaluation/history` — 500 error (SQLite path issue on Vercel read-only fs)
- `/v3/evaluation/trends` — likely same issue
- `/v3/evaluation/report/{id}` — likely same issue
- `/v3/evaluation/synthetic-benchmark` — likely same issue

#### Working Endpoints ✅
- `/health` ✅
- `/metrics` ✅
- `/metrics/agents` ✅
- `/v1/patients` ✅
- `/v1/patients/{id}` ✅
- `/v1/investigations` (POST) ✅ — returns real LLM results
- `/v1/traces` ✅
- `/v1/stats` ✅
- `/v1/compliance` ✅
- `/v2/agents` ✅
- `/v2/tools` ✅
- `/v2/investigations` (POST) ✅

#### LLM Verification ✅
- MiniMax-M3 is working — investigations return real LLM-generated conclusions
- 4/4 agents complete successfully
- Confidence scores calculated
- Evidence tracked

---

## Phase 2: Critical Fixes (P0)

### 2.1 Fix SQLite Path on Vercel
- **Problem**: `Path.home() / ".aegis" / "evaluation.db"` fails on Vercel (read-only fs)
- **Fix**: Use `/tmp` on Vercel, or use a writable directory
- **Files**: `backend/src/aegis/evaluation_extensions.py`, `backend/src/aegis/db.py`

### 2.2 Fix Analytics Ghost Pages
- **Problem**: `/analytics` returns 404
- **Fix**: Create `web/app/(dashboard)/analytics/page.tsx` with overview
- **Files**: `web/app/(dashboard)/analytics/page.tsx` (create)

### 2.3 Fix Empty Analytics Pages
- **Problem**: `/analytics/evaluation` and `/analytics/benchmark` show empty bodies
- **Fix**: Either fix the data loading or add proper empty states
- **Files**: `web/app/(dashboard)/analytics/evaluation/page.tsx`, `benchmark/page.tsx`

### 2.4 Fix NaN/Serialization Issues
- **Problem**: Some endpoints return NaN values
- **Fix**: Comprehensive `_clean_nan_values` on all data responses
- **Files**: `backend/src/aegis/api.py`

---

## Phase 3: LLM Improvements (P1)

### 3.1 Real LLM Integration Audit
- Verify each agent actually calls MiniMax API
- Add request/response logging
- Track token usage per agent
- Track costs

### 3.2 LLM Error Handling
- Add timeouts (current: none)
- Add better fallback to mock when API fails
- Better error messages

### 3.3 Structured Output Improvements
- Verify all agents return valid JSON
- Add validation
- Better retry logic

### 3.4 LLM Call Monitoring
- Add `/v2/llm/usage` endpoint
- Log all LLM calls
- Track success/failure rates

---

## Phase 4: Testing Campaign (P0)

### 4.1 Backend Endpoint Tests
Test every endpoint with curl, verify:
- [ ] Returns 2xx for valid requests
- [ ] Returns 4xx for invalid input
- [ ] Returns valid JSON shape
- [ ] No NaN/Infinity values
- [ ] Auth works correctly

### 4.2 Frontend Page Tests
Test every page route:
- [ ] Loads without error
- [ ] All components render
- [ ] Navigation works
- [ ] Empty states show
- [ ] Loading states show
- [ ] Error states show

### 4.3 Integration Tests
- [ ] Frontend → Backend → MiniMax flow works end-to-end
- [ ] SSE streaming works
- [ ] WebSocket works
- [ ] Auth flow works

### 4.4 LLM Quality Tests
- [ ] Each agent produces coherent output
- [ ] Confidence scores are reasonable
- [ ] Evidence is properly cited
- [ ] Safety gates block bad queries

---

## Phase 5: Improvements (P2)

### 5.1 Performance
- Add response caching
- Optimize database queries
- Lazy load components
- Add request batching

### 5.2 UX
- Better loading skeletons
- Better error messages
- Toast notifications
- Optimistic updates

### 5.3 Monitoring
- Add Sentry-style error tracking
- Add performance monitoring
- Add usage analytics

### 5.4 Documentation
- Add inline API docs
- Add troubleshooting guide
- Add development guide

---

## Phase 6: Long-term (P3)

### 6.1 Real Authentication
- Replace demo auth with proper JWT
- Add user roles
- Add OAuth support

### 6.2 Production Database
- PostgreSQL with pgvector
- Real embeddings
- Persistent storage

### 6.3 Advanced Features
- Multi-user collaboration
- Investigation history export
- Custom agent creation

---

## Testing Tools

### Backend
```bash
# Run all tests
pytest tests/

# Run endpoint smoke tests
python scripts/test_endpoints.py
```

### Frontend
```bash
cd web
npm test
npm run typecheck
npm run lint
```

### E2E (if added)
```bash
npx playwright test
```

---

## Success Criteria

A change is "complete" when:
1. All endpoints respond correctly
2. All pages render without errors
3. LLM produces real, coherent results
4. No ghost pages / broken links
5. No 500 errors on valid requests
6. Loading/empty/error states all work
7. Logs are clean (no errors in normal operation)