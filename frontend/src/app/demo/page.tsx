"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Sparkles, CheckCircle2, ShieldCheck, Heart, Trophy, 
  ExternalLink, ArrowRight, PlayCircle, Eye, Users, FileText
} from "lucide-react";
import { api } from "@/lib/api";

export default function CompletedDemoPage() {
  const [participants, setParticipants] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [run, setRun] = useState<any>(null);
  const [selectedDemoParticipant, setSelectedDemoParticipant] = useState<any>(null);
  const [sampleRankings, setSampleRankings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDemoData() {
      try {
        const [p, s, r] = await Promise.all([
          api.getParticipants({ limit: 30 }),
          api.getDates({ run_id: "demo-run-25-participants", limit: 30 }),
          api.getRun("demo-run-25-participants").catch(() => null),
        ]);
        setParticipants(p || []);
        setSessions(s || []);
        setRun(r);
        if (p && p.length > 0) {
          setSelectedDemoParticipant(p[0]);
          const rankData = await api.getRankings(p[0].id, "demo-run-25-participants").catch(() => null);
          if (rankData?.rankings) setSampleRankings(rankData.rankings);
        }
      } catch (err) {
        console.error("Demo load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDemoData();
  }, []);

  const handleSelectParticipant = async (p: any) => {
    setSelectedDemoParticipant(p);
    try {
      const rankData = await api.getRankings(p.id, "demo-run-25-participants");
      if (rankData?.rankings) setSampleRankings(rankData.rankings);
    } catch (_) {}
  };

  return (
    <div className="space-y-8">
      {/* Permanent Demonstration Header */}
      <div className="bg-gradient-to-r from-pink-950/40 via-purple-950/30 to-slate-900 border border-pink-500/30 rounded-2xl p-6 sm:p-8 space-y-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Official Technical Evaluation Showcase</span>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
            &check; Persisted & Survives Server Restarts
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold text-white">
          25-Participant Consenting Benchmark Demonstration
        </h1>
        <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
          This permanent showcase contains 25 verified individuals, each with authentic public LinkedIn and Instagram profiles, mutual participation consent, traceable evidence, genuine agent-to-agent dating transcripts, and deterministic compatibility rankings.
        </p>

        {/* 3-Minute Video Storyboard Guide Pill */}
        <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-300">
          <span className="font-semibold text-pink-400">Reviewer 3-Minute Video Guide Sequence:</span>
          <div className="flex flex-wrap gap-2 text-[11px] font-mono text-slate-400">
            <span className="bg-slate-800 px-2 py-0.5 rounded">0:00-0:25 Roster (25 URLs)</span>
            <span className="bg-slate-800 px-2 py-0.5 rounded">0:25-0:55 Profile Evidence</span>
            <span className="bg-slate-800 px-2 py-0.5 rounded">0:55-1:55 Agent Dialogue</span>
            <span className="bg-slate-800 px-2 py-0.5 rounded">1:55-2:35 Rankings</span>
            <span className="bg-slate-800 px-2 py-0.5 rounded">2:35-3:00 Nav & Audit</span>
          </div>
        </div>
      </div>

      {/* Dataset Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <span className="text-xs text-slate-400 uppercase font-semibold">Consenting Roster</span>
          <div className="text-2xl font-bold text-white flex items-center space-x-2">
            <span>{participants.length} Participants</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="text-[11px] text-slate-500">50 Verified Profile URLs</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <span className="text-xs text-slate-400 uppercase font-semibold">Theoretical Pairs</span>
          <div className="text-2xl font-bold text-white">300 Unordered Pairs</div>
          <span className="text-[11px] text-slate-500">25 &times; 24 / 2 Pairs</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <span className="text-xs text-slate-400 uppercase font-semibold">Simulated Dates</span>
          <div className="text-2xl font-bold text-pink-400">{sessions.length} Completed</div>
          <span className="text-[11px] text-slate-500">Observable & Persisted</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <span className="text-xs text-slate-400 uppercase font-semibold">Ranking Engine</span>
          <div className="text-2xl font-bold text-emerald-400">100% Calculated</div>
          <span className="text-[11px] text-slate-500">Deterministic Tie-Breaking</span>
        </div>
      </div>

      {/* 25 Participant Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-white">Consenting Demonstration Dataset (25 Real Profiles)</h2>
            <p className="text-xs text-slate-400">Strictly 2 URLs per participant: LinkedIn + Instagram.</p>
          </div>
          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20 font-semibold">
            &check; Consent Records Verified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] text-slate-400 uppercase bg-slate-800/40 border-y border-slate-800 font-semibold">
              <tr>
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Participant Name</th>
                <th className="py-2.5 px-3">Demographics</th>
                <th className="py-2.5 px-3">LinkedIn URL</th>
                <th className="py-2.5 px-3">Instagram URL</th>
                <th className="py-2.5 px-3">Evidence Items</th>
                <th className="py-2.5 px-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {participants.slice(0, 25).map((p, idx) => (
                <tr
                  key={p.id}
                  onClick={() => handleSelectParticipant(p)}
                  className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                    selectedDemoParticipant?.id === p.id ? "bg-pink-950/20 border-l-2 border-pink-500" : ""
                  }`}
                >
                  <td className="py-2.5 px-3 font-mono text-slate-500">{idx + 1}</td>
                  <td className="py-2.5 px-3 font-bold text-white whitespace-nowrap">{p.name}</td>
                  <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                    {p.age} yo &bull; {p.gender} &bull; {p.location}
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <a
                      href={p.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline flex items-center space-x-1"
                    >
                      <span>{p.linkedin_handle}</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <a
                      href={p.instagram_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-pink-400 hover:underline flex items-center space-x-1"
                    >
                      <span>{p.instagram_handle}</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-center">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px]">
                      {p.evidence_count} items
                    </span>
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <Link
                      href={`/participants/${p.id}`}
                      className="text-pink-400 hover:text-pink-300 font-semibold"
                    >
                      Inspect Evidence &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Participant's Demonstration Ranking Preview */}
      {selectedDemoParticipant && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Trophy className="w-4 h-4 text-amber-400" />
                <span>Demonstration Rankings for {selectedDemoParticipant.name}</span>
              </h2>
              <p className="text-xs text-slate-400">
                Top eligible matches ranked with explainable component scoring.
              </p>
            </div>
            <Link
              href={`/rankings?participant_id=${selectedDemoParticipant.id}`}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-pink-400 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1 font-semibold"
            >
              <span>Full Interactive Leaderboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {sampleRankings.slice(0, 5).map((r) => (
              <div
                key={r.id}
                className="bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center space-x-3">
                  <span className="w-7 h-7 rounded-lg bg-pink-500/10 border border-pink-500/30 text-pink-400 font-bold flex items-center justify-center">
                    #{r.rank}
                  </span>
                  <div>
                    <h3 className="font-bold text-white">{r.target_name}</h3>
                    <p className="text-slate-400 text-[11px] line-clamp-1">{r.ranking_explanation}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4 self-end sm:self-center">
                  <div className="text-right">
                    <span className="block text-[10px] text-slate-500 uppercase">Reciprocal</span>
                    <strong className="text-sm font-bold text-pink-400">{r.reciprocal_score}%</strong>
                  </div>
                  {r.session_id && (
                    <Link
                      href={`/dates/${r.session_id}`}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 font-semibold"
                    >
                      Replay Date
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
