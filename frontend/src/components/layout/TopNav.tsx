/**
 * TopNav — Sovereign-grade navigation.
 *
 * Authoritative product identity. Quiet navigation.
 * Frosted glass. No visual noise. Executive restraint.
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Container } from './Container';

const links = [
  { href: '/',           label: 'Overview' },
  { href: '/decision',   label: 'Decisions' },
  { href: '/evaluation', label: 'Evaluation' },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 bg-[var(--io-bg)]/85 backdrop-blur-xl border-b border-[var(--io-border-muted)]">
      <Container>
        <div className="flex items-center justify-between h-14">
          {/* Brand — authoritative, bilingual */}
          <Link href="/" className="flex items-baseline gap-3 group">
            <span className="text-[0.9375rem] font-bold tracking-tight text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-200">
              Impact Observatory
            </span>
            <span className="text-[0.6875rem] text-[var(--io-text-tertiary)] font-medium hidden sm:inline tracking-wide">
              مرصد الأثر
            </span>
          </Link>

          {/* Navigation — minimal, restrained */}
          <div className="flex items-center gap-1.5">
            {links.map((link) => {
              const isActive =
                link.href === '/'
                  ? pathname === '/'
                  : pathname.startsWith(link.href);

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={[
                    'px-3.5 py-1.5 rounded-md text-[0.8125rem] font-medium transition-all duration-200',
                    isActive
                      ? 'text-[var(--io-charcoal)] bg-[var(--io-muted)]/60'
                      : 'text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] hover:bg-[var(--io-muted)]/40',
                  ].join(' ')}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      </Container>
    </nav>
  );
}
