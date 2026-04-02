import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/shared/providers";
import { DirectionProvider } from "@/components/shared/direction-provider";

export const metadata: Metadata = {
  title: "Impact Observatory | مرصد الأثر",
  description:
    "Decision Intelligence Platform for GCC Financial Markets — Financial-first, decision-terminal, explainable",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-io-bg text-io-primary antialiased font-sans">
        <Providers>
          <DirectionProvider>{children}</DirectionProvider>
        </Providers>
      </body>
    </html>
  );
}
