# Frontend Testing Campaign Results & Fix/Refine/Optimize Plan

## Date: 2026-08-30

---

## 1. Testing Campaign Summary

### Infrastructure Created

- **Framework**: Vitest 4.1 + React Testing Library + jsdom
- **Test files**: 18
- **Total tests**: 215 (all passing)
- **Setup files**: `vitest.config.ts`, `tests/setup.ts`
- **Scripts added**: `test`, `test:watch`, `test:coverage`

### Test Coverage Areas

| Category | Files | Tests | Status |
|----------|-------|-------|--------|
| Utility functions | 1 | 42 | PASS |
| API client | 1 | 18 | PASS |
| Zustand store | 1 | 4 | PASS |
| React Query keys | 1 | 24 | PASS |
| UI primitives (Button, Badge, Card, Input, Tabs, Dialog) | 6 | 53 | PASS |
| Investigation components | 2 | 13 | PASS |
| Patient components (PatientHeader, RiskDashboard, LabsChart, ClinicalTrialsTab, DrugInteractionsTab) | 5 | 38 | PASS |
| Search components | 1 | 7 | PASS |

### Build & Quality Status

| Check | Status | Details |
|-------|--------|---------|
| TypeScript | PASS | `tsc --noEmit` clean |
| Build | PASS | All 17 routes built successfully |
| Tests | PASS | 215/215 |
| ESLint | FAIL | 113 errors, 59 warnings |

---

## 2. Issues Found

### 2.1 ESLint Errors (113)

| Category | Count | Severity |
|----------|-------|----------|
| `@typescript-eslint/no-explicit-any` | ~75 | Medium |
| `@typescript-eslint/no-empty-object-type` | 12 | Low |
| `react-hooks/set-state-in-effect` | 3 | High |
| `react-hooks/refs` | 2 | High |
| `react-hooks/exhaustive-deps` | 2 | Medium |
| `react/no-unescaped-entities` | 3 | Low |
| `@next/next/no-img-element` | 1 | Low |

### 2.2 ESLint Warnings (59)

| Category | Count | Severity |
|----------|-------|----------|
| `@typescript-eslint/no-unused-vars` (imports) | ~45 | Low |
| `@typescript-eslint/no-unused-vars` (variables) | ~14 | Low |

### 2.3 Critical Runtime Issues

1. **Ref access during render** (`useSocket.ts:76`) - Components won't re-render on socket connect
2. **Cascading renders** (`Dialog.tsx:79`, `auth/context.tsx:40`, `settings/page.tsx:21`) - Performance degradation from setState in useEffect
3. **Missing hook dependencies** (`ThemeProvider.tsx:84`, `useSocket.ts:57`) - Potential stale closures

---

## 3. Fix, Refine & Optimize Plan

### P0 - Critical Bugs (Fix Immediately)

#### 3.1 `useSocket.ts:76` - Ref access during render

**File**: `lib/socket/useSocket.ts:76`

**Problem**: `socketRef.current` is accessed in the return statement, causing the component to not re-render when the socket connection state changes.

**Fix**: Use state for socket instance instead of ref, or expose via a callback pattern.

```typescript
// Before
return { socket: socketRef.current, connected, error, connect, disconnect, emit, on };

// After
const [socket, setSocket] = useState<Socket | null>(null);
// In connect: setSocket(newSocket);
return { socket, connected, error, connect, disconnect, emit, on };
```

#### 3.2 `Dialog.tsx:79` - setState in useEffect

**File**: `components/ui/Dialog.tsx:79`

**Problem**: `setMounted(true)` called synchronously in effect body causes cascading renders.

**Fix**: Use `useSyncExternalStore` or move to `useLayoutEffect`, or restructure to avoid the need for a mounted state.

#### 3.3 `auth/context.tsx:40` - setState in useEffect

**File**: `lib/auth/context.tsx:40`

**Problem**: `setUser(JSON.parse(storedUser))` in effect body causes unnecessary re-render.

**Fix**: Initialize state with localStorage value via lazy initializer:

```typescript
const [user, setUser] = useState<User | null>(() => {
  const stored = localStorage.getItem("aegis-user");
  return stored ? JSON.parse(stored) : defaultUser;
});
```

#### 3.4 `settings/page.tsx:21` - setState in useEffect

**File**: `app/(dashboard)/settings/page.tsx:21`

**Problem**: Same pattern as auth context.

**Fix**: Use lazy state initializer for `apiKey`.

---

### P1 - Type Safety (Fix This Sprint)

#### 3.5 Define proper API response types

**File**: `lib/api/client.ts` - 35 `any` return types

**Problem**: All Graph RAG, temporal, evaluation, and benchmark endpoints return `any`.

**Fix**: Define interfaces in `types/index.ts` for all API responses:

