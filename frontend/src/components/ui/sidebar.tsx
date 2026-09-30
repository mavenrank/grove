/** shadcn Sidebar composition, adapted to Grove's palette and resize policy.
 * https://ui.shadcn.com/docs/components/radix/sidebar
 */
import {
  createContext, useCallback, useContext, useEffect, useRef, useState, useSyncExternalStore,
  type ComponentProps, type CSSProperties, type ReactNode,
} from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Slot } from "@radix-ui/react-slot";
import { GripVertical, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";

type Size = "mobile" | "tablet" | "desktop" | "wide";
type Preferences = Partial<Record<Size, { width?: number; open?: boolean }>>;
const STORAGE_KEY = "grove.sidebar.v1";
const DEFAULT_WIDTH: Record<Size, number> = { mobile: 288, tablet: 208, desktop: 240, wide: 264 };
const MIN_WIDTH = 184;
const RAIL_WIDTH = 64;

interface SidebarContextValue {
  isMobile: boolean;
  open: boolean;
  openMobile: boolean;
  width: number;
  maxWidth: number;
  toggleSidebar: () => void;
  closeMobile: () => void;
  resize: (width: number, persist?: boolean) => void;
  resetWidth: () => void;
  trigger: React.RefObject<HTMLButtonElement | null>;
}
const SidebarContext = createContext<SidebarContextValue | null>(null);

export function useSidebar() {
  const value = useContext(SidebarContext);
  if (!value) throw new Error("Sidebar must be used within SidebarProvider");
  return value;
}

function subscribeViewport(callback: () => void) {
  window.addEventListener("resize", callback);
  return () => window.removeEventListener("resize", callback);
}

function readPreferences(): Preferences {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
    const result: Preferences = {};
    for (const size of ["tablet", "desktop", "wide"] as const) {
      const value = stored?.[size];
      if (!value || typeof value !== "object") continue;
      result[size] = {
        ...(typeof value.width === "number" && Number.isFinite(value.width) ? { width: value.width } : {}),
        ...(typeof value.open === "boolean" ? { open: value.open } : {}),
      };
    }
    return result;
  }
  catch { return {}; }
}

export function SidebarProvider({ children }: { children: ReactNode }) {
  const viewport = useSyncExternalStore(subscribeViewport, () => window.innerWidth, () => 1024);
  const size: Size = viewport < 768 ? "mobile" : viewport < 1024 ? "tablet" : viewport < 1440 ? "desktop" : "wide";
  const isMobile = size === "mobile";
  const [preferences, setPreferences] = useState<Preferences>(readPreferences);
  const [openMobile, setOpenMobile] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const maxWidth = Math.max(MIN_WIDTH, Math.min(320, Math.floor(viewport / 3)));
  const clamp = (n: number) => Math.min(maxWidth, Math.max(MIN_WIDTH, n));
  const storedWidth = preferences[size]?.width;
  const width = clamp(typeof storedWidth === "number" && Number.isFinite(storedWidth) ? storedWidth : DEFAULT_WIDTH[size]);
  const open = isMobile || (preferences[size]?.open ?? (size !== "tablet"));

  const update = (patch: { width?: number; open?: boolean }, persist = true) => {
    setPreferences((prev) => {
      const next = { ...prev, [size]: { ...prev[size], ...patch } };
      if (persist) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { /* storage can be unavailable */ }
      }
      return next;
    });
  };
  const toggleSidebar = () => {
    if (isMobile) setOpenMobile((prev) => !prev);
    else update({ open: !open });
  };
  const closeMobile = useCallback(() => setOpenMobile(false), []);

  useEffect(() => { if (!isMobile) setOpenMobile(false); }, [isMobile]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable='true']")) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
        event.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <SidebarContext.Provider value={{ isMobile, open, openMobile, width, maxWidth, trigger,
      toggleSidebar, closeMobile, resize: (n, persist = true) => update({ width: clamp(n) }, persist),
      resetWidth: () => update({ width: DEFAULT_WIDTH[size] }) }}>
      <Dialog.Root open={isMobile && openMobile} onOpenChange={setOpenMobile}>
        <div data-slot="sidebar-wrapper" data-state={open ? "expanded" : "collapsed"}
          className="flex min-h-dvh w-full bg-paper-50">
          {children}
        </div>
      </Dialog.Root>
    </SidebarContext.Provider>
  );
}

