import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-0.5 text-xs font-mono",
  {
    variants: {
      variant: {
        high: "bg-danger/10 text-danger border-danger/20",
        medium: "bg-warning/10 text-warning border-warning/20",
        low: "bg-success/10 text-success border-success/20",
        neutral: "bg-black/[0.03] text-text-sub border-border",
        type: "bg-accent/10 text-accent border-accent/20 font-sans",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant, className }))} {...props} />;
}

export { Badge, badgeVariants };
