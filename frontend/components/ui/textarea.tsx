import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[96px] w-full rounded-2xl border-none bg-slate-50 px-5 py-4 text-sm text-text shadow-inner-soft placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/20 resize-none transition-all",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Textarea };