export function Sidebar({ children }: { children: ReactNode }) {
  const { isMobile, open, width, trigger } = useSidebar();
  const panelClass = "flex flex-col bg-forest-900 text-paper-50";
  if (isMobile) {
    return (
      <Dialog.Portal>
        <Dialog.Overlay className="sidebar-overlay fixed inset-0 z-40 bg-forest-900/35 backdrop-blur-[2px]" />
        <Dialog.Content id="grove-sidebar" data-slot="sidebar" data-state="expanded"
          className={`${panelClass} sidebar-sheet fixed inset-y-0 left-0 z-50 h-dvh w-[min(288px,calc(100vw-48px))] shadow-xl`}
          onCloseAutoFocus={(event) => { event.preventDefault(); trigger.current?.focus(); }}>
          <Dialog.Title className="sr-only">Grove navigation</Dialog.Title>
          <Dialog.Description className="sr-only">Choose a study page. Escape closes this menu.</Dialog.Description>
          <Dialog.Close aria-label="Close navigation" className="absolute right-3 top-4 z-10 rounded-md p-2 text-paper-50/70 hover:bg-white/10 hover:text-white">
            <X size={18} aria-hidden />
          </Dialog.Close>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    );
  }
  return (
    <aside id="grove-sidebar" data-slot="sidebar" data-state={open ? "expanded" : "collapsed"}
      style={{ width: open ? width : RAIL_WIDTH } as CSSProperties}
      className={`${panelClass} sticky top-0 h-dvh shrink-0 border-r border-forest-700`}>
      {children}
      {open ? <SidebarRail /> : null}
    </aside>
  );
}

export function SidebarTrigger({ className = "" }: { className?: string }) {
  const { isMobile, open, openMobile, toggleSidebar, trigger } = useSidebar();
  const expanded = isMobile ? openMobile : open;
  const label = isMobile ? "Open navigation" : open ? "Collapse sidebar" : "Expand sidebar";
  return (
    <button ref={trigger} type="button" onClick={toggleSidebar} aria-label={label}
      aria-expanded={expanded} aria-controls="grove-sidebar" title={`${label} (Ctrl+B)`}
      className={`inline-flex size-8 shrink-0 items-center justify-center rounded-md hover:bg-white/10 ${className}`}>
      {expanded ? <PanelLeftClose size={18} aria-hidden /> : <PanelLeftOpen size={18} aria-hidden />}
    </button>
  );
}

export function SidebarRail() {
  const { width, maxWidth, resize, resetWidth } = useSidebar();
  const drag = useRef<{ x: number; width: number } | null>(null);
  return (
    <div role="separator" aria-label="Resize sidebar" aria-orientation="vertical" tabIndex={0}
      aria-valuemin={MIN_WIDTH} aria-valuemax={maxWidth} aria-valuenow={width}
      title="Drag to resize · Arrow keys to adjust · Double-click to reset"
      className="group/rail absolute inset-y-0 -right-1 z-20 flex w-2 touch-none cursor-col-resize items-center justify-center outline-offset-2"
      onDoubleClick={resetWidth}
      onPointerDown={(event) => {
        if (event.button !== 0) return;
        event.preventDefault();
        drag.current = { x: event.clientX, width };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        if (drag.current) resize(drag.current.width + event.clientX - drag.current.x, false);
      }}
      onPointerUp={(event) => {
        if (!drag.current) return;
        resize(drag.current.width + event.clientX - drag.current.x);
        drag.current = null;
        event.currentTarget.releasePointerCapture(event.pointerId);
      }}
      onPointerCancel={() => { drag.current = null; }}
      onKeyDown={(event) => {
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          resize(width + (event.key === "ArrowRight" ? 1 : -1) * (event.shiftKey ? 24 : 8));
        } else if (event.key === "Home" || event.key === "End") {
          event.preventDefault();
          resize(event.key === "Home" ? MIN_WIDTH : maxWidth);
        }
      }}>
      <span className="flex h-10 w-3 items-center justify-center rounded-full border border-paper-300 bg-paper-50 text-forest-600 opacity-70 shadow-sm transition-opacity group-hover/rail:opacity-100">
        <GripVertical size={12} aria-hidden />
      </span>
    </div>
  );
}

export function SidebarHeader({ children }: { children: ReactNode }) {
  return <div data-slot="sidebar-header" className="shrink-0 border-b border-white/10 px-3 py-4">{children}</div>;
}
export function SidebarContent({ children }: { children: ReactNode }) {
  return <div data-slot="sidebar-content" className="min-h-0 flex-1 overflow-y-auto px-2 py-5">{children}</div>;
}
export function SidebarFooter({ children }: { children: ReactNode }) {
  return <div data-slot="sidebar-footer" className="shrink-0 border-t border-white/10 px-3 py-4">{children}</div>;
}
export function SidebarInset({ children }: { children: ReactNode }) {
  return <div data-slot="sidebar-inset" className="min-w-0 flex-1">{children}</div>;
}

export function SidebarMenuButton({ children, label, asChild = false, ...props }:
  ComponentProps<"button"> & { label: string; asChild?: boolean }) {
  const { open, isMobile } = useSidebar();
  const Comp = asChild ? Slot : "button";
  const button = <Comp data-slot="sidebar-menu-button" aria-label={label} {...props}>{children}</Comp>;
  if (open || isMobile) return button;
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>{button}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content side="right" sideOffset={10} className="z-50 rounded-md bg-forest-900 px-3 py-2 text-xs text-paper-50 shadow-md">
          {label}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
