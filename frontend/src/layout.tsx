import { Navigate, NavLink, Outlet } from "react-router-dom";
import {
  BookOpen,
  History as HistoryIcon,
  LayoutDashboard,
  Settings2,
  Shapes,
  SquarePen,
} from "lucide-react";
import { api } from "./api";
import { TestRunner } from "./runner/TestRunner";

/** Route guard: the runner is a chrome-less full-screen route. */
export function TestRoute() {
  return <TestRunner />;
}

export function RedirectHome() {
  return <Navigate to="/" replace />;
}

const NAV = [
  {
    to: "/",
    label: "Overview",
    icon: LayoutDashboard,
    end: true,
    prefetch: ["/api/insights", "/api/history"],
  },
  {
    to: "/learn",
    label: "Learn",
    icon: BookOpen,
    prefetch: ["/api/content/taxonomy", "/api/content/concepts"],
  },
  {
    to: "/flashcards",
    label: "Flashcards",
    icon: Shapes,
    prefetch: ["/api/content/flashcards", "/api/flashcards/stats"],
  },
  {
    to: "/tests",
    label: "Tests",
    icon: SquarePen,
    prefetch: ["/api/content/taxonomy", "/api/history"],
  },
  {
    to: "/history",
    label: "History",
    icon: HistoryIcon,
    prefetch: ["/api/history", "/api/insights"],
  },
  { to: "/admin", label: "Admin", icon: Settings2, prefetch: ["/api/health"] },
];

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-paper-300 bg-paper-100">
        <div className="px-5 py-6">
          <div className="text-xl font-semibold tracking-tight text-forest-700">Grove</div>
          <div className="mt-1 text-xs text-forest-900/50">aptitude &amp; reasoning practice</div>
        </div>
        <nav aria-label="Primary" className="mt-2 px-3">
          <ul className="space-y-1">
            {NAV.map(({ to, label, icon: Icon, end, prefetch }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  onMouseEnter={() => api.prefetch(...prefetch)}
                  onFocus={() => api.prefetch(...prefetch)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-sm px-3 py-2 text-sm ${
                      isActive
                        ? "bg-forest-100 font-medium text-forest-700"
                        : "text-forest-900/70 hover:bg-paper-200"
                    }`
                  }
                >
                  <Icon size={16} strokeWidth={1.75} aria-hidden />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>
      <main className="min-w-0 flex-1 px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