```typescript
// Add to types/index.ts
export interface GraphRAGEvidenceResponse {
  evidence: Array<{
    source_id: string;
    content: string;
    relevance_score: number;
    node_type: string;
    properties: Record<string, unknown>;
  }>;
  // ... etc
}

export interface TemporalAnomaliesResponse {
  anomalies: Array<{
    type: string;
    description: string;
    severity: number;
    timestamp: string;
    value: number;
    expected_range: [number, number];
    confidence: number;
  }>;
}

export interface EvaluationRunResponse {
  report_id: string;
  agent_name: string;
  metrics: Record<string, number>;
  // ... etc
}
```

Then update `ApiClient` methods to use these types instead of `any`.

#### 3.6 Fix `any` types in page components

**Files affected**:
- `app/(dashboard)/investigations/[traceId]/page.tsx` (22 occurrences)
- `app/(dashboard)/patients/[id]/RiskDashboard.tsx`
- `app/(dashboard)/patients/[id]/GraphRAGExplorer.tsx`
- `app/(dashboard)/patients/[id]/TabPanels.tsx`
- `app/(dashboard)/analytics/benchmark/page.tsx`
- `app/(dashboard)/analytics/evaluation/page.tsx`
- `app/(dashboard)/analytics/graph-rag/page.tsx`

**Fix**: Use proper TypeScript interfaces for all props and state variables. Use discriminated unions for stream events.

#### 3.7 Fix `any` types in investigation components

**Files affected**:
- `components/investigation/AgentFindingsPanel.tsx`
- `components/investigation/InvestigationTimeline.tsx`
- `components/patient/PatientHeader.tsx`

**Fix**: Define interfaces for agent findings, stream events, and patient props.

---

### P2 - Code Quality (Fix This Month)

#### 3.8 Remove unused imports (45+ warnings)

**Files and imports to remove**:

| File | Unused Imports |
|------|----------------|
| `components/investigation/AgentFindingsPanel.tsx` | `CardHeader`, `CardTitle`, `Button` |
| `components/investigation/DebateVisualization.tsx` | `CardHeader`, `CardTitle`, `AlertCircle`, `ArrowRight` |
| `components/investigation/InvestigationComposer.tsx` | `Search`, `Play` |
| `components/investigation/InvestigationTimeline.tsx` | `Zap` |
| `components/investigation/LiveInvestigation.tsx` | `Badge`, `Brain`, `Zap` |
| `components/investigation/ReasoningChainViewer.tsx` | `Clock`, `ArrowRight` |
| `components/patient/PatientHeader.tsx` | `getInitials`, `Avatar` |
| `app/(dashboard)/analytics/benchmark/page.tsx` | `Button`, `Clock`, `Brain` |
| `app/(dashboard)/analytics/evaluation/page.tsx` | `COLORS` |
| `app/(dashboard)/clinical-trials/page.tsx` | `CardHeader`, `CardTitle`, `ExternalLink` |
| `app/(dashboard)/patients/[id]/ClinicalTrialsTab.tsx` | `formatDate` |
| `app/(dashboard)/patients/[id]/InvestigationsTab.tsx` | `formatDateTime`, `Send` |
| `app/(dashboard)/patients/[id]/LabsChart.tsx` | `cn` |
| `app/(dashboard)/patients/[id]/TabPanels.tsx` | `cn`, `DrugInteraction` |
| `lib/hooks/useInvestigationStream.ts` | `apiClient` |
| `lib/hooks/useQueries.ts` | 12 unused type imports |
| `components/ui/ScrollArea.tsx` | `ref` |

#### 3.9 Remove unused variables (14 warnings)

| File | Variable |
|------|----------|
| `analytics/evaluation/page.tsx:34` | `COLORS` |
| `patients/[id]/DrugInteractionsTab.tsx:21` | `riskScore` |
| `patients/[id]/InvestigationsTab.tsx:22` | `activeTab`, `setActiveTab` |
| `patients/[id]/InvestigationsTab.tsx:29` | `streamError` |
| `patients/[id]/RiskDashboard.tsx:28` | `highRisks` |
| `components/providers/ThemeProvider.tsx:41` | `defaultTheme` |

#### 3.10 Fix empty interface declarations (12 errors)

**Files**: `Card.tsx:6`, `Command.tsx:77,94,178,191`, `Dialog.tsx:89,166,177,188,201`, `DropdownMenu.tsx:204,217`

**Fix**: Replace empty interfaces with type aliases:

```typescript
// Before
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

// After
type CardProps = React.HTMLAttributes<HTMLDivElement>;
```

#### 3.11 Fix unescaped entities (3 errors)

