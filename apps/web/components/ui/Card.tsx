import * as React from "react";
import { cn } from "@/lib/utils";

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "bg-[var(--color-background-paper)] rounded-[24px] p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] border border-transparent transition-all hover:shadow-[0_8px_32px_rgba(0,0,0,0.08)]",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

export { Card };
