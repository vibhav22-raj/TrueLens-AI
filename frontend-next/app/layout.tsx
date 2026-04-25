import "./globals.css";
import type { Metadata } from "next";
import { Sora, Manrope } from "next/font/google";
import Providers from "@/components/Providers";

const display = Sora({
  subsets: ["latin"],
  variable: "--font-display"
});

const body = Manrope({
  subsets: ["latin"],
  variable: "--font-body"
});

export const metadata: Metadata = {
  title: "DeepShield AI | Premium Deepfake Detection",
  description: "Premium, AI-powered deepfake detection for images and videos."
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${display.variable} ${body.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
