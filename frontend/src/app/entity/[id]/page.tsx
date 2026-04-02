"use client";

import Link from "next/link";

export default function EntityDetailPage() {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-io-primary mb-2">Entity Detail</h1>
        <p className="text-io-secondary mb-4">Coming in V2</p>
        <Link href="/" className="text-io-accent hover:underline text-sm">
          ← Back to Observatory
        </Link>
      </div>
    </div>
  );
}
