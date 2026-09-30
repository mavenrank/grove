/**
 * Facade over the decomposed UI modules.
 *
 * New code should import from the specific module (`components/ui/primitives`,
 * `layout`, `telemetry`); this file keeps every existing `from "./ui"` /
 * `from "../ui"` import working without churn.
 */
export { Layout, TestRoute, RedirectHome } from "./layout";
export { TelemetryProvider, useTelemetry } from "./telemetry";
export {
  PageHeader,
  Card,
  Button,
  ErrorNote,
  Loading,
  Empty,
  IconTip,
} from "./components/ui/primitives";
