import { useEffect } from "react";
import { Navigate, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BookOpen, History as HistoryIcon, LayoutDashboard, Settings2, Shapes, Sprout, SquarePen,
} from "lucide-react";
import { api } from "./api";
import { TestRunner } from "./runner/TestRunner";
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarInset,
  SidebarMenuButton, SidebarProvider, SidebarTrigger, useSidebar,
} from "./components/ui/sidebar";

/** Test sessions retain their dedicated full-screen layout. */
export function TestRoute() { return <TestRunner />; }
export function RedirectHome() { return <Navigate to="/" replace />; }

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true, group: "Your progress",
    prefetch: ["/api/insights", "/api/history"] },
  { to: "/learn", label: "Learn", icon: BookOpen, group: "Practice",
    prefetch: ["/api/content/taxonomy", "/api/content/concepts"] },
  { to: "/flashcards", label: "Flashcards", icon: Shapes, group: "Practice",
    prefetch: ["/api/content/flashcards", "/api/flashcards/stats"] },
  { to: "/tests", label: "Tests", icon: SquarePen, group: "Practice",
    prefetch: ["/api/content/taxonomy", "/api/history"] },
  { to: "/history", label: "History", icon: HistoryIcon, group: "Your progress",
    prefetch: ["/api/history", "/api/insights"] },
  { to: "/admin", label: "Admin", icon: Settings2, group: "Workspace", prefetch: ["/api/health"] },
];

function AppSidebar() {
  const { open, isMobile, closeMobile } = useSidebar();
  const { pathname } = useLocation();
  return (
    <Sidebar>
      <SidebarHeader>
        <div className={`flex gap-3 ${open ? "items-center" : "flex-col items-center"}`}>
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl border border-gold-500/25 bg-gold-500/10 text-gold-500">
            <Sprout size={20} strokeWidth={1.6} aria-hidden />
          </div>
          {open ? <div className="min-w-0 flex-1">
            <div className="font-serif text-xl tracking-tight">Grove</div>
            <div className="mt-0.5 truncate text-[11px] text-paper-50/50">Aptitude &amp; reasoning</div>
          </div> : null}
          {!isMobile ? <SidebarTrigger className="text-paper-50/60 hover:text-white" /> : <span className="w-6" />}
        </div>
      </SidebarHeader>
      <SidebarContent>
        <nav aria-label="Primary" className="space-y-6">
          {["Your progress", "Practice", "Workspace"].map((group) => (
            <div key={group}>
              {open ? <div className="mb-2 px-3 text-[10px] font-medium uppercase tracking-[0.15em] text-paper-50/40">{group}</div> : null}
              <ul className="space-y-1">
                {NAV.filter((item) => item.group === group).map(({ to, label, icon: Icon, end, prefetch }) => {
                  const isActive = pathname === to || (!end && pathname.startsWith(`${to}/`));
                  return (
                  <li key={to}>
                    <SidebarMenuButton asChild label={label}>
                      <NavLink to={to} end={end} onClick={closeMobile}
                        onMouseEnter={() => api.prefetch(...prefetch)} onFocus={() => api.prefetch(...prefetch)}
                        className={`relative flex min-h-10 items-center rounded-lg text-sm transition-colors ${
                          open ? "gap-3 px-3" : "justify-center"
                        } ${isActive ? "bg-white/10 font-medium text-white before:absolute before:left-0 before:h-4 before:w-0.5 before:rounded-full before:bg-gold-500" : "text-paper-50/65 hover:bg-white/5 hover:text-white"}`}>
                        <Icon size={18} strokeWidth={1.7} aria-hidden className="shrink-0" />
                        {open ? <span className="truncate">{label}</span> : null}
                      </NavLink>
                    </SidebarMenuButton>
                  </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </SidebarContent>
      {open ? <SidebarFooter>
        <div className="text-xs text-paper-50/60">Your study space</div>
        {!isMobile ? <div className="mt-1 text-[10px] text-paper-50/35">Ctrl B · Toggle sidebar</div> : null}
      </SidebarFooter> : null}
    </Sidebar>
  );
}

function LayoutContent() {
  const { isMobile, closeMobile } = useSidebar();
  const { pathname } = useLocation();
  useEffect(() => { closeMobile(); }, [pathname, closeMobile]);
  return (
    <>
      <a href="#main-content" className="sr-only z-[60] rounded-md bg-paper-50 px-4 py-2 text-forest-900 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <AppSidebar />
      <SidebarInset>
        {isMobile ? <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-paper-300 bg-paper-50/95 px-4 backdrop-blur">
          <SidebarTrigger className="text-forest-700 hover:bg-paper-200" />
          <Sprout size={18} className="text-forest-600" aria-hidden />
          <span className="font-serif text-lg text-forest-900">Grove</span>
        </header> : null}
        <main id="main-content" tabIndex={-1} className="min-w-0 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </SidebarInset>
    </>
  );
}

export function Layout() { return <SidebarProvider><LayoutContent /></SidebarProvider>; }
