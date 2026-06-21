import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-app" });

export const metadata = {
  title: "ParkPulse — AI Parking Intelligence for Impact-Prioritized Enforcement",
  description:
    "Turns 298K Bengaluru parking-violation records into a Congestion Impact Score, an "
    + "impact-weighted hotspot map, ranked enforcement zones, a violation forecaster, and a "
    + "patrol optimizer — telling enforcement where and when to deploy.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
