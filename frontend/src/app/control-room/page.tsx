"use client";

import Link from "next/link";

export default function ControlRoomPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-io-bg">
      <div className="text-center space-y-6 px-6">
        <h1 className="text-4xl font-bold text-io-accent">Coming in V2</h1>
        <p className="text-lg text-io-primary max-w-md">
          The Control Room interface is being rebuilt. Check back soon for updates.
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-2 bg-io-accent text-white rounded-lg hover:bg-blue-700 transition"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
