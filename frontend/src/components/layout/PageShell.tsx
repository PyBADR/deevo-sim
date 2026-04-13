/**
 * PageShell — full-page wrapper with TopNav and main content area.
 * Provides consistent page-level structure.
 */

import { TopNav } from "./TopNav";

interface PageShellProps {
  children: React.ReactNode;
}

export function PageShell({ children }: PageShellProps) {
  return (
    <div className="min-h-screen bg-bg-main">
      <TopNav />
      <main>{children}</main>
    </div>
  );
}
