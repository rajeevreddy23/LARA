"use client";

import React from "react";
import { VoiceState } from "@/hooks/useVoiceAssistant";

export interface AudioOrbProps {
  state?: VoiceState;
  voiceState?: VoiceState;
  isThinking?: boolean;
  size?: "sm" | "md" | "lg" | string;
  onClick?: () => void;
}

export const AudioOrb: React.FC<AudioOrbProps> = ({
  state,
  voiceState,
  isThinking,
  size = "md",
  onClick,
}) => {
  const effectiveState: VoiceState =
    isThinking
      ? "thinking"
      : voiceState || state || "idle";

  const isSmall = size === "sm";

  const stateConfig = {
    idle: {
      coreColor: "from-cyan-400 via-sky-500 to-blue-600",
      glowColor: "rgba(0, 240, 255, 0.45)",
      ringColor: "border-cyan-500/40",
      label: "LARA STANDBY • SAY 'HEY LARA'",
      sublabel: "Awaiting voice directive or text command",
      barCount: isSmall ? 8 : 18,
      barColor: "bg-cyan-400",
    },
    listening: {
      coreColor: "from-emerald-400 via-teal-500 to-green-600",
      glowColor: "rgba(16, 185, 129, 0.75)",
      ringColor: "border-emerald-400/70",
      label: "ACTIVE LISTENING • SPEAK DIRECTIVE...",
      sublabel: "Continuous tasks active • Speak naturally (Say 'Thank you' to finish)",
      barCount: isSmall ? 12 : 26,
      barColor: "bg-emerald-400",
    },
    thinking: {
      coreColor: "from-amber-400 via-orange-500 to-yellow-600",
      glowColor: "rgba(245, 158, 11, 0.75)",
      ringColor: "border-amber-400/70",
      label: "SYNTHESIZING DIRECTIVE & REAL-TIME DATA...",
      sublabel: "Synthesizing 2026 cognitive memory & tools",
      barCount: isSmall ? 10 : 22,
      barColor: "bg-amber-400",
    },
    speaking: {
      coreColor: "from-purple-400 via-fuchsia-500 to-violet-600",
      glowColor: "rgba(168, 85, 247, 0.85)",
      ringColor: "border-purple-400/80",
      label: "LARA SPEAKING TO BUNTY...",
      sublabel: "High-definition neural audio stream",
      barCount: isSmall ? 14 : 30,
      barColor: "bg-purple-400",
    },
    sleep: {
      coreColor: "from-slate-600 via-slate-700 to-slate-800",
      glowColor: "rgba(100, 116, 139, 0.25)",
      ringColor: "border-slate-700/40",
      label: "LARA IN STANDBY • SAY 'HEY LARA' TO WAKE",
      sublabel: "Background listener active",
      barCount: isSmall ? 6 : 10,
      barColor: "bg-slate-600",
    },
  };

  const current = stateConfig[effectiveState] || stateConfig.idle;

  if (isSmall) {
    return (
      <div
        onClick={onClick}
        className="flex items-center gap-2 cursor-pointer group select-none"
        title="Click to activate voice"
      >
        <div className="relative flex items-center justify-center">
          <div
            className={`w-9 h-9 rounded-full bg-gradient-to-tr ${current.coreColor} shadow-md flex items-center justify-center transition-all duration-300 transform group-hover:scale-110 border border-white/50`}
            style={{ boxShadow: `0 0 16px ${current.glowColor}` }}
          >
            <div className="w-5 h-5 rounded-full bg-slate-950/80 flex items-center justify-center">
              <div
                className={`w-2.5 h-2.5 rounded-full bg-gradient-to-br ${current.coreColor} ${
                  effectiveState !== "sleep" ? "animate-pulse" : "opacity-40"
                }`}
              />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-0.5 h-4">
          {Array.from({ length: current.barCount }).map((_, i) => (
            <span
              key={i}
              className={`w-0.5 rounded-full transition-all duration-300 ${current.barColor}`}
              style={{
                height:
                  effectiveState === "speaking"
                    ? `${Math.max(3, Math.sin(i * 0.8) * 12 + 4)}px`
                    : effectiveState === "listening"
                    ? `${Math.max(2, Math.cos(i * 0.6) * 8 + 3)}px`
                    : "2px",
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="flex flex-col items-center justify-center cursor-pointer group py-4 select-none transition-all duration-500"
      title="Click to activate or speak 'Hey LARA'"
    >
      <div className="relative flex items-center justify-center">
        {/* Outer Orbital Rotating Ring */}
        <div
          className={`absolute w-40 h-40 rounded-full border border-dashed ${current.ringColor} transition-all duration-700 ${
            effectiveState === "listening" || effectiveState === "speaking"
              ? "animate-spin scale-110"
              : "group-hover:rotate-45"
          }`}
          style={{ animationDuration: "14s" }}
        />

        {/* Second Counter-Rotating Orbital Ring */}
        <div
          className={`absolute w-32 h-32 rounded-full border ${current.ringColor} opacity-70 transition-all duration-700 ${
            effectiveState === "listening" || effectiveState === "speaking"
              ? "animate-spin scale-105"
              : ""
          }`}
          style={{ animationDirection: "reverse", animationDuration: "9s" }}
        />

        {/* Ambient Halo Glow */}
        <div
          className="absolute w-28 h-28 rounded-full blur-2xl transition-all duration-500 opacity-90"
          style={{
            backgroundColor: current.glowColor,
            transform: effectiveState === "listening" || effectiveState === "speaking" ? "scale(1.5)" : "scale(1)",
          }}
        />

        {/* Central Core Reactor Sphere */}
        <div
          className={`relative w-24 h-24 rounded-full bg-gradient-to-tr ${current.coreColor} shadow-2xl flex items-center justify-center transition-all duration-500 transform group-hover:scale-105 border border-white/40`}
          style={{
            boxShadow: `0 0 40px ${current.glowColor}`,
          }}
        >
          {/* Inner Reactor Holographic Core */}
          <div className="w-14 h-14 rounded-full bg-slate-950/80 backdrop-blur-md border border-white/50 flex items-center justify-center">
            <div
              className={`w-7 h-7 rounded-full bg-gradient-to-br ${current.coreColor} ${
                effectiveState !== "sleep" ? "animate-pulse" : "opacity-40"
              }`}
            />
          </div>
        </div>
      </div>

      {/* Dynamic Soundwave Spectrum Equalizer Bars */}
      <div className="flex items-center gap-1 mt-5 h-7 px-4">
        {Array.from({ length: current.barCount }).map((_, i) => {
          const isCenter = Math.abs(i - current.barCount / 2) < current.barCount / 4;
          const heightClass =
            effectiveState === "speaking"
              ? isCenter
                ? "animate-[pulse_0.35s_ease-in-out_infinite]"
                : "animate-[pulse_0.7s_ease-in-out_infinite]"
              : effectiveState === "listening"
              ? "animate-[pulse_0.5s_ease-in-out_infinite]"
              : "h-1 opacity-30";

          return (
            <span
              key={i}
              className={`w-1 rounded-full transition-all duration-300 ${current.barColor} ${heightClass}`}
              style={{
                height:
                  effectiveState === "speaking"
                    ? `${Math.max(4, Math.sin(i * 0.6) * 22 + 8)}px`
                    : effectiveState === "listening"
                    ? `${Math.max(3, Math.cos(i * 0.5) * 16 + 6)}px`
                    : "3px",
                animationDelay: `${(i % 6) * 0.08}s`,
              }}
            />
          );
        })}
      </div>

      {/* Telemetry Status Labels */}
      <div className="text-center mt-2 space-y-0.5">
        <p className="font-mono text-xs font-bold tracking-widest text-glow-cyan text-slate-100 flex items-center justify-center gap-2">
          {current.label}
        </p>
        <p className="font-mono text-[11px] text-slate-400 tracking-wider">
          {current.sublabel}
        </p>
      </div>
    </div>
  );
};
