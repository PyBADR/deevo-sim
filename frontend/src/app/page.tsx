/**
 * Impact Observatory | مرصد الأثر — Entry Shell
 *
 * This is NOT the product. This is the door.
 * One name. One sentence. One action.
 * The product lives at /command-center.
 */

import Link from 'next/link';

export default function EntryPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0c] flex flex-col items-center justify-center px-6">
      {/* Product identity */}
      <div className="text-center max-w-xl">
        <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight text-[#e8e6e3] leading-tight mb-3">
          Impact Observatory
        </h1>
        <p className="text-[0.9375rem] text-[#706f6c] font-medium tracking-wide mb-10">
          مرصد الأثر
        </p>

        <p className="text-[1rem] sm:text-[1.125rem] leading-relaxed text-[#a09f9c] mb-14">
          GCC Macro Intelligence Operating Surface.
          <br className="hidden sm:inline" />
          {' '}From signals to sovereign decisions.
        </p>

        {/* Single CTA — no alternatives, no storytelling */}
        <Link
          href="/command-center"
          className="inline-block px-8 py-3.5 text-[0.9375rem] font-semibold tracking-wide text-[#0a0a0c] bg-[#e8e6e3] rounded-md transition-all duration-200 hover:bg-[#ffffff] hover:shadow-[0_0_24px_rgba(232,230,227,0.15)]"
        >
          Open Command Center
        </Link>
      </div>

      {/* Minimal footer */}
      <p className="absolute bottom-8 text-[0.6875rem] text-[#3a3937] tracking-wider">
        Impact Observatory · مرصد الأثر · GCC · {new Date().getFullYear()}
      </p>
    </div>
  );
}
