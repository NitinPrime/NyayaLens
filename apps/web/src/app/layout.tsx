import type { Metadata } from "next";
import { Inter, Merriweather } from "next/font/google";
import "./globals.css";
import { DisclaimerBanner } from "@/components/layout/disclaimer-banner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const merriweather = Merriweather({
  weight: ["400", "700"],
  subsets: ["latin"],
  variable: "--font-merriweather",
});

export const metadata: Metadata = {
  title: "NyayaLens — Legal Case Analysis for India",
  description:
    "Evidence-grounded legal case analysis and decision-support for Indian law.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${merriweather.variable}`}>
        <DisclaimerBanner />
        {children}
      </body>
    </html>
  );
}
