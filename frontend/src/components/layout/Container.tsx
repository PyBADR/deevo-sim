/**
 * Container — max-width wrapper with consistent horizontal padding.
 * Used inside every section to enforce width discipline.
 */

interface ContainerProps {
  children: React.ReactNode;
  narrow?: boolean;
  className?: string;
}

export function Container({ children, narrow, className }: ContainerProps) {
  return (
    <div
      className={`
        mx-auto w-full px-6 sm:px-8
        ${narrow ? "max-w-narrow" : "max-w-content"}
        ${className ?? ""}
      `}
    >
      {children}
    </div>
  );
}