| File | Line | Fix |
|------|------|-----|
| `patients/[id]/DrugInteractionsTab.tsx:30` | Single quote | Use `&apos;` |
| `components/search/SearchResults.tsx:194` | Double quotes | Use `&quot;` |

#### 3.12 Replace `<img>` with `next/image`

**File**: `components/ui/Avatar.tsx:32`

**Fix**: Use `next/image` or custom loader for automatic optimization.

---

### P3 - React Best Practices (Fix This Quarter)

#### 3.13 Fix missing hook dependencies

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `ThemeProvider.tsx:84` | `setTheme` missing from useMemo deps | Add to dependency array or wrap in useCallback |
| `useSocket.ts:57` | Unnecessary `SOCKET_URL` dependency | Remove from deps array |

#### 3.14 Add error boundaries

- Add `error.tsx` files for each route group:
  - `app/(dashboard)/error.tsx`
  - `app/(dashboard)/patients/[id]/error.tsx`
  - `app/(dashboard)/investigations/[traceId]/error.tsx`
- Add `loading.tsx` for suspense boundaries on dynamic routes

#### 3.15 Add loading states

- Add `loading.tsx` for all route segments
- Ensure consistent skeleton loading patterns

---

### P4 - Testing Expansion (Ongoing)

#### 3.16 Add E2E tests with Playwright

**Priority flows to test**:
1. Login → Dashboard navigation
2. Patient list → Patient detail → Tab switching
3. Investigation creation and SSE streaming
4. Search functionality with results
5. Theme switching (light/dark/system)
6. Settings configuration and persistence

#### 3.17 Add integration tests with MSW

- Mock API responses with MSW (Mock Service Worker)
- Test React Query hooks in isolation
- Test auth flow end-to-end
- Test SSE/WebSocket streaming

#### 3.18 Add accessibility tests

- Install `@axe-core/react` for automated a11y checks
- Add keyboard navigation tests
- Verify screen reader compatibility
- Test focus management in dialogs and modals

---

### P5 - Performance Optimization

#### 3.19 Bundle analysis

```bash
ANALYZE=true npm run build
```

- Identify large dependencies (recharts: ~400KB, socket.io: ~150KB)
- Consider alternatives or tree-shaking

#### 3.20 Code splitting with dynamic imports

- `InvestigationComposer` (313 lines) → `dynamic(() => import(...))`
- `GraphRAGExplorer` (179 lines) → `dynamic(() => import(...))`
- Chart-heavy pages (`LabsChart`, `RiskDashboard`) → `dynamic(() => import(...))`
- `CommandDialog` in Header → `dynamic(() => import(...))`

#### 3.21 Memoization audit

- Add `React.memo` to list item components (`TrialCard`, `InteractionCard`)
- Memoize expensive computations in `RiskDashboard`, `LabsChart`
- Use `useCallback` for event handlers passed to children
- Review `useInfiniteQuery` pagination for race conditions

#### 3.22 API response caching

- Review `staleTime` (5min) and `gcTime` (30min) settings
- Add optimistic updates for mutations (`useRunInvestigation`, `useReviewInvestigation`)
- Implement proper cache invalidation strategy

---

### P6 - Architecture Improvements

#### 3.23 Consolidate duplicate API versions

- Both v2 and v3 evaluation endpoints exist
- Remove deprecated v2 evaluation endpoints or alias to v3
- Document API versioning strategy

#### 3.24 Extract shared components

`StatCard` is duplicated in:
- `ClinicalTrialsTab.tsx`
- `DrugInteractionsTab.tsx`
- `RiskDashboard.tsx`

**Fix**: Create shared `StatCard` in `components/ui/StatCard.tsx`.

#### 3.25 Improve type coverage

- Replace `any` in `TemporalAnalysis`, `GraphRAGResult` types
- Add discriminated unions for stream event types
- Add branded types for IDs (`PatientId`, `TraceId`) to prevent mixing
- Create `components/ui/types.ts` for shared component prop types

---

## 4. Implementation Priority Matrix

| Priority | Items | Effort | Impact |
|----------|-------|--------|--------|
| **P0** | Critical bugs (3.1-3.4) | 2-3 hours | High - Runtime stability |
| **P1** | Type safety (3.5-3.7) | 1-2 days | High - Prevents bugs |
| **P2** | Code quality (3.8-3.12) | 4-6 hours | Medium - Maintainability |
| **P3** | React practices (3.13-3.15) | 1 day | Medium - Best practices |
| **P4** | Testing expansion (3.16-3.18) | 3-5 days | High - Confidence |
| **P5** | Performance (3.19-3.22) | 2-3 days | Medium - User experience |
| **P6** | Architecture (3.23-3.25) | 2-3 days | Medium - Long-term health |

---

## 5. Testing Commands

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run lint
npm run lint

# Run typecheck
npm run typecheck

# Build
npm run build
```
