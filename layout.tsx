import "./globals.css";
import type { Metadata, Viewport } from "next";
import Nav from "@/components/Nav";
import SWRegister from "@/components/SWRegister";

export const metadata: Metadata = {
  title: "TechMusha — Learn tech, offline",
  description: "Zimbabwe's offline-first learning platform for CS, dev, security, and more.",
  manifest: "/manifest.json",
  applicationName: "TechMusha",
};

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen pb-20">
        <main className="max-w-2xl mx-auto px-3 pt-4">{children}</main>
        <Nav />
        <SWRegister />
      </body>
    </html>
  );
}