/**
 * PageShell — top-level page wrapper.
 *
 * Provides TopNav + MacroStrip + main content area with fade-in animation.
 * MacroStrip is the CEO intelligence strip — countries, sectors, posture.
 * Only visible when a scenario is active (client-side state).
 * Every page in the product wraps its content in PageShell.
 */

import { TopNav } from './TopNav';
import { MacroStrip } from '../intelligence/MacroStrip';

interface PageShellProps {
  children: React.ReactNode;
}

export function PageShell({ children }: PageShellProps) {
  return (
    <div className="min-h-screen bg-[var(--io-bg)]">
      <TopNav />
      <MacroStrip />
      <main className="io-fade-in">
        {children}
      </main>
    </div>
  );
}
