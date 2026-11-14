"use client";

import React from "react";
import { ShieldAlert, Check, X, AlertTriangle, Terminal, Clock } from "lucide-react";
import { PendingActionItem } from "@/lib/api";

interface RiskConfirmationModalProps {
  busy?: boolean;
  pendingAction: PendingActionItem | null;
  onConfirm: () => void;
  onReject: () => void;
}

export const RiskConfirmationModal: React.FC<RiskConfirmationModalProps> = ({
  busy = false,
  pendingAction,
  onConfirm,
  onReject,
}) => {
  if (!pendingAction) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-lg glass-panel-glow border-amber-500/50 rounded-2xl p-5 shadow-[0_0_50px_rgba(245,158,11,0.25)] space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-amber-500/20 pb-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-400 flex items-center justify-center text-amber-300 animate-pulse">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-mono font-bold text-sm text-white tracking-wider">
                SECURITY GUARDRAIL INTERCEPT
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500/40 text-amber-300 font-bold uppercase">
                {pendingAction.risk_level} RISK
              </span>
            </div>
            <p className="text-xs font-mono text-slate-400">
              Real-world side effect intercepted. User authorization required.
            </p>
          </div>
        </div>

        {/* Action Details */}
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Ticket: {pendingAction.ticket_id}</span>
            <span>Target Tool: <strong className="text-cyan-300">{pendingAction.tool_name}</strong></span>
          </div>

          <div className="text-slate-200 text-xs font-sans leading-relaxed pt-1">
            {pendingAction.rationale}
          </div>

          {/* Parameter Details */}
          {pendingAction.params && (
            <div className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 whitespace-pre-wrap max-h-32 overflow-y-auto">
              {JSON.stringify(pendingAction.params, null, 2)}
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onReject}
            disabled={busy}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white text-xs font-mono flex items-center gap-1.5 transition-all"
          >
            <X className="w-3.5 h-3.5" />
            <span>Abort Action</span>
          </button>

          <button
            onClick={onConfirm}
            disabled={busy}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs font-mono flex items-center gap-1.5 shadow-[0_0_15px_rgba(245,158,11,0.5)] transition-all"
          >
            <Check className="w-3.5 h-3.5" />
            <span>{busy ? "Processing…" : "Authorize Execution"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
