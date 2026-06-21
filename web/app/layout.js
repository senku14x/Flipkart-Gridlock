import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-app" });

export const metadata = {
  title: "ParkPulse: find the parking that chokes traffic, and patrol it first",
  description:
    "ParkPulse reads 298,000 Bengaluru parking-violation records and scores every hotspot by how "
    + "much it slows traffic, so enforcement knows where and when to deploy. Impact map, ranked "
    + "zones, a violation forecaster, and a patrol optimizer.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
