"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Zap,
  Terminal,
  Cpu,
  HardDrive,
  Wifi,
  Sparkles,
  Send,
  MessageSquare,
  Globe,
  Code,
  FileSpreadsheet,
  Folder,
  Mail,
  Layers,
  Lock,
  Unlock,
  Radio,
  Clock,
} from "lucide-react";
import { VoiceState } from "@/hooks/useVoiceAssistant";

interface JarvisVisionHudProps {
  voiceState: VoiceState;
  interimTranscript: string;
  isWakeWordActive: boolean;
  onExecuteCommand: (cmd: string) => void;
  onStartManualListening: () => void;
  onStopManualListening: () => void;
}

export const JarvisVisionHud: React.FC<JarvisVisionHudProps> = ({
  voiceState,
  interimTranscript,
  isWakeWordActive,
  onExecuteCommand,
  onStartManualListening,
  onStopManualListening,
}) => {
  const [cmdInput, setCmdInput] = useState<string>("");
  const [currentTime, setCurrentTime] = useState<string>("00:00:00");
  const [currentDate, setCurrentDate] = useState<string>("SUNDAY // AUG 30, 2026");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString("en-US", { hour12: false }));
      setCurrentDate(
        now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "2-digit",
          year: "numeric",
        }).toUpperCase().replace(",", " //")
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isListening = voiceState === "listening";
  const isSpeaking = voiceState === "speaking";
  const isThinking = voiceState === "thinking";

  const handleQuickLaunch = (command: string) => {
    onExecuteCommand(command);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cmdInput.trim()) return;
    onExecuteCommand(cmdInput.trim());
    setCmdInput("");
  };

  const appLockerCards = [
    {
      label: "WhatsApp",
      desc: "Desktop & Web",
      cmd: "Open WhatsApp",
      icon: <MessageSquare className="w-5 h-5 text-emerald-400" />,
      tag: "COMM",
      glow: "hover:border-emerald-400/80 hover:shadow-[0_0_20px_rgba(16,185,129,0.35)]",
      badgeColor: "bg-emerald-950/80 text-emerald-300 border-emerald-500/40",
    },
    {
      label: "Google Chrome",
      desc: "Web Navigator",
      cmd: "Open Chrome",
      icon: <Globe className="w-5 h-5 text-cyan-400" />,
      tag: "WEB",
      glow: "hover:border-cyan-400/80 hover:shadow-[0_0_20px_rgba(0,240,255,0.35)]",
      badgeColor: "bg-cyan-950/80 text-cyan-300 border-cyan-500/40",
    },
    {
      label: "VS Code",
      desc: "Dev IDE",
      cmd: "Open VS Code",
      icon: <Code className="w-5 h-5 text-blue-400" />,
      tag: "DEV",
      glow: "hover:border-blue-400/80 hover:shadow-[0_0_20px_rgba(59,130,246,0.35)]",
      badgeColor: "bg-blue-950/80 text-blue-300 border-blue-500/40",
    },
    {
      label: "Microsoft Excel",
      desc: "Sheets & Calc",
      cmd: "Open Excel",
      icon: <FileSpreadsheet className="w-5 h-5 text-green-400" />,
      tag: "DOCS",
      glow: "hover:border-green-400/80 hover:shadow-[0_0_20px_rgba(34,197,94,0.35)]",
      badgeColor: "bg-green-950/80 text-green-300 border-green-500/40",
    },
    {
      label: "File Explorer",
      desc: "System Storage",
      cmd: "Browse files in D:\\",
      icon: <Folder className="w-5 h-5 text-amber-400" />,
      tag: "DISK",
      glow: "hover:border-amber-400/80 hover:shadow-[0_0_20px_rgba(245,158,11,0.35)]",
      badgeColor: "bg-amber-950/80 text-amber-300 border-amber-500/40",
    },
    {
      label: "Gmail Inbox",
      desc: "Live Email Hub",
      cmd: "Check my mail",
      icon: <Mail className="w-5 h-5 text-purple-400" />,
      tag: "MAIL",
      glow: "hover:border-purple-400/80 hover:shadow-[0_0_20px_rgba(168,85,247,0.35)]",
      badgeColor: "bg-purple-950/80 text-purple-300 border-purple-500/40",
    },
    {
      label: "System Apps",
      desc: "133 Programs",
      cmd: "Analyze apps in my system",
      icon: <Layers className="w-5 h-5 text-pink-400" />,
      tag: "APPS",
      glow: "hover:border-pink-400/80 hover:shadow-[0_0_20px_rgba(236,72,153,0.35)]",
      badgeColor: "bg-pink-950/80 text-pink-300 border-pink-500/40",
    },
    {
      label: "Show Desktop",
      desc: "Minimize Windows",
      cmd: "Show desktop",
      icon: <HardDrive className="w-5 h-5 text-indigo-400" />,
      tag: "SYSTEM",
      glow: "hover:border-indigo-400/80 hover:shadow-[0_0_20px_rgba(99,102,241,0.35)]",
      badgeColor: "bg-indigo-950/80 text-indigo-300 border-indigo-500/40",
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-2 py-3 z-10">
      {/* Main Holographic Locker Frame */}
      <div className="relative rounded-3xl p-5 glass-locker-card border border-cyan-500/40 shadow-[0_0_50px_rgba(0,240,255,0.18)] overflow-hidden">
        {/* Holographic HUD Watermark & Status Line */}
        <div className="flex items-center justify-between font-mono text-[10px] text-cyan-400/70 border-b border-cyan-500/20 pb-2 mb-4">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>SECURE AI LOCKER // AUTHENTICATED: BUNTY</span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-cyan-300">
              <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
              <span>NODE: 192.168.1.4:3000</span>
            </span>
            <span className="px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-400/40 text-[9px] text-cyan-300 font-bold">
              v2.5 FLASH
            </span>
          </div>
        </div>

        {/* Central Locker Centerpiece: Clock, Reactor Core, & Telemetry */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center mb-5">
          {/* Left: Cyber Digital Clock & Lock State */}
          <div className="flex flex-col items-center md:items-start space-y-1 p-3 rounded-2xl bg-slate-950/70 border border-cyan-500/20">
            <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400">
              <Clock className="w-3.5 h-3.5" />
              <span>SYSTEM TIME</span>
            </div>
            <div
              className="text-3xl md:text-4xl font-mono font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-sky-200 to-white tracking-widest text-glow-cyan"
              suppressHydrationWarning
            >
              {currentTime}
            </div>
            <div className="text-[10px] font-mono text-slate-400 tracking-wider" suppressHydrationWarning>
              {currentDate}
            </div>
          </div>

          {/* Center: Holographic AI Arc-Reactor Core */}
          <div className="flex flex-col items-center justify-center">
            <div
              onClick={isListening ? onStopManualListening : onStartManualListening}
              className="relative cursor-pointer group select-none flex items-center justify-center"
              title="Click to speak or say 'Hey LARA'"
            >
              {/* Outer Spin Ring */}
              <div
                className={`w-28 h-28 rounded-full border border-dashed border-cyan-400/50 transition-all duration-700 ${
                  isListening || isSpeaking ? "animate-spin-slow scale-110 border-emerald-400" : "group-hover:rotate-45"
                }`}
              />

              {/* Inner Reverse Spin Ring */}
              <div
                className={`absolute w-22 h-22 rounded-full border border-cyan-500/40 transition-all duration-700 ${
                  isListening || isSpeaking ? "animate-spin-slow-reverse border-emerald-400/70" : ""
                }`}
              />

              {/* Glowing Core Sphere */}
              <div
                className={`absolute w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 border border-white/60 ${
                  isListening
                    ? "bg-gradient-to-tr from-emerald-500 to-teal-400 shadow-[0_0_35px_rgba(16,185,129,0.9)] animate-pulse"
                    : isSpeaking
                    ? "bg-gradient-to-tr from-purple-500 to-fuchsia-400 shadow-[0_0_35px_rgba(168,85,247,0.9)]"
                    : isThinking
                    ? "bg-gradient-to-tr from-amber-500 to-yellow-400 shadow-[0_0_35px_rgba(245,158,11,0.8)] animate-spin"
                    : "bg-gradient-to-tr from-cyan-500 via-sky-400 to-blue-600 shadow-[0_0_28px_rgba(0,240,255,0.7)] group-hover:scale-105"
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-slate-950/80 flex items-center justify-center">
                  <Zap
                    className={`w-4 h-4 ${
                      isListening
                        ? "text-emerald-300 animate-bounce"
                        : isSpeaking
                        ? "text-purple-300"
                        : isThinking
                        ? "text-amber-300"
                        : "text-cyan-300"
                    }`}
                  />
                </div>
              </div>
            </div>

            {/* Dynamic Status Text */}
            <div className="mt-3 text-center">
              <span className="font-mono text-xs font-bold tracking-widest text-white block">
                {isListening
                  ? "LISTENING • SPEAK NOW"
                  : isSpeaking
                  ? "LARA SPEAKING..."
                  : isThinking
                  ? "ANALYZING DIRECTIVE..."
                  : "SAY 'HEY LARA' TO WAKE"}
              </span>
              <span className="font-mono text-[10px] text-cyan-400/80">
                {isListening ? "Say 'LARA open whatsapp' or 'type text'" : "AI Voice Reactor Active"}
              </span>
            </div>
          </div>

          {/* Right: Hardware Telemetry Metrics */}
          <div className="flex flex-col space-y-2 p-3 rounded-2xl bg-slate-950/70 border border-cyan-500/20 text-[11px] font-mono">
            <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-1">
              <span className="flex items-center gap-1 text-cyan-300 font-bold">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>CORE METRICS</span>
              </span>
              <span className="text-emerald-400 text-[10px]">ALL SYSTEMS GO</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">VOICE:</span>
              <span className="text-cyan-300 font-semibold">JENNY NEURAL (ZERO ECHO)</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">ENGINE:</span>
              <span className="text-purple-300 font-semibold">GEMINI 2.5 LIVE</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">WORKSPACE:</span>
              <span className="text-emerald-300 font-semibold">D:\LARA (ONLINE)</span>
            </div>
          </div>
        </div>

        {/* Live Voice Typist & Speech Capturing Stream */}
        {interimTranscript && (
          <div className="mb-4 p-3 rounded-2xl bg-cyan-950/90 border border-cyan-400 shadow-[0_0_30px_rgba(0,240,255,0.35)] animate-pulse">
            <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300 mb-1">
              <span className="flex items-center gap-1.5 font-bold">
                <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" />
                <span>LIVE VOICE STREAM DIRECTIVE:</span>
              </span>
              <span className="text-slate-400 text-[10px]">CAPTURING...</span>
            </div>
            <p className="font-mono text-sm text-white font-semibold tracking-wide">
              &gt; {interimTranscript}
            </p>
          </div>
        )}

        {/* Apps Locker Grid - 8 Glowing Sci-Fi Cards */}
        <div className="mb-4">
          <div className="flex items-center justify-between font-mono text-xs text-slate-400 mb-2 px-1">
            <span className="font-bold text-cyan-300 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>APPS LOCKER &amp; LAUNCHER NODES:</span>
            </span>
            <span className="text-[10px] text-slate-500">CLICK OR SAY &quot;OPEN &lt;APP&gt;&quot;</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {appLockerCards.map((card, i) => (
              <div
                key={i}
                onClick={() => handleQuickLaunch(card.cmd)}
                className={`cursor-pointer p-3 rounded-2xl bg-slate-950/80 border border-slate-800 transition-all duration-300 ${card.glow} flex flex-col justify-between group`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 group-hover:scale-110 transition-all">
                    {card.icon}
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold border ${card.badgeColor}`}>
                    {card.tag}
                  </span>
                </div>
                <div>
                  <div className="font-mono text-xs font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                    {card.label}
                  </div>
                  <div className="font-mono text-[10px] text-slate-500">
                    {card.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Command Runner & Voice Typist Quick Bar */}
        <form onSubmit={handleCustomSubmit} className="flex items-center gap-2 pt-2 border-t border-cyan-500/20">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Terminal className="w-4 h-4 text-cyan-400" />
            </div>
            <input
              type="text"
              placeholder="Speak or type directive: 'Open WhatsApp', 'cmd dir', 'type my notes', 'check mail'..."
              value={cmdInput}
              onChange={(e) => setCmdInput(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950/90 border border-slate-700 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 shadow-inner transition-all"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.4)] flex items-center gap-1.5 flex-shrink-0"
          >
            <span>RUN</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
