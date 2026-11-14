"use client";

import React from "react";
import { Sparkles, Bell, ArrowRight, X, Clock, FolderGit2 } from "lucide-react";
import { ProactiveNotificationItem } from "@/lib/api";

interface ProactiveAlertBannerProps {
  notification: ProactiveNotificationItem | null;
  onDismiss: () => void;
  onAction: (text: string) => void;
}

export const ProactiveAlertBanner: React.FC<ProactiveAlertBannerProps> = ({
  notification,
  onDismiss,
  onAction,
}) => {
  if (!notification) return null;

  const isProject = notification.type === "project_followup";

  return (
    <div className="w-full max-w-5xl mx-auto px-4 mt-2 animate-in slide-in-from-top duration-300">
      <div className="glass-panel-glow border-purple-500/40 rounded-xl p-3.5 bg-gradient-to-r from-purple-950/40 via-slate-900/80 to-cyan-950/40 flex flex-wrap items-center justify-between gap-3 shadow-[0_0_20px_rgba(112,0,255,0.25)]">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-purple-500/20 border border-purple-400/50 flex items-center justify-center text-purple-300 flex-shrink-0 animate-pulse">
            {isProject ? <FolderGit2 className="w-3.5 h-3.5" /> : <Bell className="w-3.5 h-3.5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-purple-950 border border-purple-500/40 text-purple-300 font-semibold">
                PROACTIVE INTEL
              </span>
              <span className="text-xs font-mono font-bold text-white">
                {notification.title}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5 font-sans">
              {notification.message}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAction(`Responding to follow-up: I am addressing "${notification.title}" now.`)}
            className="px-3 py-1 rounded-lg bg-purple-600/30 hover:bg-purple-600/50 border border-purple-400 text-purple-200 text-xs font-mono flex items-center gap-1 transition-all"
          >
            <span>Respond</span>
            <ArrowRight className="w-3 h-3" />
          </button>
          <button
            onClick={onDismiss}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            title="Dismiss alert"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
