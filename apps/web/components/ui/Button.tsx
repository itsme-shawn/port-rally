import * as React from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-2xl font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.96]",
          {
            "bg-[var(--color-primary)] text-white hover:bg-[#00B34E] shadow-sm hover:shadow-md": variant === "primary",
            "bg-[var(--color-secondary)] text-[var(--color-text-primary)] hover:bg-[#D5F0DE]": variant === "secondary",
            "bg-transparent text-[var(--color-text-secondary)] hover:bg-black/5": variant === "ghost",
            "h-10 px-4 py-2 text-sm": size === "sm",
            "h-13 px-6 py-3.5 text-base": size === "md",
            "h-16 px-8 py-5 text-xl": size === "lg",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
