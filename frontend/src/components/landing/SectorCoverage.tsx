/**
 * SectorCoverage — grid showing which sectors the system covers.
 * Quiet row of labeled items. No heavy graphics.
 */

import { Container } from "@/components/layout/Container";
import { SectionTitle } from "@/components/primitives/SectionTitle";
import { sectorCoverage } from "@/lib/copy";

export function SectorCoverage() {
  return (
    <Container>
      <SectionTitle
        heading={sectorCoverage.heading}
        subtitle={sectorCoverage.subtitle}
      />
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {sectorCoverage.sectors.map((sector) => (
          <div
            key={sector.key}
            className="
              bg-bg-surface border border-border-muted rounded-lg
              px-5 py-4 text-center
            "
          >
            <span className="text-label text-tx-primary">{sector.label}</span>
          </div>
        ))}
      </div>
    </Container>
  );
}
