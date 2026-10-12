"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  Trophy, HeartHandshake, Sliders, ArrowRight, ShieldCheck, 
  HelpCircle, Sparkles, User, RefreshCw, BarChart2, Eye
} from "lucide-react";
import { api } from "@/lib/api";

function RankingsContent() {
  const searchParams = useSearchParams();
  const initialParticipantId = searchParams.get("participant_id") || "";

  const [participants, setParticipants] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState(initialParticipantId);
  const [rankingData, setRankingData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Weights Drawer / Config
  const [showWeights, setShowWeights] = useState(false);
  const [weights, setWeights] = useState({
    weight_preferences: 0.25,
    weight_shared_interests: 0.25,
    weight_lifestyle_fit: 0.20,
    weight_date_engagement: 0.20,
    weight_values_priorities: 0.10,
  });
  const [recalculating, setRecalculating] = useState(false);

  useEffect(() => {
    api.getParticipants({ limit: 50 }).then((data) => {
      setParticipants(data || []);
      if (!selectedId && data && data.length > 0) {
        setSelectedId(data[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    api.getRankings(selectedId)
      .then((data) => {
        setRankingData(data);
        if (data.weights_used) setWeights(data.weights_used);
      })
      .catch((err) => console.error("Failed to load rankings:", err))
      .finally(() => setLoading(false));
  }, [selectedId]);

  const handleUpdateWeights = async () => {
    if (!selectedId) return;
    setRecalculating(true);
    try {
      const updated = await api.recalculateRankings(selectedId, weights);
      setRankingData(updated);
    } catch (err) {
      console.error("Recalculate error:", err);
    } finally {
      setRecalculating(false);
    }
  };

  const selectedParticipant = participants.find((p) => p.id === selectedId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold mb-2">
            <Trophy className="w-3.5 h-3.5" />
            <span>Explainable Compatibility Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Compatibility Rankings</h1>
          <p className="text-slate-400 text-sm mt-1">
            Ordered candidate suitability calculated with documented multi-attribute math and genuine date outcomes.
          </p>
        </div>

        <button
          onClick={() => setShowWeights(!showWeights)}
          className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2.5 rounded-xl text-xs font-semibold self-start sm:self-auto transition-colors"
        >
          <Sliders className="w-4 h-4 text-pink-400" />
          <span>{showWeights ? "Hide Weight Controls" : "Adjust Scoring Weights"}</span>
        </button>
      </div>

      {/* Participant Selector Strip */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Evaluate For:</span>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 font-semibold focus:outline-none focus:border-pink-500"
          >
            {participants.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.location || "California"})
              </option>
            ))}
          </select>
        </div>

        {selectedParticipant && (
          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <span>Identity: <strong className="text-white">{selectedParticipant.gender}</strong></span>
            <span>&bull;</span>
            <span>Target: <strong className="text-white">{selectedParticipant.target_gender || "Any"}</strong></span>
            <span>&bull;</span>
            <Link href={`/participants/${selectedId}`} className="text-pink-400 hover:underline flex items-center space-x-1">
              <span>View Source Evidence</span>
              <Eye className="w-3 h-3" />
            </Link>
          </div>
        )}
      </div>

      {/* Configurable Weights Drawer */}
      {showWeights && (
        <div className="bg-slate-900/90 border border-slate-700 rounded-2xl p-6 space-y-4 animate-in fade-in duration-200 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">Configurable Component Weights</h2>
              <p className="text-[11px] text-slate-400">Fine-tune the provisional heuristic weights. Scores normalize automatically.</p>
            </div>
            <button
              onClick={handleUpdateWeights}
              disabled={recalculating}
              className="bg-pink-600 hover:bg-pink-500 text-white px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 flex items-center space-x-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculating ? "animate-spin" : ""}`} />
              <span>Recalculate Leaderboard</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
            <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] font-semibold text-slate-300 block">Stated Preferences</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weights.weight_preferences}
                onChange={(e) => setWeights({ ...weights, weight_preferences: Number(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
              />
              <span className="text-[10px] text-slate-500">Weight: {(weights.weight_preferences * 100).toFixed(0)}%</span>
            </div>

            <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] font-semibold text-slate-300 block">Shared Interests</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weights.weight_shared_interests}
                onChange={(e) => setWeights({ ...weights, weight_shared_interests: Number(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
              />
              <span className="text-[10px] text-slate-500">Weight: {(weights.weight_shared_interests * 100).toFixed(0)}%</span>
            </div>

            <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] font-semibold text-slate-300 block">Lifestyle Alignment</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weights.weight_lifestyle_fit}
                onChange={(e) => setWeights({ ...weights, weight_lifestyle_fit: Number(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
              />
              <span className="text-[10px] text-slate-500">Weight: {(weights.weight_lifestyle_fit * 100).toFixed(0)}%</span>
            </div>

            <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] font-semibold text-slate-300 block">Date Engagement</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weights.weight_date_engagement}
                onChange={(e) => setWeights({ ...weights, weight_date_engagement: Number(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
              />
              <span className="text-[10px] text-slate-500">Weight: {(weights.weight_date_engagement * 100).toFixed(0)}%</span>
            </div>

            <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] font-semibold text-slate-300 block">Values & Priorities</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weights.weight_values_priorities}
                onChange={(e) => setWeights({ ...weights, weight_values_priorities: Number(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
              />
              <span className="text-[10px] text-slate-500">Weight: {(weights.weight_values_priorities * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Rankings Leaderboard */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Computing explainable candidate rankings...</p>
        </div>
      ) : !rankingData?.rankings || rankingData.rankings.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-2xl space-y-3">
          <Trophy className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No candidate rankings available</h3>
          <p className="text-xs text-slate-500">Execute dating simulations to populate match rankings.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Tie-Breaking Rule: <strong className="text-slate-300">{rankingData.deterministic_rule}</strong></span>
            <span>Candidates Ranked: <strong className="text-white">{rankingData.rankings.length}</strong></span>
          </div>

          <div className="space-y-4">
            {rankingData.rankings.map((r: any) => (
              <div
                key={r.id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center space-x-4">
                    {/* Rank Badge */}
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-extrabold text-base shadow ${
                      r.rank === 1
                        ? "bg-gradient-to-tr from-amber-500 to-yellow-300 text-slate-950 border border-amber-300"
                        : r.rank === 2
                        ? "bg-gradient-to-tr from-slate-400 to-slate-200 text-slate-950 border border-slate-300"
                        : r.rank === 3
                        ? "bg-gradient-to-tr from-amber-700 to-amber-600 text-white border border-amber-500"
                        : "bg-slate-800 text-slate-300 border border-slate-700"
                    }`}>
                      #{r.rank}
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                        <span>{r.target_name}</span>
                      </h3>
                      <p className="text-xs text-slate-400">{r.supporting_evidence_summary}</p>
                    </div>
                  </div>

                  {/* Dual Score Badges */}
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <span className="block text-[10px] text-slate-400 uppercase font-semibold">Harmonized Reciprocal</span>
                      <strong className="text-xl font-extrabold text-pink-400">{r.reciprocal_score}%</strong>
                    </div>
                    <div className="w-px h-8 bg-slate-800" />
                    <div className="text-right">
                      <span className="block text-[10px] text-slate-400 uppercase font-semibold">Directional (A&rarr;B)</span>
                      <strong className="text-xl font-bold text-slate-200">{r.individual_score}%</strong>
                    </div>
                  </div>
                </div>

                {/* Score Components Breakdown Bars */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Preferences</span>
                      <strong className="text-slate-200">{r.preference_score}%</strong>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-pink-500 h-1 rounded-full" style={{ width: `${r.preference_score}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Interests</span>
                      <strong className="text-slate-200">{r.interest_score}%</strong>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-purple-500 h-1 rounded-full" style={{ width: `${r.interest_score}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Lifestyle</span>
                      <strong className="text-slate-200">{r.lifestyle_score}%</strong>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${r.lifestyle_score}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Date Flow</span>
                      <strong className="text-slate-200">{r.engagement_score}%</strong>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-sky-500 h-1 rounded-full" style={{ width: `${r.engagement_score}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Confidence</span>
                      <strong className="text-slate-200">{Math.round(r.confidence_score * 100)}%</strong>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-amber-500 h-1 rounded-full" style={{ width: `${r.confidence_score * 100}%` }} />
                    </div>
                  </div>
                </div>

                {/* Shared Interests & Incompatibilities */}
                <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                  {r.shared_interests?.map((item: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px]">
                      &check; {item}
                    </span>
                  ))}
                  {r.potential_incompatibilities?.map((item: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 text-[10px]">
                      &times; {item}
                    </span>
                  ))}
                </div>

                {/* Ranking Rationale Box */}
                <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Transparent Rationale:
                  </span>
                  <p className="leading-relaxed">{r.ranking_explanation}</p>
                </div>

                {/* Action Links */}
                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                  <Link
                    href={`/participants/${r.target_participant_id}`}
                    className="text-slate-400 hover:text-white flex items-center space-x-1"
                  >
                    <span>Inspect {r.target_name}&rsquo;s Profile</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  {r.session_id ? (
                    <Link
                      href={`/dates/${r.session_id}`}
                      className="bg-slate-800 hover:bg-slate-700 text-pink-400 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1 font-semibold transition-colors"
                    >
                      <span>Replay Supporting Date</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  ) : (
                    <span className="text-[11px] text-slate-500">Date pending simulation</span>
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

export default function CompatibilityRankingsPage() {
  return (
    <Suspense fallback={
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Loading candidate rankings...</p>
      </div>
    }>
      <RankingsContent />
    </Suspense>
  );
}
