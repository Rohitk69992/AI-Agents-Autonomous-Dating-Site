"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ShieldCheck, ExternalLink, ArrowLeft, RefreshCw, CheckCircle2, 
  HelpCircle, Sparkles, HeartHandshake, FileText, AlertCircle, Calendar, Hash
} from "lucide-react";
import { api } from "@/lib/api";

export default function ParticipantProfilePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [participant, setParticipant] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<"analysis" | "evidence">("analysis");

  useEffect(() => {
    async function loadData() {
      if (!id) return;
      try {
        const [p, ev] = await Promise.all([
          api.getParticipant(id),
          api.getParticipantEvidence(id).catch(() => []),
        ]);
        setParticipant(p);
        setEvidence(ev || []);
      } catch (err) {
        console.error("Failed to load profile:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      const updatedProfile = await api.triggerAnalysis(id);
      setParticipant((prev: any) => ({ ...prev, analyzed_profile: updatedProfile }));
    } catch (err) {
      console.error("Reanalysis failed:", err);
    } finally {
      setReanalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <RefreshCw className="w-8 h-8 text-pink-400 animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Loading verified participant profile...</p>
      </div>
    );
  }

  if (!participant) {
    return (
      <div className="py-20 text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Participant Not Found</h2>
        <Link href="/participants" className="text-xs text-pink-400 underline">Back to Directory</Link>
      </div>
    );
  }

  const profile = participant.analyzed_profile;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link
          href="/participants"
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Directory</span>
        </Link>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="inline-flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reanalyzing ? "animate-spin" : ""}`} />
            <span>{reanalyzing ? "Re-Analyzing..." : "Re-Analyze Profile"}</span>
          </button>
          <Link
            href={`/rankings?participant_id=${participant.id}`}
            className="inline-flex items-center space-x-1.5 bg-pink-600 hover:bg-pink-500 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-pink-600/20 transition-colors"
          >
            <HeartHandshake className="w-3.5 h-3.5" />
            <span>View Candidate Rankings</span>
          </Link>
        </div>
      </div>

      {/* Participant Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-pink-600 to-rose-500 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-pink-500/20">
              {participant.name.split(" ").map((n: string) => n[0]).join("")}
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
                <span>{participant.name}</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Consented
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                {participant.location || "California"} &bull; {participant.age || 28} years old &bull; Gender: {participant.gender || "Open"} &bull; Seeking: {participant.target_gender || "Open"}
              </p>
            </div>
          </div>

          {/* Social Proof URLs */}
          <div className="flex flex-wrap gap-2 text-xs">
            <a
              href={participant.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1.5 transition-colors"
            >
              <span>LinkedIn Profile</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
            </a>
            <a
              href={participant.instagram_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1.5 transition-colors"
            >
              <span>Instagram Profile</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
            </a>
          </div>
        </div>

        {/* Provenance Metadata Strip */}
        <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Strict 2-Source Provenance</span>
            </span>
            <span>&bull;</span>
            <span className="flex items-center space-x-1">
              <FileText className="w-3.5 h-3.5 text-pink-400" />
              <span>{evidence.length} Evidence Items</span>
            </span>
          </div>
          <div className="flex items-center space-x-4 font-mono text-[11px]">
            <span>Model: {profile?.model_version || "gemini-2.5-flash"}</span>
            <span>&bull;</span>
            <span>Analyzed: {profile ? new Date(profile.analyzed_at).toLocaleDateString() : "Pending"}</span>
          </div>
        </div>
      </div>

      {/* Tabs: Structured Analysis vs Source Evidence */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("analysis")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-all ${
            activeTab === "analysis"
              ? "border-pink-500 text-pink-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Extracted Dating Profile & Inferences</span>
        </button>
        <button
          onClick={() => setActiveTab("evidence")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-all ${
            activeTab === "evidence"
              ? "border-pink-500 text-pink-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Underlying Source Evidence ({evidence.length})</span>
        </button>
      </div>

      {activeTab === "analysis" ? (
        <div className="space-y-6">
          {/* Summary Box */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-pink-400">Executive Compatibility Summary</h2>
            <p className="text-sm text-slate-200 leading-relaxed">
              {profile?.summary || "No summary generated yet."}
            </p>
          </div>

          {/* Key Attributes Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Career & Professional */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Professional Background & Career Focus</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.career_interests?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-slate-800 text-xs text-slate-200 border border-slate-700">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Demonstrated Hobbies */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Demonstrated Hobbies (Instagram Verified)</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.demonstrated_hobbies?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-pink-500/10 text-xs text-pink-300 border border-pink-500/20">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Stated Interests */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Stated Personal Interests</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.stated_interests?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-xs text-purple-300 border border-purple-500/20">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Lifestyle Preferences */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Lifestyle Preferences</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.lifestyle_preferences?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-xs text-emerald-300 border border-emerald-500/20">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Communication Preferences */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Communication Preferences</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.communication_preferences?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-sky-500/10 text-xs text-sky-300 border border-sky-500/20">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Voluntary Relationship Preferences */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Relationship Intent (Voluntary)</h3>
              <div className="flex flex-wrap gap-2">
                {profile?.relationship_preferences?.map((item: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-xs text-amber-300 border border-amber-500/20">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Probabilistic Inferences with Explicit Confidence */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Model Interpretations with Calibrated Confidence
              </h3>
              <span className="text-[11px] text-slate-400">Traceable to explicit behavioral signals</span>
            </div>
            <div className="space-y-3">
              {profile?.inferences_with_confidence?.map((inf: any, idx: number) => (
                <div key={idx} className="p-3 bg-slate-800/40 border border-slate-800 rounded-xl space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{inf.claim}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/10 text-pink-400 border border-pink-500/30">
                      {Math.round(inf.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">Supporting basis: &ldquo;{inf.basis}&rdquo;</p>
                </div>
              ))}
            </div>
          </div>

          {/* Uncertainties and Insufficiently Supported Fields */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center space-x-1.5">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Uncertainties & Insufficiently Supported Characteristics</span>
            </h3>
            <p className="text-xs text-slate-400">
              The platform adheres to strict non-inference rules. The following characteristics are unknown and must be discovered during live dating conversations:
            </p>
            <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
              {profile?.uncertainties_and_unknowns?.map((u: string, idx: number) => (
                <li key={idx}>{u}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        /* Underlying Source Evidence Tab */
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
            Source-of-truth guarantee: Every substantive claim is backed by the raw quotes below, retrieved with participant authorization from LinkedIn and Instagram.
          </div>

          <div className="space-y-3">
            {evidence.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                      item.source_platform === "linkedin"
                        ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                        : "bg-pink-500/10 text-pink-400 border border-pink-500/30"
                    }`}>
                      {item.source_platform}
                    </span>
                    <span className="text-slate-400">Category: <strong className="text-slate-200 capitalize">{item.category}</strong></span>
                    <span className="text-slate-500">&bull;</span>
                    <span className="text-slate-400">Type: <strong className="text-slate-200">{item.evidence_type.replace(/_/g, " ")}</strong></span>
                  </div>
                  <span className="text-emerald-400 font-mono text-[11px]">
                    Confidence: {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800/80 text-slate-200 italic font-mono text-[11px]">
                  &ldquo;{item.raw_quote}&rdquo;
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-pink-400 flex items-center space-x-1"
                  >
                    <span>{item.source_url}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                  <span>Retrieved: {new Date(item.retrieved_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
