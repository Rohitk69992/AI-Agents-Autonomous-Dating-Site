"use client";

import { useEffect, useState } from "react";
import { 
  Settings, Server, ShieldCheck, Activity, RefreshCw, 
  Database, Cpu, DollarSign, CheckCircle2, AlertTriangle, Layers
} from "lucide-react";
import { api } from "@/lib/api";

export default function AdminOperationsPage() {
  const [config, setConfig] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    async function loadOpsData() {
      try {
        const [c, m, h] = await Promise.all([
          api.getAdminConfig().catch(() => null),
          api.getMetrics().catch(() => null),
          api.getHealth().catch(() => null),
        ]);
        setConfig(c);
        setMetrics(m);
        setHealth(h);
      } catch (err) {
        console.error("Ops data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadOpsData();
  }, []);

  const handleSeedDemo = async () => {
    setExecuting(true);
    setActionStatus(null);
    try {
      await api.seedDemo();
      setActionStatus("Demonstration dataset seeded and simulated successfully.");
      const [c, m] = await Promise.all([api.getAdminConfig(), api.getMetrics()]);
      setConfig(c);
      setMetrics(m);
    } catch (err: any) {
      setActionStatus(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleRunFullBenchmark = async () => {
    setExecuting(true);
    setActionStatus(null);
    try {
      await api.startRun({
        run_id: "demo-run-25-participants",
        name: "Full 25-Participant Complete Simulation Benchmark",
      });
      setActionStatus("Full 25-Participant batch simulation job enqueued in background worker.");
    } catch (err: any) {
      setActionStatus(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold mb-2">
          <Settings className="w-3.5 h-3.5 text-pink-400" />
          <span>Operations & Observability</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">System Configuration & Health</h1>
        <p className="text-slate-400 text-sm mt-1">
          Inspect backend runtimes, background worker queues, model token consumption, and execute benchmark jobs.
        </p>
      </div>

      {actionStatus && (
        <div className="p-4 rounded-xl bg-pink-500/10 border border-pink-500/30 text-pink-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{actionStatus}</span>
        </div>
      )}

      {/* Observability Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">API Health</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white capitalize">{health?.status || "Online"}</div>
          <p className="text-[11px] text-slate-400">Active background jobs: {health?.active_background_jobs || 0}</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Tokens Consumed</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-white">{metrics?.total_tokens_consumed?.toLocaleString() || 0}</div>
          <p className="text-[11px] text-slate-400">Est. cost: ${metrics?.estimated_total_cost_usd?.toFixed(4) || "0.0000"}</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Sessions Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">{metrics?.completed_sessions || 0}</div>
          <p className="text-[11px] text-slate-400">{metrics?.failed_sessions || 0} failed / passed</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Average Latency</span>
            <Activity className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-xl font-bold text-white">{metrics?.average_session_latency_ms || 0} ms</div>
          <p className="text-[11px] text-slate-400">Multi-turn conversation</p>
        </div>
      </div>

      {/* Configuration Detail Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Server className="w-4 h-4 text-pink-400" />
            <span>LLM Provider & Runtime Security</span>
          </h2>
          <p className="text-xs text-slate-400">
            Zero credentials are exposed to frontend clients. Provider routing is enforced server-side.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">Active LLM Provider</span>
            <strong className="text-sm text-white capitalize">{config?.llm_provider || "deterministic"}</strong>
            <p className="text-[11px] text-slate-500">Google Gemini API / Deterministic Test Engine</p>
          </div>

          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">Model Selection</span>
            <strong className="text-sm text-white font-mono">{config?.gemini_model || "gemini-2.5-flash"}</strong>
            <p className="text-[11px] text-slate-500">Structured JSON schema output validation enabled</p>
          </div>

          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">API Key State</span>
            <strong className={`text-sm ${config?.api_key_configured ? "text-emerald-400" : "text-amber-400"}`}>
              {config?.api_key_configured ? "Configured & Secure" : "Not Set (Using Deterministic Engine)"}
            </strong>
            <p className="text-[11px] text-slate-500">Credentials kept strictly outside public Git / bundle</p>
          </div>

          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">Database Connection</span>
            <strong className="text-sm text-white font-mono">{config?.database_url_masked || "sqlite:///./dating.db"}</strong>
            <p className="text-[11px] text-slate-500">Relational persistence with transaction boundaries</p>
          </div>
        </div>

        {/* Operational Actions */}
        <div className="pt-4 border-t border-slate-800 flex flex-wrap gap-4">
          <button
            onClick={handleSeedDemo}
            disabled={executing}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${executing ? "animate-spin" : ""}`} />
            <span>Re-Seed 25-Participant Dataset</span>
          </button>

          <button
            onClick={handleRunFullBenchmark}
            disabled={executing}
            className="bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-pink-600/20 text-xs flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Run Complete Simulation Run in Background</span>
          </button>
        </div>
      </div>
    </div>
  );
}
