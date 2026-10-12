"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Users, Search, ExternalLink, ShieldCheck, HeartHandshake, 
  Sparkles, Filter, ChevronRight, UserPlus
} from "lucide-react";
import { api } from "@/lib/api";

export default function ParticipantsDirectoryPage() {
  const [participants, setParticipants] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchParticipants = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getParticipants({ search, status_filter: statusFilter });
      setParticipants(data || []);
    } catch (err: any) {
      console.error("Failed to load participants:", err);
      setError(err?.message || "Failed to connect to the AuraMatch backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchParticipants, 300);
    return () => clearTimeout(timer);
  }, [search, statusFilter]);

  const hasSynthetic = participants.some((p) => p.is_synthetic);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold mb-2">
            <Users className="w-3.5 h-3.5" />
            <span>Participant Directory</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Participant Profiles</h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse synthetic demo fixtures and registered participants represented by autonomous dating agents.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/demo"
            className="inline-flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium px-3.5 py-2 rounded-xl text-xs transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-pink-400" />
            <span>Demo Workflow</span>
          </Link>
          <Link
            href="/ingest"
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-medium px-4 py-2.5 rounded-xl shadow-lg shadow-pink-600/20 text-xs transition-all"
          >
            <UserPlus className="w-4 h-4" />
            <span>Ingest Profile</span>
          </Link>
        </div>
      </div>

      {/* Synthetic Demo Data Notice */}
      {hasSynthetic && (
        <div className="flex items-center justify-between text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 px-4 py-2.5 rounded-xl">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Synthetic Demo Dataset Active:</strong> Directory displays 25 realistic synthetic development fixtures for autonomous simulation testing.
            </span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-200 uppercase tracking-wider hidden sm:inline-block">
            DEMO MODE
          </span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 bg-slate-900/80 border border-slate-800 p-3 rounded-xl">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, location (e.g. Bengaluru, Mumbai), or handle..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500 hidden sm:block" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-pink-500"
          >
            <option value="">All Statuses</option>
            <option value="analyzed">Analyzed Only</option>
            <option value="pending">Pending Analysis</option>
          </select>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-2 text-xs text-rose-300">
          <div className="font-semibold text-rose-200">Unable to load participants:</div>
          <div className="text-rose-400 font-mono text-[11px]">{error}</div>
          <div className="pt-2 flex items-center space-x-3">
            <button
              onClick={() => fetchParticipants()}
              className="px-3 py-1.5 bg-rose-600/30 hover:bg-rose-600/50 text-white rounded-lg font-medium transition-colors"
            >
              Retry Connection
            </button>
            <span className="text-[11px] text-slate-400">
              Ensure the backend is online and configured in <code>NEXT_PUBLIC_API_URL</code>.
            </span>
          </div>
        </div>
      )}

      {/* Grid of Participant Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-full bg-slate-800" />
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-slate-800 rounded w-1/2" />
                  <div className="h-3 bg-slate-800 rounded w-1/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : participants.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-2xl space-y-4">
          <Users className="w-12 h-12 text-slate-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-300">No participants found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No matching records in the database. Run the synthetic seeder script or ingest a new participant.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/admin"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              Admin Seeder Panel
            </Link>
            <Link
              href="/ingest"
              className="px-4 py-2 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 text-white text-xs font-semibold rounded-xl shadow transition-colors"
            >
              Ingest Participant
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {participants.map((p) => {
            const initials = p.name.split(" ").map((n: string) => n[0]).join("");
            const profile = p.analyzed_profile;
            return (
              <div
                key={p.id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 space-y-4 transition-all flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-pink-600/30 to-purple-600/30 border border-pink-500/30 flex items-center justify-center font-bold text-pink-400 text-sm shadow">
                        {initials}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white group-hover:text-pink-300 transition-colors">
                          {p.name}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {p.location || "India"} &bull; {p.age || 28} yo &bull; {p.gender || "Not specified"}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {p.status === "withdrawn" || p.consent_status === "withdrawn" ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          Withdrawn
                        </span>
                      ) : p.is_synthetic ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          Synthetic Demo Data
                        </span>
                      ) : p.consent_verified ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Verified Consent
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                          Consent Declared
                        </span>
                      )}
                      {p.is_synthetic ? (
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                          DEMO FIXTURE
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                          PARTICIPANT
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Summary Snippet */}
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {profile?.summary || "Profile evidence gathered. Pending automated semantic analysis."}
                  </p>

                  {/* Badges for Hobbies & Interests */}
                  {profile && profile.demonstrated_hobbies?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {profile.demonstrated_hobbies.slice(0, 3).map((h: string, idx: number) => (
                        <span key={idx} className="px-2 py-0.5 rounded-md bg-slate-800 text-[10px] font-medium text-slate-300 border border-slate-700">
                          {h}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Source URLs with Provenance */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center space-x-3 text-[11px] text-slate-400">
                    <a
                      href={p.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-pink-400 flex items-center space-x-1"
                    >
                      <span>LinkedIn</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                    <span>&bull;</span>
                    <a
                      href={p.instagram_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-pink-400 flex items-center space-x-1"
                    >
                      <span>Instagram</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                    <span>&bull;</span>
                    <span>{p.evidence_count} evidence items</span>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="pt-3 border-t border-slate-800 flex items-center space-x-2">
                  <Link
                    href={`/participants/${p.id}`}
                    className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 rounded-xl text-center transition-colors"
                  >
                    View Analysis & Evidence
                  </Link>
                  <Link
                    href={`/rankings?participant_id=${p.id}`}
                    title="View candidate rankings for this participant"
                    className="p-2 bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 border border-pink-500/20 rounded-xl transition-colors"
                  >
                    <HeartHandshake className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
