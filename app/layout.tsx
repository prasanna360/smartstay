import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartStay | Rental Pricing Demo",
  description:
    "Explore explainable nightly pricing benchmarks for short-term rentals. Uses synthetic demo data, not live market rates.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
