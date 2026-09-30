import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout, TelemetryProvider, TestRoute } from "./ui";
import { Loading } from "./ui";

// Route-level code splitting: each page is its own chunk, so first paint
// only needs the shell + the visited route. (The test runner stays eager —
// entering test mode must not wait on a chunk fetch.)
const Overview = lazy(() => import("./pages/Overview").then((m) => ({ default: m.Overview })));
const Learn = lazy(() => import("./pages/Learn").then((m) => ({ default: m.Learn })));
const ConceptPage = lazy(() => import("./pages/Concept").then((m) => ({ default: m.ConceptPage })));
const Flashcards = lazy(() => import("./pages/Flashcards").then((m) => ({ default: m.Flashcards })));
const TestSetup = lazy(() => import("./pages/TestSetup").then((m) => ({ default: m.TestSetup })));
const Results = lazy(() => import("./pages/Results").then((m) => ({ default: m.Results })));
const TestDetailPage = lazy(() => import("./pages/TestDetail").then((m) => ({ default: m.TestDetailPage })));
const History = lazy(() => import("./pages/History").then((m) => ({ default: m.History })));
const Admin = lazy(() => import("./pages/Admin").then((m) => ({ default: m.Admin })));

export default function App() {
  return (
    <BrowserRouter>
      <TelemetryProvider>
      <Routes>
        {/* Test mode is chrome-less and isolated from learning surfaces (handoff §8.4) */}
        <Route path="/tests/run" element={<TestRoute />} />
        <Route path="/results" element={<Results />} />

        <Route element={<Layout />}>
          <Route path="/" element={<Suspense fallback={<Loading />}><Overview /></Suspense>} />
          <Route path="/learn" element={<Suspense fallback={<Loading />}><Learn /></Suspense>} />
          <Route path="/learn/:conceptId" element={<Suspense fallback={<Loading />}><ConceptPage /></Suspense>} />
          <Route path="/flashcards" element={<Suspense fallback={<Loading />}><Flashcards /></Suspense>} />
          <Route path="/tests" element={<Suspense fallback={<Loading />}><TestSetup /></Suspense>} />
          <Route path="/tests/:sessionId" element={<Suspense fallback={<Loading />}><TestDetailPage /></Suspense>} />
          <Route path="/history" element={<Suspense fallback={<Loading />}><History /></Suspense>} />
          <Route path="/admin" element={<Suspense fallback={<Loading />}><Admin /></Suspense>} />
        </Route>
      </Routes>
      </TelemetryProvider>
    </BrowserRouter>
  );
}
