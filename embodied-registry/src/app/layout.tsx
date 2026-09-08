import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://embodied-registry.vercel.app"),
  title: "Embodied Registry — Evidence for robot skills",
  description: "A trusted, open registry for reproducible robot skills, hardware compatibility, and real-world evaluation evidence.",
  openGraph: { type: "website", title: "Embodied Registry", description: "Make robot-policy transfer a testable claim." },
  twitter: { card: "summary_large_image", title: "Embodied Registry", description: "Make robot-policy transfer a testable claim." },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}><body>{children}</body></html>;
}
