"use client";

import React, { useState, useEffect } from "react";
import {
  Grid,
  Search,
  RefreshCw,
  ExternalLink,
  X,
  Sparkles,
  Code,
  Globe,
  FileText,
  Music,
  Settings,
  Gamepad2,
  Layers,
  Play,
} from "lucide-react";
import { getInstalledApps, SystemAppItem, SystemAppsResponse } from "@/lib/api";

interface AppsExplorerWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteCommand: (command: string) => void;
}

export const AppsExplorerWidget: React.FC<AppsExplorerWidgetProps> = ({
  isOpen,
  onClose,
  onExecuteCommand,
}) => {
  const [appsData, setAppsData] = useState<SystemAppsResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchApps = async () => {
    setIsLoading(true);
    try {
      const data = await getInstalledApps();
      setAppsData(data);
    } catch (err) {
      console.error("System apps fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchApps();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const categories = ["ALL", "PRODUCTIVITY", "INTERNET", "DEVELOPMENT", "SYSTEM", "MEDIA", "GAMES"];

  const getCategoryIcon = (cat: string) => {
    switch (cat.toUpperCase()) {
      case "DEVELOPMENT":
        return <Code className="w-3.5 h-3.5 text-blue-400" />;
      case "INTERNET":
        return <Globe className="w-3.5 h-3.5 text-emerald-400" />;
      case "MEDIA":
        return <Music className="w-3.5 h-3.5 text-purple-400" />;
      case "SYSTEM":
        return <Settings className="w-3.5 h-3.5 text-amber-400" />;
      case "GAMES":
        return <Gamepad2 className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <FileText className="w-3.5 h-3.5 text-cyan-400" />;
    }
  };

  const filteredApps = (appsData?.apps || []).filter((app) => {
    const matchesCategory =
      selectedCategory === "ALL" ||
      app.category.toUpperCase() === selectedCategory;
    const matchesSearch =
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleLaunchApp = (appName: string) => {
    onExecuteCommand(`Open ${appName}`);
  };

  const handleAnalyzeWithGemini = () => {
    onExecuteCommand("Analyze installed apps in my system");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col glass-panel border border-cyan-500/40 rounded-2xl p-6 shadow-[0_0_50px_rgba(0,240,255,0.25)] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-400/50 text-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.3)]">
              <Grid className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono font-bold text-lg text-white tracking-wider">
                  SYSTEM APPS &amp; TOOLS HUB
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-400/50 text-[10px] font-mono font-bold text-cyan-300">
                  {appsData?.total || 0} APPS DETECTED
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Real-time index of all installed Windows applications, programs &amp; tools
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyzeWithGemini}
              className="px-2.5 py-1.5 rounded-lg bg-purple-950/60 border border-purple-400/50 text-purple-300 hover:bg-purple-900/60 text-xs font-mono flex items-center gap-1 transition-all"
              title="Analyze installed apps with Gemini AI"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span className="hidden sm:inline">AI ANALYZE</span>
            </button>
            <button
              onClick={fetchApps}
              className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 hover:border-cyan-400 transition-all"
              title="Rescan installed apps"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-cyan-400" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex items-center gap-1.5 py-3 overflow-x-auto border-b border-slate-800/80">
          {categories.map((cat, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all flex-shrink-0 border ${
                selectedCategory === cat
                  ? "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-glow-sm"
                  : "bg-slate-900/80 border-slate-700 text-slate-300 hover:border-cyan-500/50 hover:text-white"
              }`}
            >
              {cat !== "ALL" && getCategoryIcon(cat)}
              <span>{cat}</span>
            </button>
          ))}
        </div>

        {/* Search Filter */}
        <div className="py-3 relative">
          <input
            type="text"
            placeholder="Search apps (e.g. Excel, Chrome, Word, Notepad++, VS Code, Spotify)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-all"
          />
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-5 pointer-events-none" />
        </div>

        {/* Apps Grid */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1 min-h-[280px] max-h-[420px] rounded-xl bg-slate-950/60 p-3 border border-slate-800">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 gap-2 font-mono text-xs text-cyan-400 animate-pulse">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Indexing installed programs on Windows...</span>
            </div>
          ) : filteredApps.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 font-mono text-xs text-slate-500">
              <Layers className="w-8 h-8 text-slate-700 mb-2" />
              <span>No applications matching query.</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {filteredApps.map((app, idx) => (
                <div
                  key={idx}
                  onClick={() => handleLaunchApp(app.name)}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 hover:bg-cyan-950/40 border border-slate-800 hover:border-cyan-500/40 transition-all duration-200 group cursor-pointer"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <div className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 group-hover:border-cyan-500/40 transition-colors flex-shrink-0">
                      {getCategoryIcon(app.category)}
                    </div>
                    <div className="truncate">
                      <span className="text-xs font-mono font-bold text-slate-200 group-hover:text-cyan-200 truncate block">
                        {app.name}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">
                        {app.category}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchApp(app.name);
                    }}
                    className="p-1.5 rounded-md bg-slate-950 hover:bg-cyan-500 hover:text-slate-950 border border-slate-800 text-cyan-400 transition-all flex-shrink-0 ml-2"
                    title={`Launch ${app.name}`}
                  >
                    <Play className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] font-mono text-slate-500">
            Tip: Say <em>&quot;LARA, open Excel&quot;</em> or <em>&quot;LARA, open Word&quot;</em>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs shadow-glow-sm transition-all"
          >
            DISMISS
          </button>
        </div>
      </div>
    </div>
  );
};
