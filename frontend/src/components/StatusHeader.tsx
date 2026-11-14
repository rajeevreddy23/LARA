"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Cpu,
  ShieldCheck,
  Terminal,
  Radio,
  Mic,
  MicOff,
  Volume2,
  Brain,
  FileText,
  Moon,
  Sparkles,
  Clock,
  User,
  Smartphone,
  FolderOpen,
  Mail,
  Grid,
} from "lucide-react";
import { HealthResponse } from "@/lib/api";
import { VoiceState } from "@/hooks/useVoiceAssistant";

interface StatusHeaderProps {
  health: HealthResponse | null;
  isConnected: boolean;
  briefingMode: boolean;
  onToggleBriefing: () => void;
  latency: number | null;
  isWakeWordActive: boolean;
  voiceState: VoiceState;
  onToggleWakeWord: () => void;
  onOpenMemory: () => void;
  onTriggerBriefing: () => void;
  memoryItemCount?: number;
  onOpenDeviceBridge?: () => void;
  onOpenFiles?: () => void;
  onOpenMail?: () => void;
  mailUnreadCount?: number;
  onOpenApps?: () => void;
  appsCount?: number;
}

export const StatusHeader: React.FC<StatusHeaderProps> = ({
  health,
  isConnected,
  briefingMode,
  onToggleBriefing,
  latency,
  isWakeWordActive,
  voiceState,
  onToggleWakeWord,
  onOpenMemory,
  onTriggerBriefing,
  memoryItemCount = 0,
  onOpenDeviceBridge,
  onOpenFiles,
  onOpenMail,
  mailUnreadCount = 0,
  onOpenApps,
  appsCount = 0,
}) => {
  const [liveTime, setLiveTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLiveTime(
        now.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        }) + " • " +
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="w-full glass-panel-glow border-b border-cyan-500/30 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 sticky top-0 z-50 bg-slate-950/90 backdrop-blur-xl">
      {/* Brand Identity */}
      <div className="flex items-center space-x-3">
        <div className="relative flex items-center justify-center group">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-400/60 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.4)] group-hover:scale-105 transition-transform">
            <Terminal className="w-5 h-5" />
          </div>
          {isConnected && (
            <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500 shadow-[0_0_8px_#00f0ff]"></span>
            </span>
          )}
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-mono font-black tracking-widest text-xl text-white text-glow-cyan">
              LARA
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-cyan-950/90 border border-cyan-400/50 text-cyan-300 font-bold shadow-[0_0_12px_rgba(0,240,255,0.25)]">
              AI OS • 2026 REALTIME
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1 text-cyan-300">
              <User className="w-3 h-3 text-cyan-400" />
              <span>Bunty</span>
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 text-slate-300">
              <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
              <span>JARVIS OS Core</span>
            </span>
          </div>
        </div>
      </div>

      {/* Real-Time Telemetry Badges */}
      <div className="hidden lg:flex items-center gap-2.5 text-xs font-mono text-slate-300">
        {/* Live 2026 Clock */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/80 border border-cyan-500/30 text-cyan-300 shadow-sm">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span suppressHydrationWarning className="text-[11px] font-semibold">{liveTime || "2026 Live Telemetry"}</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700/60">
          <Activity className={`w-3.5 h-3.5 ${isConnected ? "text-emerald-400 animate-pulse" : "text-rose-400"}`} />
          <span className="text-[11px]">{isConnected ? "ONLINE" : "OFFLINE"}</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700/60">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[11px]">{health?.active_model || "gemini-2.5-flash"}</span>
        </div>

        {latency !== null && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700/60 text-cyan-300">
            <span className="text-[11px]">{latency}ms</span>
          </div>
        )}
      </div>

      {/* Action Controls & Voice Toggle */}
      <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
        {/* Mobile Phone Link & QR Pairing */}
        {onOpenDeviceBridge && (
          <button
            onClick={onOpenDeviceBridge}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-cyan-950/50 border-cyan-400/50 hover:bg-cyan-900/60 text-cyan-200 hover:text-cyan-100 flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,240,255,0.25)] font-bold"
            title="Scan QR Code to access LARA on Mobile Phone"
          >
            <Smartphone className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="hidden sm:inline">PHONE LINK</span>
          </button>
        )}

        {/* System File & Folder Hub */}
        {onOpenFiles && (
          <button
            onClick={onOpenFiles}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-slate-900/80 border-slate-700 hover:border-cyan-400/60 text-slate-200 hover:text-cyan-300 flex items-center gap-1.5 shadow-sm"
            title="Open System File & Folder Hub"
          >
            <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">FILES</span>
          </button>
        )}

        {/* System Apps Hub */}
        {onOpenApps && (
          <button
            onClick={onOpenApps}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-blue-950/40 border-blue-500/40 hover:bg-blue-900/50 text-blue-200 hover:text-blue-100 flex items-center gap-1.5 shadow-sm"
            title="Open System Applications Hub"
          >
            <Grid className="w-3.5 h-3.5 text-blue-400" />
            <span className="hidden sm:inline">APPS</span>
            {appsCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-blue-950 border border-blue-400/50 text-[10px] text-blue-300 font-bold">
                {appsCount}
              </span>
            )}
          </button>
        )}

        {/* Mail & Email Hub */}
        {onOpenMail && (
          <button
            onClick={onOpenMail}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-purple-950/40 border-purple-500/40 hover:bg-purple-900/50 text-purple-200 hover:text-purple-100 flex items-center gap-1.5 shadow-sm"
            title="Open Mail & Email Hub"
          >
            <Mail className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden sm:inline">MAIL</span>
            {mailUnreadCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-purple-600 text-[10px] text-white font-bold animate-pulse">
                {mailUnreadCount}
              </span>
            )}
          </button>
        )}

        {/* Executive Daily Briefing Trigger */}
        <button
          onClick={onTriggerBriefing}
          className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-slate-900/80 border-slate-700 hover:border-purple-400/60 text-slate-300 hover:text-purple-200 flex items-center gap-1.5 shadow-sm"
          title="Generate real-time executive daily briefing"
        >
          <FileText className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden sm:inline">BRIEFING</span>
        </button>

        {/* Memory Intel Button */}
        <button
          onClick={onOpenMemory}
          className="px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border bg-slate-900/80 border-slate-700 hover:border-cyan-400/60 text-slate-200 hover:text-cyan-300 flex items-center gap-1.5 shadow-sm"
          title="Open Memory Intel and Knowledge Graph"
        >
          <Brain className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">INTEL</span>
          {memoryItemCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-cyan-950 border border-cyan-500/50 text-[10px] text-cyan-300 font-bold">
              {memoryItemCount}
            </span>
          )}
        </button>

        {/* Hey LARA / Bye LARA Wake Word Status Toggle */}
        <button
          onClick={onToggleWakeWord}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-300 border flex items-center gap-1.5 font-bold ${
            isWakeWordActive
              ? voiceState === "listening"
                ? "bg-emerald-500/30 border-emerald-400 text-emerald-200 shadow-[0_0_25px_rgba(16,185,129,0.6)] animate-pulse"
                : voiceState === "speaking"
                ? "bg-purple-600/30 border-purple-400 text-purple-200 shadow-[0_0_25px_rgba(168,85,247,0.6)]"
                : voiceState === "sleep"
                ? "bg-slate-900/90 border-slate-700 text-slate-400"
                : "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_20px_rgba(0,240,255,0.4)]"
              : "bg-slate-900/80 border-slate-700 hover:border-cyan-500/50 text-slate-400 hover:text-slate-200"
          }`}
          title="Toggle hands-free 'Hey LARA' continuous listening & 'Bye LARA' sleep"
        >
          {isWakeWordActive ? (
            voiceState === "speaking" ? (
              <Volume2 className="w-3.5 h-3.5 animate-bounce text-purple-300" />
            ) : voiceState === "sleep" ? (
              <Moon className="w-3.5 h-3.5 text-slate-400" />
            ) : (
              <Mic className="w-3.5 h-3.5 text-cyan-300 animate-pulse" />
            )
          ) : (
            <MicOff className="w-3.5 h-3.5" />
          )}
          <span>
            {isWakeWordActive
              ? voiceState === "listening"
                ? "LISTENING..."
                : voiceState === "speaking"
                ? "LARA SPEAKING"
                : voiceState === "sleep"
                ? "SLEEP • SAY 'HEY LARA'"
                : "HEY LARA: ACTIVE"
              : "WAKE WORD OFF"}
          </span>
        </button>

        {/* Briefing Mode Toggle */}
        <button
          onClick={onToggleBriefing}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border flex items-center gap-1.5 ${
            briefingMode
              ? "bg-purple-600/30 border-purple-400 text-purple-200 shadow-[0_0_15px_rgba(168,85,247,0.4)]"
              : "bg-slate-900/80 border-slate-700 hover:border-cyan-500/50 text-slate-300 hover:text-white"
          }`}
          title="Toggle between concise casual and thorough briefing mode"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{briefingMode ? "BRIEFING" : "CASUAL"}</span>
        </button>
      </div>
    </header>
  );
};
