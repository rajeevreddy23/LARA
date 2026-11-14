"use client";

import React, { useState } from "react";
import {
  X,
  ExternalLink,
  Maximize2,
  Minimize2,
  RefreshCw,
  MessageSquare,
  Globe,
  Code,
  FileSpreadsheet,
  Folder,
  Mail,
  Terminal,
  Calculator,
  Video,
  Play,
  CheckCircle2,
  Activity,
  Layers,
} from "lucide-react";

export interface ActiveAppItem {
  id: string;
  name: string;
  category: string;
  iconType: string;
  webUrl?: string;
  localPath?: string;
  status: "active" | "launching" | "ready";
  details?: string;
}

interface AppViewerStageProps {
  activeApp: ActiveAppItem | null;
  onClose: () => void;
  onExecuteCommand: (cmd: string) => void;
}

export const AppViewerStage: React.FC<AppViewerStageProps> = ({
  activeApp,
  onClose,
  onExecuteCommand,
}) => {
  const [isMaximized, setIsMaximized] = useState<boolean>(false);
  const [isIframeLoaded, setIsIframeLoaded] = useState<boolean>(false);

  if (!activeApp) return null;

  const renderAppIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "whatsapp":
      case "messagesquare":
        return <MessageSquare className="w-5 h-5 text-emerald-400" />;
      case "chrome":
      case "globe":
      case "youtube":
      case "video":
        return <Globe className="w-5 h-5 text-cyan-400" />;
      case "vscode":
      case "code":
        return <Code className="w-5 h-5 text-blue-400" />;
      case "excel":
      case "filespreadsheet":
        return <FileSpreadsheet className="w-5 h-5 text-green-400" />;
      case "files":
      case "folder":
        return <Folder className="w-5 h-5 text-amber-400" />;
      case "mail":
        return <Mail className="w-5 h-5 text-purple-400" />;
      case "terminal":
      case "cmd":
        return <Terminal className="w-5 h-5 text-yellow-400" />;
      default:
        return <Activity className="w-5 h-5 text-cyan-400" />;
    }
  };

  const isWebUrl = Boolean(activeApp.webUrl);

  return (
    <div className="w-full max-w-5xl mx-auto px-2 mb-4 animate-in fade-in slide-in-from-top-4 duration-300">
      <div
        className={`rounded-3xl glass-panel border border-cyan-500/40 shadow-[0_0_45px_rgba(0,240,255,0.2)] overflow-hidden transition-all duration-300 ${
          isMaximized ? "h-[620px]" : "h-[360px]"
        } flex flex-col bg-slate-950/90`}
      >
        {/* App Stage Window Header */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-cyan-500/30">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-slate-950 border border-cyan-500/40">
              {renderAppIcon(activeApp.iconType || activeApp.name)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-white tracking-wider">
                  {activeApp.name.toUpperCase()} // IN-PAGE STAGE
                </span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-[9px] font-mono text-emerald-300 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  <span>ACTIVE</span>
                </span>
              </div>
              <p className="font-mono text-[10px] text-slate-400">
                {activeApp.details || "Host Process Executed • Live In-Page Viewer"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {activeApp.webUrl && (
              <a
                href={activeApp.webUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all text-xs flex items-center gap-1 font-mono"
                title="Open in new browser window"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span className="hidden sm:inline text-[10px]">NEW TAB</span>
              </a>
            )}

            <button
              onClick={() => setIsMaximized((prev) => !prev)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
              title={isMaximized ? "Restore size" : "Maximize view"}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950 hover:text-rose-400 text-slate-400 transition-all"
              title="Close in-page app viewer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* App Stage Content Area */}
        <div className="flex-1 relative overflow-hidden bg-slate-950 flex flex-col justify-center items-center p-4">
          {isWebUrl ? (
            <div className="w-full h-full flex flex-col items-center justify-center relative">
              <iframe
                src={activeApp.webUrl}
                title={activeApp.name}
                className="w-full h-full rounded-xl border border-slate-800 bg-slate-900"
                onLoad={() => setIsIframeLoaded(true)}
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
              />
              <div className="absolute bottom-3 right-3 px-3 py-1.5 rounded-xl bg-slate-950/90 border border-cyan-500/40 text-[10px] font-mono text-cyan-300 shadow-lg flex items-center gap-2">
                <span>{activeApp.name} Live Gateway</span>
                <a
                  href={activeApp.webUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-400 underline font-bold"
                >
                  Open Direct Tab
                </a>
              </div>
            </div>
          ) : (
            /* System Native App Telemetry & Launcher Stage */
            <div className="flex flex-col items-center justify-center text-center space-y-4 max-w-lg">
              <div className="p-4 rounded-3xl bg-slate-900/90 border border-cyan-500/40 shadow-[0_0_30px_rgba(0,240,255,0.3)]">
                {renderAppIcon(activeApp.iconType || activeApp.name)}
              </div>
              <div className="space-y-1">
                <h3 className="font-mono text-lg font-bold text-white tracking-wider">
                  {activeApp.name} Application Active
                </h3>
                <p className="font-mono text-xs text-slate-400">
                  Application launched natively on your Windows host workstation.
                </p>
                {activeApp.localPath && (
                  <p className="font-mono text-[10px] text-cyan-400 bg-slate-900/80 px-3 py-1 rounded-lg border border-slate-800 inline-block mt-1">
                    Path: {activeApp.localPath}
                  </p>
                )}
              </div>

              {/* Quick Action Buttons for the Active App */}
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                <button
                  onClick={() => onExecuteCommand(`Open ${activeApp.name}`)}
                  className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all shadow-glow-sm flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Relaunch</span>
                </button>
                <button
                  onClick={() => onExecuteCommand("System stats")}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs transition-all border border-slate-700 flex items-center gap-1.5"
                >
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Telemetry</span>
                </button>
                <button
                  onClick={onClose}
                  className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 font-mono text-xs transition-all border border-slate-800"
                >
                  Dismiss Stage
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
