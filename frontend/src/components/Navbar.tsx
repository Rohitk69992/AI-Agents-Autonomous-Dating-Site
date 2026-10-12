"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Heart, Users, UserPlus, PlayCircle, History, Trophy, Sparkles, Settings, Activity } from "lucide-react";
import { api } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<{ status: string; llm_provider: string; llm_model: string } | null>(null);

  useEffect(() => {
    api.getHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: "offline", llm_provider: "unknown", llm_model: "none" }));
  }, []);

  const navLinks = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/participants", label: "Directory", icon: Users },
    { href: "/ingest", label: "Ingest", icon: UserPlus },
    { href: "/dates/live", label: "Live Simulation", icon: PlayCircle },
    { href: "/dates", label: "Sessions", icon: History },
    { href: "/rankings", label: "Rankings", icon: Trophy },
    { href: "/demo", label: "25-Participant Demo", icon: Sparkles, highlight: true },
    { href: "/admin", label: "Operations", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-pink-600 to-rose-500 flex items-center justify-center shadow-lg shadow-pink-500/20">
                <Heart className="w-5 h-5 text-white fill-white" />
              </div>
              <div>
                <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  AuraMatch AI
                </span>
                <span className="block text-[10px] uppercase tracking-wider font-semibold text-pink-400">
                  Agentic Dating Platform
                </span>
              </div>
            </Link>
          </div>

          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    link.highlight
                      ? "bg-pink-500/10 text-pink-400 border border-pink-500/30 hover:bg-pink-500/20"
                      : isActive
                      ? "bg-slate-800 text-white font-semibold border border-slate-700"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center space-x-2">
            {health && (
              <div className="flex items-center space-x-2 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700 text-xs">
                <span
                  className={`w-2 h-2 rounded-full ${
                    health.status === "healthy" ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                  }`}
                />
                <span className="text-slate-300 font-medium text-[11px]">
                  {health.llm_model
                    ? health.llm_model
                        .replace(/openai\/gpt-oss-20b/i, "GPT-OSS 20B (Groq)")
                        .replace(/openai\/gpt-oss-120b/i, "GPT-OSS 120B (Groq)")
                        .replace(/llama-3\.3-70b-versatile/i, "Llama 3.3 70B (Groq)")
                        .replace(/llama-3\.1-8b-instant/i, "Llama 3.1 8B (Groq)")
                        .replace(/gemini-2\.5-flash/i, "Gemini 2.5 Flash")
                    : "GPT-OSS 20B (Groq)"}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
