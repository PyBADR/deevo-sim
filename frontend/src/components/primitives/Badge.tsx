/**
 * Badge — small classification or status indicator.
 */

type BadgeVariant = "default" | "amber" | "red" | "olive";

const VARIANT_STYLES: Record<BadgeVariant, string> = {
  default: "bg-bg-muted text-tx-secondary",
  amber: "bg-status-amber/10 text-status-amber",
  red: "bg-status-red/10 text-status-red",
  olive: "bg-status-olive/10 text-status-olive",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
}

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-sm
        text-micro font-medium uppercase tracking-wider
        ${VARIANT_STYLES[variant]}
      `}
    >
      {children}
    </span>
  );
}
