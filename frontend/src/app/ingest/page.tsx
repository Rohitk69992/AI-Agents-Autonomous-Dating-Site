"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  UserPlus, CheckCircle2, AlertCircle, ShieldCheck, ArrowRight, 
  ExternalLink, FileSpreadsheet, Sparkles, RefreshCw
} from "lucide-react";
import { api } from "@/lib/api";

export default function IngestPage() {
  const router = useRouter();
  const [tab, setTab] = useState<"single" | "batch">("single");

  // Single Form State
  const [name, setName] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  const [age, setAge] = useState<number | "">(28);
  const [gender, setGender] = useState("Female");
  const [targetGender, setTargetGender] = useState("Male");
  const [location, setLocation] = useState("San Francisco, CA");
  const [consentConfirmed, setConsentConfirmed] = useState(false);

  // Status & Feedback
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  // Batch Form State
  const [batchJson, setBatchJson] = useState("");
  const [batchResults, setBatchResults] = useState<any[] | null>(null);

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!consentConfirmed) {
      setErrorMsg("Participant consent is non-negotiable. You must check the consent confirmation box.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.createParticipant({
        name,
        linkedin_url: linkedinUrl,
        instagram_url: instagramUrl,
        consent_confirmed: consentConfirmed,
        age: age ? Number(age) : undefined,
        gender,
        target_gender: targetGender,
        location,
      });

      setSuccessMsg(`Participant ${res.name} successfully registered, analyzed, and added to the matchmaking registry.`);
      setCreatedId(res.id);
      // Reset form
      setName("");
      setLinkedinUrl("");
      setInstagramUrl("");
      setConsentConfirmed(false);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register participant.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleBatchSubmit = async () => {
    setErrorMsg(null);
    setBatchResults(null);
    setSubmitting(true);

    try {
      const parsed = JSON.parse(batchJson);
      const items = Array.isArray(parsed) ? parsed : parsed.participants || [];
      if (items.length === 0) throw new Error("No participant entries found in JSON array.");

      const results = [];
      for (const item of items) {
        try {
          const res = await api.createParticipant({
            name: item.name,
            linkedin_url: item.linkedin_url,
            instagram_url: item.instagram_url,
            consent_confirmed: Boolean(item.consent_confirmed),
            age: item.age,
            gender: item.gender,
            target_gender: item.target_gender,
            location: item.location,
          });
          results.push({ name: item.name, status: "success", id: res.id });
        } catch (err: any) {
          results.push({ name: item.name, status: "error", error: err.message });
        }
      }
      setBatchResults(results);
    } catch (err: any) {
      setErrorMsg(`JSON Parse Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold mb-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Strict Provenance & Consent Ingestion</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">Ingest Consenting Participant</h1>
        <p className="text-slate-400 text-sm mt-1">
          Each participant’s substantive evidence originates exclusively from verified public LinkedIn and Instagram profiles. No scraped credentials or unauthorized profiles.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setTab("single")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-all ${
            tab === "single"
              ? "border-pink-500 text-pink-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <UserPlus className="w-4 h-4" />
          <span>Single Participant</span>
        </button>
        <button
          onClick={() => setTab("batch")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-all ${
            tab === "batch"
              ? "border-pink-500 text-pink-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Authorized Batch Import</span>
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div>
            <span className="font-semibold block">Ingestion Blocked</span>
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-start justify-between space-x-3">
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400 mt-0.5" />
            <div>
              <span className="font-semibold block">Participant Ingested</span>
              <span>{successMsg}</span>
            </div>
          </div>
          {createdId && (
            <button
              onClick={() => router.push(`/participants/${createdId}`)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded-lg flex items-center space-x-1 whitespace-nowrap"
            >
              <span>View Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {tab === "single" ? (
        <form onSubmit={handleSingleSubmit} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Full Name <span className="text-pink-400">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Maya Lindqvist"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                LinkedIn Profile URL <span className="text-pink-400">*</span>
              </label>
              <input
                type="url"
                required
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://www.linkedin.com/in/handle"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500 font-mono text-xs"
              />
              <span className="text-[11px] text-slate-500">Format: https://www.linkedin.com/in/{`{handle}`}</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Instagram Profile URL <span className="text-pink-400">*</span>
              </label>
              <input
                type="url"
                required
                value={instagramUrl}
                onChange={(e) => setInstagramUrl(e.target.value)}
                placeholder="https://www.instagram.com/handle"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500 font-mono text-xs"
              />
              <span className="text-[11px] text-slate-500">Format: https://www.instagram.com/{`{handle}`}</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">Age</label>
              <input
                type="number"
                min="18"
                max="100"
                value={age}
                onChange={(e) => setAge(e.target.value === "" ? "" : Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. San Francisco, CA"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">Gender Identity</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-pink-500"
              >
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Non-Binary">Non-Binary</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">Dating Target Preference</label>
              <select
                value={targetGender}
                onChange={(e) => setTargetGender(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-pink-500"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Any">Any / Open</option>
              </select>
            </div>
          </div>

          {/* Consent Checkbox */}
          <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700 space-y-3">
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="consentCheck"
                checked={consentConfirmed}
                onChange={(e) => setConsentConfirmed(e.target.checked)}
                className="mt-1 w-4 h-4 rounded text-pink-600 focus:ring-pink-500 border-slate-600 bg-slate-700 cursor-pointer"
              />
              <label htmlFor="consentCheck" className="text-xs text-slate-300 leading-relaxed cursor-pointer">
                <strong className="text-white">Mutual Participation & Agent Representation Consent:</strong> I confirm that this participant has explicitly consented to being represented by an autonomous AI agent in simulated dating conversations, and that the specified LinkedIn and Instagram URLs are public profiles authorized for compatibility evidence extraction.
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-semibold py-3 rounded-xl shadow-lg shadow-pink-600/20 text-sm flex items-center justify-center space-x-2 disabled:opacity-50 transition-all"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Validating & Analyzing Profile...</span>
              </>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Submit & Ingest Participant</span>
              </>
            )}
          </button>
        </form>
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Batch JSON Manifest
            </label>
            <p className="text-xs text-slate-400">
              Paste an array of authorized participant records. Each row is validated independently.
            </p>
            <textarea
              rows={8}
              value={batchJson}
              onChange={(e) => setBatchJson(e.target.value)}
              placeholder={`[
  {
    "name": "Alex Rivera",
    "linkedin_url": "https://www.linkedin.com/in/alex-rivera-tech",
    "instagram_url": "https://www.instagram.com/alex_takes_photos",
    "consent_confirmed": true,
    "age": 29,
    "gender": "Non-Binary",
    "target_gender": "Any",
    "location": "San Francisco, CA"
  }
]`}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl p-4 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-pink-500"
            />
          </div>

          <button
            onClick={handleBatchSubmit}
            disabled={submitting || !batchJson.trim()}
            className="w-full bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-semibold py-3 rounded-xl shadow-lg shadow-pink-600/20 text-sm flex items-center justify-center space-x-2 disabled:opacity-50 transition-all"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Processing Manifest Records...</span>
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4" />
                <span>Run Batch Ingestion</span>
              </>
            )}
          </button>

          {batchResults && (
            <div className="space-y-3 pt-4 border-t border-slate-800">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">Batch Results</h3>
              <div className="space-y-2">
                {batchResults.map((r, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg text-xs flex items-center justify-between ${
                      r.status === "success"
                        ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/10 border border-rose-500/20 text-rose-300"
                    }`}
                  >
                    <span className="font-semibold">{r.name}</span>
                    <span>{r.status === "success" ? `Ingested (ID: ${r.id.substring(0, 8)}...)` : r.error}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
