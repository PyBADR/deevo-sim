/**
 * SectionTitle — consistent heading + optional subtitle for page sections.
 */

interface SectionTitleProps {
  heading: string;
  subtitle?: string;
  align?: "left" | "center";
}

export function SectionTitle({ heading, subtitle, align = "left" }: SectionTitleProps) {
  const alignment = align === "center" ? "text-center" : "text-left";

  return (
    <div className={`mb-12 ${alignment}`}>
      <h2 className="text-section-title text-tx-primary text-balance">
        {heading}
      </h2>
      {subtitle && (
        <p className="mt-3 text-section-sub text-tx-secondary max-w-narrow text-balance">
          {subtitle}
        </p>
      )}
    </div>
  );
}
