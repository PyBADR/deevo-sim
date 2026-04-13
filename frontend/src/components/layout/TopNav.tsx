"use client";

/**
 * TopNav — minimal top navigation bar.
 * Neutral premium tone. No blue identity.
 * Sticks to top on scroll with subtle backdrop.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Container } from "./Container";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/command-center", label: "Scenarios" },
  { href: "/evaluation", label: "Evaluation" },
] as const;

export function TopNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 bg-bg-main/90 backdrop-blur-md border-b border-border-muted">
      <Container>
        <nav className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link
            href="/"
            className="text-label font-semibold text-tx-primary tracking-tight"
          >
            Impact Observatory
          </Link>

          {/* Links */}
          <div className="flex items-center gap-6">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    text-caption font-medium transition-colors duration-150
                    ${active
                      ? "text-tx-primary"
                      : "text-tx-tertiary hover:text-tx-secondary"
                    }
                  `}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </Container>
    </header>
  );
}
