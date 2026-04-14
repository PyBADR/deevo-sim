"use client";

/**
 * DemoOverlay — Placeholder for executive demo mode.
 * Full implementation deferred; this stub unblocks the build.
 */

import { useRouter } from "next/navigation";

export function DemoOverlay({ onExit }: { onExit?: () => void }) {
  const router = useRouter();

  const handleExit = () => {
    if (onExit) {
      onExit();
    } else {
      router.push("/command-center");
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center gap-6">
      <div className="text-center max-w-lg px-6">
        <h1 className="text-xl font-bold text-slate-900 mb-2">
          Executive Demo Mode
        </h1>
        <p className="text-sm text-slate-600 mb-6">
          Guided walkthrough coming soon. Use the Command Center for the full intelligence flow.
        </p>
        <button
          onClick={handleExit}
          className="px-6 py-2.5 text-sm font-semibold rounded-lg bg-io-accent text-white hover:bg-io-accent-hover transition-colors"
        >
          Open Command Center
        </button>
      </div>
    </div>
  );
}
