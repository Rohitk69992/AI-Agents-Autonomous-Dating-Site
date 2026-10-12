"use client";

import { useEffect, useState } from "react";
import { 
  PlayCircle, RefreshCw, Heart, MessageSquare, Brain, 
  Sparkles, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, HelpCircle
} from "lucide-react";
import { api } from "@/lib/api";

function checkPairEligibility(pA: any, pB: any): { eligible: boolean; reason?: string } {
  if (!pA || !pB) return { eligible: false, reason: "Select two distinct participants." };
  if (pA.id === pB.id) return { eligible: false, reason: "Cannot date self." };
  if (pA.status === "withdrawn") return { eligible: false, reason: `${pA.name} has withdrawn their profile.` };
  if (pB.status === "withdrawn") return { eligible: false, reason: `${pB.name} has withdrawn their profile.` };
  if (pA.consent_status !== "consented" && pA.consent_status !== "verified") {
    return { eligible: false, reason: `${pA.name} has not verified consent.` };
  }
  if (pB.consent_status !== "consented" && pB.consent_status !== "verified") {
    return { eligible: false, reason: `${pB.name} has not verified consent.` };
  }
  if (pA.simulation_eligible === false) return { eligible: false, reason: `${pA.name} is not simulation eligible.` };
  if (pB.simulation_eligible === false) return { eligible: false, reason: `${pB.name} is not simulation eligible.` };

  const openTargets = ["any", "all", "everyone", "open"];
  const tgA = pA.target_gender?.toLowerCase()?.trim();
  const gB = pB.gender?.toLowerCase()?.trim();
  if (tgA && gB && !openTargets.includes(tgA) && tgA !== gB) {
    return { eligible: false, reason: `Gender mismatch: ${pA.name} seeks ${pA.target_gender}, but ${pB.name} is ${pB.gender}.` };
  }

  const tgB = pB.target_gender?.toLowerCase()?.trim();
  const gA = pA.gender?.toLowerCase()?.trim();
  if (tgB && gA && !openTargets.includes(tgB) && tgB !== gA) {
    return { eligible: false, reason: `Gender mismatch: ${pB.name} seeks ${pB.target_gender}, but ${pA.name} is ${pA.gender}.` };
  }

  return { eligible: true };
}

