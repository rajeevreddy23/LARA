"use client";

import React, { useRef, useEffect } from "react";
import { VoiceState } from "@/hooks/useVoiceAssistant";
import {
  Folder,
  Brain,
  MessageSquare,
  Mail,
  Globe,
  Terminal,
  Smartphone,
  Volume2,
  Sparkles,
  Zap,
} from "lucide-react";

interface HolographicGlobeProps {
  voiceState: VoiceState;
  interimTranscript: string;
  isWakeWordActive: boolean;
  onExecuteCommand: (cmd: string) => void;
  onStartManualListening: () => void;
  onStopManualListening: () => void;
}

interface OrbitNode {
  name: string;
  category: string;
  icon: string;
  cmd: string;
  angle: number;
  radius: number;
  speed: number;
  color: string;
}

export const HolographicGlobeVisualizer: React.FC<HolographicGlobeProps> = ({
  voiceState,
  interimTranscript,
  isWakeWordActive,
  onExecuteCommand,
  onStartManualListening,
  onStopManualListening,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const isListening = voiceState === "listening";
  const isSpeaking = voiceState === "speaking";
  const isThinking = voiceState === "thinking";

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let rotationAngle = 0;

    // Orbiting system files and neural network nodes
    const nodes: OrbitNode[] = [
      { name: "FILES // D:\\LARA", category: "STORAGE", icon: "folder", cmd: "Browse files in D:\\", angle: 0, radius: 180, speed: 0.008, color: "#38bdf8" },
      { name: "WHATSAPP GATEWAY", category: "COMM", icon: "whatsapp", cmd: "Open WhatsApp", angle: Math.PI / 4, radius: 210, speed: 0.006, color: "#34d399" },
      { name: "GEMINI 2.5 LIVE", category: "AI CORE", icon: "brain", cmd: "What can you do?", angle: Math.PI / 2, radius: 170, speed: 0.01, color: "#c084fc" },
      { name: "GMAIL SSL SYNC", category: "MAIL", icon: "mail", cmd: "Check my mail", angle: (3 * Math.PI) / 4, radius: 220, speed: 0.007, color: "#f472b6" },
      { name: "CHROME & WEB", category: "NAVIGATOR", icon: "globe", cmd: "Open Chrome", angle: Math.PI, radius: 190, speed: 0.009, color: "#22d3ee" },
      { name: "CMD / POWERSHELL", category: "TERMINAL", icon: "terminal", cmd: "cmd dir", angle: (5 * Math.PI) / 4, radius: 215, speed: 0.006, color: "#fbbf24" },
      { name: "MOBILE QR NODE", category: "BRIDGE", icon: "mobile", cmd: "System stats", angle: (3 * Math.PI) / 2, radius: 175, speed: 0.008, color: "#818cf8" },
      { name: "JENNY NEURAL TTS", category: "AUDIO", icon: "audio", cmd: "Run system diagnostic", angle: (7 * Math.PI) / 4, radius: 200, speed: 0.007, color: "#4ade80" },
    ];

    // Data packet signals traversing connecting lines
    const packets = Array.from({ length: 16 }).map(() => ({
      nodeIndex: Math.floor(Math.random() * nodes.length),
      progress: Math.random(),
      speed: 0.01 + Math.random() * 0.015,
    }));

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resize();
    window.addEventListener("resize", resize);

    const render = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      const centerX = width / 2;
      const centerY = height / 2;

      ctx.clearRect(0, 0, width, height);

      // Determine state theme colors
      let primaryGlow = "#00f0ff";
      let secondaryGlow = "#a855f7";
      let rotationSpeed = 0.006;

      if (isListening) {
        primaryGlow = "#10b981";
        secondaryGlow = "#34d399";
        rotationSpeed = 0.012;
      } else if (isSpeaking) {
        primaryGlow = "#c084fc";
        secondaryGlow = "#e879f9";
        rotationSpeed = 0.016;
      } else if (isThinking) {
        primaryGlow = "#fbbf24";
        secondaryGlow = "#f59e0b";
        rotationSpeed = 0.02;
      }

      rotationAngle += rotationSpeed;

      // 1. Draw 3D Rotating Wireframe Holographic Globe
      const globeRadius = Math.min(centerX, centerY) * 0.46;
      const numRings = 7;
      const numMeridians = 8;

      ctx.save();
      ctx.translate(centerX, centerY);

      // Ambient Core Aura
      const radialGrad = ctx.createRadialGradient(0, 0, 10, 0, 0, globeRadius * 1.3);
      radialGrad.addColorStop(0, `${primaryGlow}22`);
      radialGrad.addColorStop(0.5, `${secondaryGlow}11`);
      radialGrad.addColorStop(1, "transparent");
      ctx.fillStyle = radialGrad;
      ctx.beginPath();
      ctx.arc(0, 0, globeRadius * 1.3, 0, Math.PI * 2);
      ctx.fill();

      // Draw Rotating Latitudinal Rings
      for (let i = 1; i < numRings; i++) {
        const latAngle = ((i / numRings) - 0.5) * Math.PI;
        const ringRadius = globeRadius * Math.cos(latAngle);
        const y = globeRadius * Math.sin(latAngle);

        ctx.beginPath();
        ctx.ellipse(0, y, ringRadius, ringRadius * 0.32, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `${primaryGlow}44`;
        ctx.lineWidth = 1;
        ctx.shadowBlur = 8;
        ctx.shadowColor = primaryGlow;
        ctx.stroke();
      }

      // Draw Rotating Longitudinal Meridian Curves (3D Perspective Math)
      for (let m = 0; m < numMeridians; m++) {
        const meridianAngle = rotationAngle + (m * Math.PI) / numMeridians;
        const xFactor = Math.sin(meridianAngle);

        ctx.beginPath();
        ctx.ellipse(0, 0, Math.abs(globeRadius * xFactor), globeRadius, 0, 0, Math.PI * 2);
        ctx.strokeStyle = xFactor > 0 ? `${primaryGlow}55` : `${secondaryGlow}25`;
        ctx.lineWidth = xFactor > 0 ? 1.4 : 0.8;
        ctx.shadowBlur = 10;
        ctx.shadowColor = primaryGlow;
        ctx.stroke();
      }

      // Outer Glowing Equatorial Boundary Ring
      ctx.beginPath();
      ctx.arc(0, 0, globeRadius, 0, Math.PI * 2);
      ctx.strokeStyle = primaryGlow;
      ctx.lineWidth = 1.6;
      ctx.shadowBlur = 16;
      ctx.shadowColor = primaryGlow;
      ctx.stroke();

      // 2. Draw Orbiting Neural Network Nodes & Connecting Lines
      nodes.forEach((node) => {
        node.angle += node.speed;
        const nodeX = Math.cos(node.angle) * node.radius;
        const nodeY = Math.sin(node.angle) * (node.radius * 0.58);

        // Draw Neural Laser Line from Center Globe to Node
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(nodeX, nodeY);
        ctx.strokeStyle = `${node.color}33`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Draw Node Outer Ring
        ctx.beginPath();
        ctx.arc(nodeX, nodeY, 6, 0, Math.PI * 2);
        ctx.fillStyle = "#020617";
        ctx.fill();
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 1.8;
        ctx.shadowBlur = 12;
        ctx.shadowColor = node.color;
        ctx.stroke();

        // Draw Node Center Core Particle
        ctx.beginPath();
        ctx.arc(nodeX, nodeY, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();

        // Draw Node Label Text
        ctx.font = "bold 9px monospace";
        ctx.fillStyle = node.color;
        ctx.shadowBlur = 6;
        ctx.shadowColor = node.color;
        ctx.fillText(node.name, nodeX + 10, nodeY + 3);
      });

      // 3. Draw Traveling Data Packets along Neural Lines
      packets.forEach((pkt) => {
        pkt.progress += pkt.speed;
        if (pkt.progress >= 1) {
          pkt.progress = 0;
          pkt.nodeIndex = Math.floor(Math.random() * nodes.length);
        }

        const targetNode = nodes[pkt.nodeIndex];
        const targetX = Math.cos(targetNode.angle) * targetNode.radius;
        const targetY = Math.sin(targetNode.angle) * (targetNode.radius * 0.58);

        const currentX = targetX * pkt.progress;
        const currentY = targetY * pkt.progress;

        ctx.beginPath();
        ctx.arc(currentX, currentY, 2, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.shadowBlur = 10;
        ctx.shadowColor = targetNode.color;
        ctx.fill();
      });

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isListening, isSpeaking, isThinking]);

  return (
    <div className="relative w-full max-w-5xl mx-auto px-2 py-4 mb-2 select-none">
      {/* Central 3D Canvas Visualizer Container */}
      <div className="relative w-full h-[360px] md:h-[420px] rounded-3xl overflow-hidden glass-panel border border-cyan-500/40 shadow-[0_0_50px_rgba(0,240,255,0.2)] flex items-center justify-center">
        {/* Background 3D Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none"
        />

        {/* Centerpiece Floating Cybernetic Greeting */}
        <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 pointer-events-auto">
          {/* Glowing Animated Hologram Ring */}
          <div
            onClick={isListening ? onStopManualListening : onStartManualListening}
            className={`p-4 rounded-full cursor-pointer transition-all duration-500 transform hover:scale-110 mb-3 border ${
              isListening
                ? "bg-emerald-950/80 border-emerald-400 shadow-[0_0_40px_rgba(16,185,129,0.9)] animate-pulse"
                : isSpeaking
                ? "bg-purple-950/80 border-purple-400 shadow-[0_0_40px_rgba(168,85,247,0.9)]"
                : isThinking
                ? "bg-amber-950/80 border-amber-400 shadow-[0_0_40px_rgba(245,158,11,0.9)] animate-spin"
                : "bg-slate-950/80 border-cyan-400/70 hover:border-cyan-300 shadow-[0_0_35px_rgba(0,240,255,0.8)]"
            }`}
            title="Click to talk or say 'Hey LARA'"
          >
            <Zap
              className={`w-8 h-8 ${
                isListening
                  ? "text-emerald-300 animate-bounce"
                  : isSpeaking
                  ? "text-purple-300 animate-pulse"
                  : isThinking
                  ? "text-amber-300"
                  : "text-cyan-300"
              }`}
            />
          </div>

          {/* Glowing Neon Center Text: "HEY, THIS IS LARA" */}
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-4xl md:text-5xl font-mono font-extrabold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-sky-200 to-white text-glow-cyan">
              HEY, THIS IS LARA
            </h1>
            <p className="font-mono text-xs sm:text-sm font-semibold tracking-wider text-cyan-400/90 text-glow-cyan">
              AUTONOMOUS INTELLIGENCE ENGINE // STANDING BY
            </p>
            <p className="font-mono text-[11px] text-slate-400 tracking-wide">
              {isListening
                ? "🎙️ LISTENING TO YOUR DIRECTIVE... SPEAK FREELY"
                : isSpeaking
                ? "🔊 TRANSMITTING REAL-TIME NEURAL VOICE..."
                : isThinking
                ? "⚡ REASONING DIRECTIVE & SYNTHESIZING TOOLS..."
                : "SAY 'HEY LARA' OR CLICK CORE TO COMMAND"}
            </p>
          </div>

          {/* Live Voice Typist Directive Stream */}
          {interimTranscript && (
            <div className="mt-3 px-4 py-2 rounded-xl bg-cyan-950/90 border border-cyan-400 shadow-[0_0_25px_rgba(0,240,255,0.4)] animate-pulse max-w-lg">
              <span className="text-[10px] font-mono text-cyan-300 font-bold block mb-0.5">
                VOICE DIRECTIVE CAPTURED:
              </span>
              <p className="font-mono text-xs text-white font-semibold">
                &gt; {interimTranscript}
              </p>
            </div>
          )}
        </div>

        {/* Bottom Fast Action Nodes Pill Bar */}
        <div className="absolute bottom-2 inset-x-0 flex items-center justify-center gap-2 px-4 overflow-x-auto pb-1">
          <button
            onClick={() => onExecuteCommand("Open Google AI Studio")}
            className="px-3 py-1 rounded-full bg-purple-950/90 border border-purple-400 text-purple-200 hover:border-purple-300 text-xs font-mono font-bold flex items-center gap-1.5 shadow-[0_0_12px_rgba(168,85,247,0.4)] transition-all flex-shrink-0"
          >
            <Brain className="w-3 h-3 text-purple-300" />
            <span>AI Studio</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Open WhatsApp")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-emerald-500/40 text-emerald-300 hover:border-emerald-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <MessageSquare className="w-3 h-3" />
            <span>WhatsApp</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Open Chrome")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-cyan-500/40 text-cyan-300 hover:border-cyan-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <Globe className="w-3 h-3" />
            <span>Chrome</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Open VS Code")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-blue-500/40 text-blue-300 hover:border-blue-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <Brain className="w-3 h-3" />
            <span>VS Code</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Browse files in D:\\")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-amber-500/40 text-amber-300 hover:border-amber-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <Folder className="w-3 h-3" />
            <span>Files</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Check my mail")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-purple-500/40 text-purple-300 hover:border-purple-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <Mail className="w-3 h-3" />
            <span>Mail</span>
          </button>
          <button
            onClick={() => onExecuteCommand("Analyze apps in my system")}
            className="px-3 py-1 rounded-full bg-slate-950/90 border border-pink-500/40 text-pink-300 hover:border-pink-400 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all flex-shrink-0"
          >
            <Terminal className="w-3 h-3" />
            <span>Apps</span>
          </button>
        </div>
      </div>
    </div>
  );
};
