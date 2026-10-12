"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  History, Heart, ArrowRight, Clock, CheckCircle2, 
  AlertTriangle, Filter, Sparkles, PlayCircle
} from "lucide-react";
import { api } from "@/lib/api";

export default function SessionHistoryPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getDates({ status_filter: statusFilter })
      .then((data) => setSessions(data || []))
      .catch((err) => console.error("Failed to load sessions:", err))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold mb-2">
            <History className="w-3.5 h-3.5" />
            <span>Persisted Dating Ledger</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Dating Session History</h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse genuine multi-turn interaction records with observable messages, independent evaluations, and outcomes.
          </p>
        </div>

        <Link
          href="/dates/live"
          className="inline-flex items-center space-x-2 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-medium px-4 py-2.5 rounded-xl shadow-lg shadow-pink-600/20 text-xs self-start sm:self-auto transition-all"
        >
          <PlayCircle className="w-4 h-4" />
          <span>Launch New Live Date</span>
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-3 rounded-xl">
        <span className="text-xs text-slate-400">Total Persisted Sessions: <strong className="text-slate-200">{sessions.length}</strong></span>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-pink-500"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed Only</option>
            <option value="incompatible">Incompatible / Polite Pass</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse h-24" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-2xl space-y-3">
          <History className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No dating sessions recorded yet</h3>
          <p className="text-xs text-slate-500">Run a live simulation or trigger the demo benchmark to populate history.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center -space-x-2">
                    <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center text-xs font-bold text-white border-2 border-slate-900">
                      {s.participant_a_name?.[0] || "A"}
                    </div>
                    <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-xs font-bold text-white border-2 border-slate-900">
                      {s.participant_b_name?.[0] || "B"}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      {s.participant_a_name} &bull; {s.participant_b_name}
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Executed {new Date(s.started_at).toLocaleDateString()} at {new Date(s.started_at).toLocaleTimeString()} &bull; {s.total_turns} turns
                    </p>
                  </div>
                </div>

                <p className="text-xs text-slate-300 line-clamp-1 max-w-2xl">
                  {s.outcome_summary || "Autonomous coffee date completed."}
                </p>

                <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-mono">
                  <span>Tokens: {s.total_tokens_used}</span>
                  <span>&bull;</span>
                  <span>Cost: ${s.approx_cost_usd?.toFixed(4)}</span>
                  <span>&bull;</span>
                  <span>Latency: {s.latency_ms}ms</span>
                </div>
              </div>

              <div className="flex items-center space-x-3 self-end sm:self-center">
                <span
                  className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wider ${
                    s.outcome_status === "second_date_agreed"
                      ? "bg-pink-500/10 text-pink-400 border border-pink-500/30"
                      : s.outcome_status === "mutual_friendship"
                      ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                      : "bg-slate-700/50 text-slate-300 border border-slate-600/50"
                  }`}
                >
                  {s.outcome_status?.replace(/_/g, " ") || s.status}
                </span>

                <Link
                  href={`/dates/${s.id}`}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2 rounded-xl border border-slate-700 flex items-center space-x-1.5 transition-colors whitespace-nowrap"
                >
                  <span>Replay Session</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
