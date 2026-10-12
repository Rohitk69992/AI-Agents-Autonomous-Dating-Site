import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AuraMatch AI — Production Agentic Dating Platform",
  description: "Autonomous multi-agent dating platform with genuine agent-to-agent interactions, LinkedIn/Instagram evidence traceability, and explainable rankings.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased`}>
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800 bg-slate-900/60 py-6 text-center text-xs text-slate-500">
          <p>AuraMatch AI &bull; Autonomous Multi-Agent Dating Simulation &bull; Consented Profiles with Verifiable Traceability</p>
        </footer>
      </body>
    </html>
  );
}
