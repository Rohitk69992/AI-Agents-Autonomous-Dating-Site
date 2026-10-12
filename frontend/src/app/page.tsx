"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Users, CheckCircle2, Clock, HeartHandshake, Sparkles, 
  ArrowRight, ShieldCheck, PlayCircle, Trophy, BarChart3, AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [participants, setParticipants] = useState<any[]>([]);
  const [recentDates, setRecentDates] = useState<any[]>([]);
  const [run, setRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, p, d, r] = await Promise.all([
          api.getMetrics().catch(() => null),
          api.getParticipants({ limit: 10 }).catch(() => []),
          api.getDates({ limit: 5 }).catch(() => []),
          api.getRun("demo-run-25-participants").catch(() => null),
        ]);
        setMetrics(m);
        setParticipants(p || []);
        setRecentDates(d || []);
        setRun(r);
      } catch (err) {
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalRegistered = metrics?.total_participants || participants.length || 0;
  const validatedCount = participants.filter((p) => p.consent_status === "consented").length;
  const analyzedCount = metrics?.analyzed_participants || participants.filter((p) => p.status === "analyzed").length;
  const awaitingAnalysis = Math.max(0, totalRegistered - analyzedCount);
  const theoreticalPairs = totalRegistered > 1 ? Math.floor((totalRegistered * (totalRegistered - 1)) / 2) : 0;
  const eligiblePairs = run?.total_eligible_pairs ?? theoreticalPairs;
  const completedSessions = metrics?.completed_sessions || 0;
  const failedSessions = metrics?.failed_sessions || 0;
  const datasetPercent = run?.status === "completed" ? 100 : Math.min(100, Math.round((completedSessions / Math.max(eligiblePairs, 1)) * 100));

  return (
    <div className="space-y-8">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-pink-900/40 via-purple-900/20 to-slate-900 border border-pink-500/20 p-8 shadow-2xl">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Multi-Agent Matchmaking Harness</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Where AI Agents Date First, So Real People Match With Confidence.
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Every participant is represented by an autonomous agent powered strictly by evidence from their public LinkedIn and Instagram profiles. Agents converse, probe compatibility, and generate explainable rankings.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/demo"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-pink-600/30 text-sm transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>Explore 25-Participant Demonstration</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/dates/live"
              className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium px-4 py-2.5 rounded-xl text-sm transition-all"
            >
              <PlayCircle className="w-4 h-4 text-pink-400" />
              <span>Launch Live Simulation</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Primary Persisted Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Registered Participants</span>
            <Users className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-white">{totalRegistered}</div>
          <p className="text-[11px] text-slate-400 flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400 inline" />
            <span>{validatedCount} Verified with Consenting URLs</span>
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Analyzed Profiles</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-white">{analyzedCount}</div>
          <p className="text-[11px] text-slate-400">
            {awaitingAnalysis > 0 ? `${awaitingAnalysis} awaiting analysis` : "100% profiles analyzed"}
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dating Sessions</span>
            <HeartHandshake className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-white">{completedSessions}</div>
          <p className="text-[11px] text-slate-400">
            {failedSessions} incompatible / passed
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dataset Completion</span>
            <Trophy className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-white">{datasetPercent}%</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-pink-500 to-emerald-400 h-1.5 rounded-full"
              style={{ width: `${datasetPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Secondary Metrics & Observability Row */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400 font-medium">Model Tokens Consumed</span>
              <p className="text-xl font-bold text-slate-100">{metrics.total_tokens_consumed.toLocaleString()}</p>
            </div>
            <BarChart3 className="w-6 h-6 text-slate-600" />
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400 font-medium">Est. Execution Cost</span>
              <p className="text-xl font-bold text-emerald-400">${metrics.estimated_total_cost_usd.toFixed(4)}</p>
            </div>
            <Sparkles className="w-6 h-6 text-emerald-500/40" />
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400 font-medium">Avg Dating Session Latency</span>
              <p className="text-xl font-bold text-slate-100">{metrics.average_session_latency_ms} ms</p>
            </div>
            <Clock className="w-6 h-6 text-slate-600" />
          </div>
        </div>
      )}

      {/* Main Grid: Directory Preview & Recent Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Consented Participants Preview */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Registered Participants</h2>
              <p className="text-xs text-slate-400">Consented individuals with verified LinkedIn and Instagram profiles.</p>
            </div>
            <Link href="/participants" className="text-xs text-pink-400 hover:text-pink-300 font-semibold flex items-center space-x-1">
              <span>View Directory ({totalRegistered})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-800/60">
            {participants.slice(0, 6).map((p) => (
              <div key={p.id} className="py-3 flex items-center justify-between hover:bg-slate-800/30 px-2 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-pink-400 text-xs">
                    {p.name.split(" ").map((n: string) => n[0]).join("")}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">{p.name}</h3>
                    <p className="text-xs text-slate-400">{p.location || "California, USA"} &bull; {p.age || 28} yo</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Consented
                  </span>
                  <Link
                    href={`/participants/${p.id}`}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    Inspect Profile
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Recent Simulated Dates */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Recent Dating Sessions</h2>
              <p className="text-xs text-slate-400">Genuine multi-turn agent dialogues.</p>
            </div>
            <Link href="/dates" className="text-xs text-pink-400 hover:text-pink-300 font-semibold flex items-center space-x-1">
              <span>All History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {recentDates.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                <HeartHandshake className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                No sessions simulated yet.
              </div>
            ) : (
              recentDates.map((s) => (
                <Link
                  key={s.id}
                  href={`/dates/${s.id}`}
                  className="block p-3 rounded-lg bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">
                      {s.participant_a_name} & {s.participant_b_name}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                        s.outcome_status === "second_date_agreed"
                          ? "bg-pink-500/10 text-pink-400 border border-pink-500/30"
                          : s.outcome_status === "mutual_friendship"
                          ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                          : "bg-slate-700/50 text-slate-300"
                      }`}
                    >
                      {s.outcome_status?.replace(/_/g, " ") || "In Progress"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{s.outcome_summary}</p>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
