"use client";

import React from "react";
import {
  Cpu,
  Mail,
  FolderOpen,
  Music,
  Video,
  MessageCircle,
  Calculator,
  FileText,
  Activity,
  Globe,
  Sparkles,
  Command,
  Code,
} from "lucide-react";

interface SystemControlWidgetProps {
  onExecuteCommand: (command: string) => void;
}

export const SystemControlWidget: React.FC<SystemControlWidgetProps> = ({
  onExecuteCommand,
}) => {
  const quickActions = [
    {
      label: "Check Mail",
      cmd: "check my mail",
      icon: <Mail className="w-3.5 h-3.5 text-purple-400" />,
      tag: "INBOX",
    },
    {
      label: "Downloads Folder",
      cmd: "list files in downloads",
      icon: <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />,
      tag: "FILES",
    },
    {
      label: "Open WhatsApp",
      cmd: "open whatsapp",
      icon: <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />,
      tag: "MOBILE/WEB",
    },
    {
      label: "Open Gmail",
      cmd: "open gmail",
      icon: <Mail className="w-3.5 h-3.5 text-rose-400" />,
      tag: "WEBMAIL",
    },
    {
      label: "Open Spotify",
      cmd: "open spotify",
      icon: <Music className="w-3.5 h-3.5 text-green-400" />,
      tag: "MEDIA",
    },
    {
      label: "Open YouTube",
      cmd: "open youtube",
      icon: <Video className="w-3.5 h-3.5 text-red-400" />,
      tag: "STREAM",
    },
    {
      label: "Open VS Code",
      cmd: "open vs code",
      icon: <Code className="w-3.5 h-3.5 text-blue-400" />,
      tag: "IDE",
    },
    {
      label: "System Specs",
      cmd: "check my system stats",
      icon: <Cpu className="w-3.5 h-3.5 text-amber-400" />,
      tag: "HARDWARE",
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 my-2">
      <div className="glass-panel border-cyan-500/20 rounded-xl p-3 bg-slate-950/60 backdrop-blur-md shadow-[0_0_20px_rgba(6,182,212,0.1)]">
        <div className="flex items-center justify-between pb-2 border-b border-cyan-500/10 mb-2.5">
          <div className="flex items-center gap-2">
            <Command className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[11px] font-mono uppercase tracking-wider text-cyan-300 font-bold">
              CROSS-DEVICE &amp; SYSTEM DIRECTIVES
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            DESKTOP &amp; MOBILE ECOSYSTEM
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => onExecuteCommand(action.cmd)}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-cyan-950/40 border border-slate-800 hover:border-cyan-500/40 transition-all duration-200 group text-left cursor-pointer"
            >
              <div className="flex items-center gap-2 truncate">
                <div className="p-1 rounded bg-slate-950 border border-slate-800 group-hover:border-cyan-500/40 transition-colors flex-shrink-0">
                  {action.icon}
                </div>
                <span className="text-xs font-mono text-slate-200 group-hover:text-cyan-200 font-medium truncate">
                  {action.label}
                </span>
              </div>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 group-hover:border-cyan-500/30 group-hover:text-cyan-300 font-bold flex-shrink-0 ml-1">
                {action.tag}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