export default function LiveDatingSimulationPage() {
  const [participants, setParticipants] = useState<any[]>([]);
  const [partAId, setPartAId] = useState("");
  const [partBId, setPartBId] = useState("");
  const [maxTurns, setMaxTurns] = useState(6);
  const [onlyCompatible, setOnlyCompatible] = useState(true);

  const [simulating, setSimulating] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedThoughts, setExpandedThoughts] = useState<{ [turn: number]: boolean }>({});

  useEffect(() => {
    api.getParticipants({ limit: 50 }).then((data) => {
      const list = data || [];
      setParticipants(list);
      if (list.length >= 2) {
        // Find default compatible pair: prioritize Aarav & Ananya or first mutually compatible pair
        let foundA = list[0].id;
        let foundB = list[1].id;

        const demo1 = list.find((p: any) => p.name?.includes("Aarav"));
        const demo2 = list.find((p: any) => p.name?.includes("Ananya"));
        if (demo1 && demo2 && checkPairEligibility(demo1, demo2).eligible) {
          foundA = demo1.id;
          foundB = demo2.id;
        } else {
          let matched = false;
          for (let i = 0; i < list.length && !matched; i++) {
            for (let j = 0; j < list.length && !matched; j++) {
              if (i !== j && checkPairEligibility(list[i], list[j]).eligible) {
                foundA = list[i].id;
                foundB = list[j].id;
                matched = true;
              }
            }
          }
        }
        setPartAId(foundA);
        setPartBId(foundB);
      }
    });
  }, []);

  const partA = participants.find((p) => p.id === partAId);
  const partB = participants.find((p) => p.id === partBId);

  const candidatesForB = participants.filter((p) => {
    if (p.id === partAId) return false;
    if (onlyCompatible && partA) {
      return checkPairEligibility(partA, p).eligible;
    }
    return true;
  });

  useEffect(() => {
    if (candidatesForB.length > 0 && !candidatesForB.some((p) => p.id === partBId)) {
      setPartBId(candidatesForB[0].id);
    }
  }, [partAId, onlyCompatible, candidatesForB, partBId]);

  const eligibility = checkPairEligibility(partA, partB);

  const handleStartSimulation = async () => {
    if (!partAId || !partBId) return;
    if (partAId === partBId) {
      setErrorMsg("Please select two distinct participants for the simulated date.");
      return;
    }
    if (!eligibility.eligible) {
      setErrorMsg(eligibility.reason || "Selected participants are incompatible.");
      return;
    }

    setErrorMsg(null);
    setSimulating(true);
    setSession(null);
    setExpandedThoughts({});

    try {
      const result = await api.startDatingSession({
        participant_a_id: partAId,
        participant_b_id: partBId,
        max_turns: maxTurns,
      });
      setSession(result);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute dating simulation.");
    } finally {
      setSimulating(false);
    }
  };

  const toggleThought = (turn: number) => {
    setExpandedThoughts((prev) => ({ ...prev, [turn]: !prev[turn] }));
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold mb-2">
          <PlayCircle className="w-3.5 h-3.5" />
          <span>Observable Agent-to-Agent Harness</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">Live Dating Simulation</h1>
        <p className="text-slate-400 text-sm mt-1">
          Two autonomous agents engage in an unscripted, genuine coffee date, discovering mutual chemistry and evaluating compatibility independently.
        </p>
      </div>

      {/* Candidate Pair Selection Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Agent A Selector */}
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-pink-400 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-pink-500" />
              <span>Agent A (Initiating Date)</span>
            </label>
            <select
              value={partAId}
              onChange={(e) => setPartAId(e.target.value)}
              disabled={simulating}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-pink-500"
            >
              {participants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.gender || "Open"}, seeks {p.target_gender || "Open"}) &bull; {p.location || "India"}
                </option>
              ))}
            </select>
            {partA && (
              <p className="text-xs text-slate-400 italic">
                {partA.analyzed_profile?.summary || "Profile loaded"}
              </p>
            )}
          </div>

          {/* Agent B Selector */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-purple-400 flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-purple-500" />
                <span>Agent B (Responding Date)</span>
              </label>
              <label className="flex items-center space-x-1.5 cursor-pointer text-slate-400 hover:text-slate-200 select-none">
                <input
                  type="checkbox"
                  checked={onlyCompatible}
                  onChange={(e) => setOnlyCompatible(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-pink-600 focus:ring-0 text-xs"
                />
                <span className="text-[11px]">Compatible only</span>
              </label>
            </div>
            <select
              value={partBId}
              onChange={(e) => setPartBId(e.target.value)}
              disabled={simulating}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-pink-500"
            >
              {candidatesForB.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.gender || "Open"}, seeks {p.target_gender || "Open"}) &bull; {p.location || "India"}
                </option>
              ))}
            </select>
            {partB && (
              <p className="text-xs text-slate-400 italic">
                {partB.analyzed_profile?.summary || "Profile loaded"}
              </p>
            )}
          </div>
        </div>

        {/* Real-Time Pre-Flight Eligibility Badge */}
        <div
          className={`p-3.5 rounded-xl border flex items-center space-x-3 text-xs ${
            eligibility.eligible
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-amber-500/10 border-amber-500/30 text-amber-300"
          }`}
        >
          {eligibility.eligible ? (
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          )}
          <div className="flex-1">
            <span className="font-semibold block">
              {eligibility.eligible ? "Pre-Flight Status: Compatible Pair" : "Pre-Flight Status: Incompatible Selection"}
            </span>
            <span className="text-[11px] opacity-90">
              {eligibility.eligible
                ? "Mutual gender preferences aligned, consent verified, and both agents are eligible for autonomous simulation."
                : eligibility.reason}
            </span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800">
          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <span>Turns Limit:</span>
            {[4, 6, 8].map((t) => (
              <button
                key={t}
                onClick={() => setMaxTurns(t)}
                disabled={simulating}
                className={`px-3 py-1 rounded-lg font-mono text-xs ${
                  maxTurns === t ? "bg-pink-600 text-white font-bold" : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {t} Turns
              </button>
            ))}
          </div>

          <div className="flex flex-col items-end space-y-1 w-full sm:w-auto">
            <button
              onClick={handleStartSimulation}
              disabled={simulating || !partAId || !partBId || !eligibility.eligible}
              className="w-full sm:w-auto bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-semibold px-6 py-2.5 rounded-xl shadow-lg shadow-pink-600/30 text-xs flex items-center justify-center space-x-2 disabled:opacity-40 transition-all"
            >
              {simulating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Simulating Multi-Agent Date...</span>
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4" />
                  <span>Begin Autonomous Date</span>
                </>
              )}
            </button>
            {!eligibility.eligible && (
              <span className="text-[10px] text-amber-400/90 font-medium">
                Select a compatible candidate pair to enable date simulation.
              </span>
            )}
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Date Simulation Screen */}
      {session && (
        <div className="space-y-6">
          {/* Outcome Header Banner */}
          <div
            className={`p-6 rounded-2xl border ${
              session.outcome_status === "second_date_agreed"
                ? "bg-gradient-to-r from-pink-900/30 to-rose-900/20 border-pink-500/40"
                : session.outcome_status === "mutual_friendship"
                ? "bg-gradient-to-r from-purple-900/30 to-indigo-900/20 border-purple-500/40"
                : "bg-gradient-to-r from-slate-900 to-slate-800 border-slate-700"
            } space-y-3`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                <Heart className={`w-5 h-5 ${session.outcome_status === "second_date_agreed" ? "text-pink-400 fill-pink-400" : "text-slate-400"}`} />
                <h2 className="text-lg font-bold text-white capitalize">
                  Outcome: {session.outcome_status?.replace(/_/g, " ")}
                </h2>
                {session.is_synthetic ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                    SYNTHETIC SESSION
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                    VERIFIED PARTICIPANTS
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-3 text-xs font-mono text-slate-300">
                <span>Engagement: {Math.round(session.mutual_engagement_score * 100)}%</span>
                <span>&bull;</span>
                <span>Tokens: {session.total_tokens_used}</span>
                <span>&bull;</span>
                <span>Latency: {session.latency_ms}ms</span>
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{session.outcome_summary}</p>
          </div>

          {/* Turn-by-Turn Dialogue Stream */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-pink-400" />
                <span>Transcript of Conversation ({session.messages?.length || 0} Turns)</span>
              </h3>
              <span className="text-[11px] text-slate-500">Live Agent Interaction Record</span>
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

                    {/* Speech Bubble */}
                    <div
                      className={`max-w-xl p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        isAgentA
                          ? "bg-slate-800/90 border border-slate-700 text-slate-100 rounded-tl-sm"
                          : "bg-pink-950/40 border border-pink-500/30 text-pink-50 rounded-tr-sm"
                      } space-y-2.5 shadow-md`}
                    >
                      <p>{msg.content}</p>

                      {/* Observations Pill */}
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

                      {/* Expandable Agent Decision Strategy */}
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

          {/* Independent Post-Date Agent Evaluations */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Independent Post-Date Agent Evaluations</span>
              </h3>
              <p className="text-xs text-slate-400">
                After the conversation concluded, both agents reflected independently and recorded private scorecards.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {session.evaluations?.map((ev: any, idx: number) => (
                <div key={idx} className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                        {ev.evaluator_name}&rsquo;s Evaluation of {ev.target_name}
                      </h4>
                      <span className="text-[10px] text-slate-400">Private Scorecard</span>
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

                  {ev.perceived_green_flags?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">Observed Green Flags:</span>
                      <div className="flex flex-wrap gap-1">
                        {ev.perceived_green_flags.map((g: string, i: number) => (
                          <span key={i} className="text-[10px] bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/20">
                            {g}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {ev.perceived_red_flags?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold text-rose-400 uppercase tracking-wider">Perceived Concerns:</span>
                      <div className="flex flex-wrap gap-1">
                        {ev.perceived_red_flags.map((r: string, i: number) => (
                          <span key={i} className="text-[10px] bg-rose-500/10 text-rose-300 px-2 py-0.5 rounded border border-rose-500/20">
                            {r}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
