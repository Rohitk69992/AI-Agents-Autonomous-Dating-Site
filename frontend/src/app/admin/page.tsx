"use client";

import { useEffect, useState } from "react";
import { 
  Settings, Server, ShieldCheck, Activity, RefreshCw, 
  Database, Cpu, DollarSign, CheckCircle2, AlertTriangle, Layers, Lock, Unlock, Key
} from "lucide-react";
import { api, getSessionAdminKey, setSessionAdminKey, clearSessionAdminKey } from "@/lib/api";

export default function AdminOperationsPage() {
  const [config, setConfig] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  // Client-side session admin key (sessionStorage only, never baked into bundle)
  const [adminKeyInput, setAdminKeyInput] = useState("");
  const [isUnlocked, setIsUnlocked] = useState(false);

  useEffect(() => {
    const existing = getSessionAdminKey();
    if (existing) {
      setIsUnlocked(true);
    }

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

  const handleUnlock = (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminKeyInput.trim()) return;
    setSessionAdminKey(adminKeyInput.trim());
    setIsUnlocked(true);
    setAdminKeyInput("");
    setActionStatus("Admin session key stored in active browser session.");
  };

  const handleLock = () => {
    clearSessionAdminKey();
    setIsUnlocked(false);
    setActionStatus("Admin session locked. Session key removed.");
  };

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<((key: string) => Promise<void>) | null>(null);
  const [authModalKey, setAuthModalKey] = useState("");

  const executeWithAuth = (action: (key: string) => Promise<void>) => {
    const key = getSessionAdminKey();
    if (key) {
      action(key);
    } else {
      setPendingAction(() => action);
      setShowAuthModal(true);
    }
  };

  const handleSeedDemo = () => {
    executeWithAuth(async (key: string) => {
      setExecuting(true);
      setActionStatus(null);
      try {
        await api.seedDemo(key);
        setActionStatus("Demonstration dataset seeded and simulated successfully.");
        const [c, m] = await Promise.all([api.getAdminConfig(), api.getMetrics()]);
        setConfig(c);
        setMetrics(m);
      } catch (err: any) {
        setActionStatus(`Error: ${err.message}`);
      } finally {
        setExecuting(false);
      }
    });
  };

  const handleRunFullBenchmark = () => {
    executeWithAuth(async (key: string) => {
      setExecuting(true);
      setActionStatus(null);
      try {
        await api.startRun({
          run_id: "demo-run-25-participants",
          name: "Full 25-Participant Complete Simulation Benchmark",
        }, key);
        setActionStatus("Full 25-Participant batch simulation job enqueued in background worker.");
      } catch (err: any) {
        setActionStatus(`Error: ${err.message}`);
      } finally {
        setExecuting(false);
      }
    });
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
          Inspect backend runtimes, background worker queues, model token consumption, and execute authorized benchmark jobs.
        </p>
      </div>

      {/* Admin Session Security Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 text-xs">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isUnlocked ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
            {isUnlocked ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
          </div>
          <div>
            <span className="font-bold text-white block">
              {isUnlocked ? "Admin Session: Authorized" : "Admin Session: Locked"}
            </span>
            <span className="text-slate-400 text-[11px]">
              {isUnlocked ? "Session key active in client memory (never bundled in code)." : "Provide ADMIN_API_KEY to unlock privileged operations."}
            </span>
          </div>
        </div>

        {isUnlocked ? (
          <button
            onClick={handleLock}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center space-x-1.5"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Lock Session</span>
          </button>
        ) : (
          <form onSubmit={handleUnlock} className="flex items-center space-x-2 w-full sm:w-auto">
            <input
              type="password"
              placeholder="Enter Admin API Key..."
              value={adminKeyInput}
              onChange={(e) => setAdminKeyInput(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500"
            />
            <button
              type="submit"
              className="bg-pink-600 hover:bg-pink-500 text-white font-semibold px-3 py-1.5 rounded-xl text-xs flex items-center space-x-1.5 whitespace-nowrap shadow-md shadow-pink-600/20"
            >
              <Key className="w-3.5 h-3.5" />
              <span>Unlock</span>
            </button>
          </form>
        )}
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
            <strong className="text-sm text-white capitalize">{config?.llm_provider || "Google Gemini"}</strong>
            <p className="text-[11px] text-slate-500">Google Gemini API Multimodal Agent Engine</p>
          </div>

          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">Model Selection</span>
            <strong className="text-sm text-white font-mono">{config?.gemini_model || "gemini-2.5-flash"}</strong>
            <p className="text-[11px] text-slate-500">Structured JSON schema output validation enabled</p>
          </div>

          <div className="space-y-1 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <span className="text-slate-400 font-semibold uppercase text-[10px] block">API Key State</span>
            <strong className="text-sm text-emerald-400">
              {config?.api_key_configured ? "Configured & Secure" : "Offline Mock Harness Active"}
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

      {/* In-App Admin Authorization Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center space-x-3 text-pink-400">
              <div className="w-9 h-9 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Admin Authorization Required</h3>
                <p className="text-[11px] text-slate-400">Privileged action confirmation</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Enter your <code className="bg-slate-800 px-1.5 py-0.5 rounded text-pink-300 font-mono">ADMIN_API_KEY</code> to authorize this operation. The key is stored in your active browser session only.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const trimmed = authModalKey.trim();
                if (!trimmed) return;
                setSessionAdminKey(trimmed);
                setIsUnlocked(true);
                setShowAuthModal(false);
                setAuthModalKey("");
                if (pendingAction) {
                  const actionToRun = pendingAction;
                  setPendingAction(null);
                  actionToRun(trimmed);
                }
              }}
              className="space-y-4"
            >
              <input
                type="password"
                placeholder="Enter ADMIN_API_KEY..."
                value={authModalKey}
                onChange={(e) => setAuthModalKey(e.target.value)}
                autoFocus
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pink-500"
              />
              <div className="flex justify-end space-x-2 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setShowAuthModal(false);
                    setPendingAction(null);
                    setAuthModalKey("");
                    setActionStatus("Action cancelled: Authorization was not provided.");
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!authModalKey.trim()}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-pink-600 hover:bg-pink-500 text-white disabled:opacity-50 transition-colors shadow-md shadow-pink-600/20"
                >
                  Authorize & Proceed
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
