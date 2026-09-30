import type * as React from "react";
import { Loader2Icon } from "lucide-react";

/** shadcn/ui default spinner: a spinning Loader2 icon. */
function Spinner({ className, ...props }: React.ComponentProps<"svg">) {
  return (
    <Loader2Icon
      role="status"
      aria-label="Loading"
      className={"size-4 animate-spin " + (className ?? "")}
      {...props}
    />
  );
}

export { Spinner };
