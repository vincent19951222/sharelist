import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PhoneShellProps {
  children: ReactNode;
  className?: string;
}

export function PhoneShell({ children, className }: PhoneShellProps) {
  return (
    <main className="px-0 md:px-4">
      <div className={cn("quest-shell quest-grid", className)}>{children}</div>
    </main>
  );
}
