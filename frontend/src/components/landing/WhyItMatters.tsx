/**
 * WhyItMatters — value proposition section with 4 quiet cards.
 */

import { Container } from "@/components/layout/Container";
import { SectionTitle } from "@/components/primitives/SectionTitle";
import { QuietCard } from "@/components/primitives/QuietCard";
import { whyItMatters } from "@/lib/copy";

export function WhyItMatters() {
  return (
    <Container>
      <SectionTitle heading={whyItMatters.heading} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {whyItMatters.points.map((point) => (
          <QuietCard key={point.title}>
            <h3 className="text-card-title text-tx-primary mb-2">
              {point.title}
            </h3>
            <p className="text-card-body text-tx-secondary leading-relaxed">
              {point.description}
            </p>
          </QuietCard>
        ))}
      </div>
    </Container>
  );
}
