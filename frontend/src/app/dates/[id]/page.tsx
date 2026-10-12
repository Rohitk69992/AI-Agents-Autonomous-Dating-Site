"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, Heart, MessageSquare, Brain, CheckCircle2, 
  History, ShieldCheck, Clock, ExternalLink, AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";

export default function SessionReplayPage() {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedThoughts, setExpandedThoughts] = useState<{ [turn: number]: boolean }>({});

  useEffect(() => {
    if (!id) return;
    api.getDateSession(id)
      .then((data) => setSession(data))
      .catch((err) => console.error("Failed to load session:", err))
      .finally(() => setLoading(false));
  }, [id]);

  const toggleThought = (turn: number) => {
    setExpandedThoughts((prev) => ({ ...prev, [turn]: !prev[turn] }));
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Loading persisted dating transcript...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="py-20 text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Dating Session Not Found</h2>
        <Link href="/dates" className="text-xs text-pink-400 underline">Back to Session History</Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/dates"
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Session History</span>
        </Link>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
          <History className="w-3.5 h-3.5" />
          <span>REPLAY MODE &bull; Persisted Genuine Record</span>
        </div>
      </div>

      {/* Outcome Header Banner */}
      <div
        className={`p-6 sm:p-8 rounded-2xl border ${
          session.outcome_status === "second_date_agreed"
            ? "bg-gradient-to-r from-pink-900/30 to-rose-900/20 border-pink-500/40"
            : session.outcome_status === "mutual_friendship"
            ? "bg-gradient-to-r from-purple-900/30 to-indigo-900/20 border-purple-500/40"
            : "bg-slate-900 border-slate-700"
        } space-y-4 shadow-xl`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-pink-600/20 border border-pink-500/30 flex items-center justify-center">
              <Heart className={`w-6 h-6 ${session.outcome_status === "second_date_agreed" ? "text-pink-400 fill-pink-400" : "text-slate-400"}`} />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">
                {session.participant_a_name} &bull; {session.participant_b_name}
              </h1>
              <span className="text-xs text-slate-400">
                Outcome: <strong className="text-white capitalize">{session.outcome_status?.replace(/_/g, " ")}</strong>
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 text-xs font-mono">
            <span className="bg-slate-800/80 px-2.5 py-1 rounded-md text-slate-300 border border-slate-700">
              Turns: {session.total_turns}
            </span>
            <span className="bg-slate-800/80 px-2.5 py-1 rounded-md text-emerald-400 border border-slate-700">
              Engagement: {Math.round(session.mutual_engagement_score * 100)}%
            </span>
            <span className="bg-slate-800/80 px-2.5 py-1 rounded-md text-slate-300 border border-slate-700">
              Latency: {session.latency_ms}ms
            </span>
          </div>
        </div>

        <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/40 p-4 rounded-xl border border-slate-800">
          {session.outcome_summary}
        </p>

        {session.shared_interests_found?.length > 0 && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-emerald-400 font-semibold">Shared Ground:</span>
            <div className="flex flex-wrap gap-1.5">
              {session.shared_interests_found.map((s: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[11px]">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Transcript of Messages */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <MessageSquare className="w-4 h-4 text-pink-400" />
            <span>Persisted Dialogue Record ({session.messages?.length || 0} Alternating Turns)</span>
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">Session ID: {session.id.substring(0, 8)}...</span>
        </div>

        <div className="space-y-6">
          {session.messages?.map((msg: any) => {
            const isAgentA = msg.sender_agent_role === "Agent A";
            const isThoughtOpen = expandedThoughts[msg.turn_number];
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isAgentA ? "items-start" : "items-end"} space-y-2`}
              >
                <div className="flex items-center space-x-2 text-xs text-slate-400 px-1">
                  <span className={`font-bold ${isAgentA ? "text-pink-400" : "text-purple-400"}`}>
                    {msg.sender_name || msg.sender_agent_role}
                  </span>
                  <span className="text-[10px] text-slate-500">&bull; Turn {msg.turn_number}</span>
                </div>

                <div
                  className={`max-w-xl p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isAgentA
                      ? "bg-slate-800/90 border border-slate-700 text-slate-100 rounded-tl-sm"
                      : "bg-pink-950/40 border border-pink-500/30 text-pink-50 rounded-tr-sm"
                  } space-y-2.5 shadow-md`}
                >
                  <p>{msg.content}</p>

                  {(msg.question_asked || msg.interest_referenced) && (
                    <div className="pt-2 border-t border-slate-700/60 flex flex-wrap gap-2 text-[10px]">
                      {msg.interest_referenced && (
                        <span className="bg-slate-900/60 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">
                          Topic: {msg.interest_referenced}
                        </span>
                      )}
                      {msg.question_asked && (
                        <span className="bg-pink-500/10 text-pink-300 px-2 py-0.5 rounded-md border border-pink-500/20">
                          Question: {msg.question_asked}
                        </span>
                      )}
                    </div>
                  )}

                  {(msg.decision_summary || msg.internal_thought) && (
                    <div className="pt-1">
                      <button
                        onClick={() => toggleThought(msg.turn_number)}
                        className="inline-flex items-center space-x-1.5 text-[10px] text-slate-400 hover:text-pink-300 font-mono transition-colors"
                      >
                        <Brain className="w-3 h-3 text-pink-400" />
                        <span>{isThoughtOpen ? "Hide Decision Factors" : "Inspect Decision Strategy"}</span>
                      </button>
                      {isThoughtOpen && (
                        <div className="mt-2 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1.5">
                          <span className="text-[10px] uppercase font-bold text-pink-400 block tracking-wider">
                            Observable Decision Factors:
                          </span>
                          <p className="leading-relaxed text-slate-200">
                            {msg.decision_summary || msg.internal_thought}
                          </p>
                          {msg.decision_factors && msg.decision_factors.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {msg.decision_factors.map((f: string, fi: number) => (
                                <span key={fi} className="px-1.5 py-0.5 rounded bg-slate-800 text-[9px] text-slate-300 border border-slate-700">
                                  {f}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Evaluations Screen */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <h2 className="text-sm font-bold text-white flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Independent Post-Date Agent Evaluations</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {session.evaluations?.map((ev: any, idx: number) => (
            <div key={idx} className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    {ev.evaluator_name}&rsquo;s Evaluation of {ev.target_name}
                  </h3>
                  <span className="text-[10px] text-slate-400">Post-Date Reflection</span>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                    ev.would_date_again
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {ev.would_date_again ? "Second Date: YES" : "Second Date: NO"}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                  <span className="block text-[10px] text-slate-400">Chemistry</span>
                  <strong className="text-sm font-bold text-pink-400">{ev.chemistry_score}/10</strong>
                </div>
                <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                  <span className="block text-[10px] text-slate-400">Comfort</span>
                  <strong className="text-sm font-bold text-purple-400">{ev.communication_comfort}/10</strong>
                </div>
                <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                  <span className="block text-[10px] text-slate-400">Values</span>
                  <strong className="text-sm font-bold text-emerald-400">{ev.shared_values_alignment}/10</strong>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-900/40 p-3 rounded-lg border border-slate-800">
                &ldquo;{ev.evaluation_rationale}&rdquo;
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
