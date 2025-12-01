"use client";

import { useState } from "react";
import { api, ScanResponse } from "@/lib/api";
import { ShieldAlert, RefreshCw, ShoppingCart, Truck, Activity, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

export default function Dashboard() {
  // --- STATE MANAGEMENT ---
  const [region, setRegion] = useState("Taiwan");
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  
  // Interactive Procurement State
  const [procurementLog, setProcurementLog] = useState<string[]>([]);
  const [pendingApproval, setPendingApproval] = useState(false);

  // --- HANDLER: RUN RISK ANALYSIS ---
  const handleScan = async () => {
    setLoading(true);
    setScanResult(null);
    setProcurementLog([]); // Clear previous logs
    try {
      const data = await api.scanRegion(region);
      setScanResult(data);
    } catch (err) {
      alert("Failed to connect to Sentinell Backend. Please check your .env.local file.");
    } finally {
      setLoading(false);
    }
  };

  // --- HANDLER: START PROCUREMENT ---
  const startPurchase = async () => {
    setLoading(true);
    setProcurementLog(["Initiating purchase request..."]);
    setPendingApproval(false);
    
    try {
      // Step A: Agent thinks and checks price
      const res = await api.purchaseParts("Logic-Core-CPU", 50);
      setProcurementLog(prev => [...prev, `Agent: ${res.summary}`]);
      
      // Step B: Check if Agent paused for approval or asked a question
      if (res.status === "PAUSED_FOR_APPROVAL" || res.summary.includes("?")) {
        setPendingApproval(true);
      }
    } catch (err) {
      setProcurementLog(prev => [...prev, "❌ Connection Error: Backend unreachable."]);
    } finally {
      setLoading(false);
    }
  };

  // --- HANDLER: USER SAYS 'YES' ---
  const confirmPurchase = async () => {
    setLoading(true);
    setPendingApproval(false); // Hide buttons
    setProcurementLog(prev => [...prev, "User: YES, Proceed."]);
    
    try {
      // We call the API again. In a real system, we'd use session IDs.
      // Here, re-issuing the command forces the agent to proceed since the prompt context resets/updates.
      const res = await api.purchaseParts("Logic-Core-CPU", 50);
      setProcurementLog(prev => [...prev, `Agent: ${res.summary}`]);
    } catch (err) {
      setProcurementLog(prev => [...prev, "❌ System Error during execution."]);
    } finally {
      setLoading(false);
    }
  };

  // --- HANDLER: USER SAYS 'NO' ---
  const cancelPurchase = () => {
    setPendingApproval(false);
    setProcurementLog(prev => [...prev, "User: Cancelled operation."]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-4 md:p-8 font-sans">
      {/* --- HEADER --- */}
      <header className="mb-8 flex flex-col md:flex-row items-start md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="text-blue-500" /> Sentinell.ai
          </h1>
          <p className="text-slate-400 text-sm">Autonomous Supply Chain Resilience System</p>
        </div>
        <div className="bg-slate-900 px-4 py-2 rounded-lg border border-slate-800 flex items-center gap-2">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm font-medium">System Online</span>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* --- LEFT COLUMN: CONTROLS --- */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* 1. Risk Monitor Card (Selector + Scan Button) */}
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
              <Activity size={20} className="text-blue-400"/> Risk Monitor
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-slate-500 mb-1">Target Region</label>
                <select 
                  value={region} 
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                >
                  <option value="Taiwan">Taiwan (High Risk Sim)</option>
                  <option value="USA">USA (Medium Risk Sim)</option>
                  <option value="Vietnam">Vietnam (Low Risk Sim)</option>
                </select>
              </div>
              
              <button
                onClick={handleScan}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md active:scale-95"
              >
                {loading ? <RefreshCw className="animate-spin" /> : <ShieldAlert size={20} />}
                {loading ? "Analyzing..." : "Run Risk Analysis"}
              </button>
            </div>
          </div>

          {/* 2. Response Actions Card (Purchase Button) */}
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg opacity-90">
            <h2 className="text-lg font-semibold mb-2 text-white flex items-center gap-2">
              <ShoppingCart size={20} className="text-green-400"/> Response Actions
            </h2>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Detected a critical shortage? Authorize the Procurement Agent to negotiate with backup suppliers immediately.
            </p>
            <button 
              onClick={startPurchase}
              disabled={loading || !scanResult} // Only enable if we have scanned first
              className={`w-full border-2 font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all ${
                !scanResult 
                  ? "border-slate-700 text-slate-600 cursor-not-allowed"
                  : "border-green-600 text-green-500 hover:bg-green-900/20 active:scale-95"
              }`}
            >
              <Truck size={20} />
              {loading ? "Agent Working..." : "Replenish Inventory"}
            </button>
          </div>
        </div>

        {/* --- RIGHT COLUMN: LIVE FEED --- */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-slate-900 min-h-[600px] p-6 rounded-xl border border-slate-800 relative shadow-xl flex flex-col">
            
            {/* Feed Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <h2 className="text-xl font-semibold text-white">Agent Intelligence Feed</h2>
              <span className="text-xs text-slate-500 font-mono">LIVE CONNECTED</span>
            </div>

            {/* Empty State */}
            {!scanResult && procurementLog.length === 0 && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-600 space-y-4">
                <div className="p-4 bg-slate-800/50 rounded-full">
                  <ShieldAlert size={48} />
                </div>
                <p>Ready to analyze. Select a region to begin.</p>
              </div>
            )}

            <div className="space-y-6">
              {/* 3. Scan Result Display */}
              {scanResult && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-2 ${
                      scanResult.risk_level === 'CRITICAL' ? 'bg-red-950/50 border-red-500 text-red-400' :
                      scanResult.risk_level === 'MEDIUM' ? 'bg-yellow-950/50 border-yellow-500 text-yellow-400' :
                      'bg-green-950/50 border-green-500 text-green-400'
                    }`}>
                      {scanResult.risk_level === 'CRITICAL' && <AlertTriangle size={12} />}
                      {scanResult.risk_level} RISK DETECTED
                    </span>
                    <span className="text-xs text-slate-500">{new Date(scanResult.timestamp).toLocaleTimeString()}</span>
                  </div>
                  
                  <div className="bg-slate-950 p-6 rounded-lg border border-slate-700/50 shadow-inner">
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-slate-300">
                      {scanResult.summary}
                    </pre>
                  </div>
                </div>
              )}

              {/* 4. Interactive Transaction Log */}
              {procurementLog.length > 0 && (
                <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider border-t border-slate-800 pt-4">Transaction Log</h3>
                  
                  {procurementLog.map((msg, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border flex gap-3 items-start ${
                      msg.startsWith("User") ? "bg-slate-800 border-slate-700 ml-12" : 
                      msg.startsWith("❌") ? "bg-red-900/20 border-red-800" :
                      "bg-green-900/10 border-green-900 mr-12"
                    }`}>
                      {/* Icon Logic */}
                      <div className="mt-1">
                        {msg.startsWith("User") ? <CheckCircle size={16} className="text-blue-400"/> : 
                         msg.startsWith("❌") ? <XCircle size={16} className="text-red-400"/> :
                         <Truck size={16} className="text-green-400"/>}
                      </div>
                      <p className="text-sm text-slate-300 leading-relaxed">{msg}</p>
                    </div>
                  ))}

                  {/* 5. APPROVAL BUTTONS (Only show when agent pauses) */}
                  {pendingApproval && (
                    <div className="flex gap-4 mt-4 justify-end animate-pulse">
                      <button 
                        onClick={cancelPurchase}
                        className="px-4 py-2 rounded-lg border border-red-500 text-red-400 hover:bg-red-900/20 flex items-center gap-2 transition-all"
                      >
                        <XCircle size={16} /> Cancel
                      </button>
                      <button 
                        onClick={confirmPurchase}
                        className="px-6 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 flex items-center gap-2 shadow-lg transition-all"
                      >
                        <CheckCircle size={16} /> Approve Payment
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}