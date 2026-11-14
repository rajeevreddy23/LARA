"use client";

import React, { useState, useEffect } from "react";
import {
  Folder,
  FolderOpen,
  FileText,
  Search,
  HardDrive,
  Download,
  Laptop,
  FileCode,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
  X,
  Plus,
} from "lucide-react";
import { browseSystemFiles, FileItem, FileBrowseResponse } from "@/lib/api";

interface FileExplorerWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteCommand: (command: string) => void;
}

const QUICK_FOLDERS = [
  { name: "Downloads", path: "Downloads", icon: Download },
  { name: "Desktop", path: "Desktop", icon: Laptop },
  { name: "Documents", path: "Documents", icon: FileText },
  { name: "D:\\LARA", path: "D:\\LARA", icon: FileCode },
  { name: "D:\\ Drive", path: "D:\\", icon: HardDrive },
  { name: "C:\\ Drive", path: "C:\\", icon: HardDrive },
];

export const FileExplorerWidget: React.FC<FileExplorerWidgetProps> = ({
  isOpen,
  onClose,
  onExecuteCommand,
}) => {
  const [currentPath, setCurrentPath] = useState<string>("D:\\LARA");
  const [browseData, setBrowseData] = useState<FileBrowseResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchDirectory = async (targetPath: string) => {
    setIsLoading(true);
    try {
      const data = await browseSystemFiles(targetPath);
      setBrowseData(data);
      setCurrentPath(data.path);
    } catch (err) {
      console.error("Directory browse error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDirectory(currentPath);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFolderClick = (path: string) => {
    fetchDirectory(path);
  };

  const handleOpenNative = (path: string, isFolder: boolean) => {
    const cmd = isFolder ? `Open folder ${path}` : `Open file ${path}`;
    onExecuteCommand(cmd);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    onExecuteCommand(`Find files ${searchQuery.trim()}`);
    onClose();
  };

  const filteredItems = (browseData?.items || []).filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col glass-panel border border-cyan-500/40 rounded-2xl p-6 shadow-[0_0_50px_rgba(0,240,255,0.25)] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-400/50 text-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.3)]">
              <FolderOpen className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono font-bold text-lg text-white tracking-wider">
                  SYSTEM FILE &amp; FOLDER HUB
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-400/50 text-[10px] font-mono font-bold text-cyan-300">
                  WINDOWS LIVE
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Browse, search, inspect, and open any file or directory on your PC
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchDirectory(currentPath)}
              className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 hover:border-cyan-400 transition-all"
              title="Refresh directory"
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

        {/* Quick Nav Chips */}
        <div className="flex items-center gap-2 py-3 overflow-x-auto border-b border-slate-800/80">
          {QUICK_FOLDERS.map((f, idx) => {
            const Icon = f.icon;
            const isCurrent = currentPath.toLowerCase().includes(f.name.toLowerCase());
            return (
              <button
                key={idx}
                onClick={() => handleFolderClick(f.path)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all flex-shrink-0 border ${
                  isCurrent
                    ? "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-glow-sm"
                    : "bg-slate-900/80 border-slate-700 text-slate-300 hover:border-cyan-500/50 hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5 text-cyan-400" />
                <span>{f.name}</span>
              </button>
            );
          })}
        </div>

        {/* Search & Current Path Breadcrumb */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 py-3 items-center">
          <div className="md:col-span-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-950/90 border border-slate-700 font-mono text-xs text-cyan-300 overflow-hidden">
            {browseData?.parent_path && (
              <button
                onClick={() => handleFolderClick(browseData.parent_path!)}
                className="p-1 hover:text-white hover:bg-slate-800 rounded transition-all"
                title="Go up to parent folder"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
              </button>
            )}
            <span className="text-slate-500 truncate">Path:</span>
            <span className="truncate flex-1">{currentPath}</span>
            <button
              onClick={() => handleOpenNative(currentPath, true)}
              className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500/40 text-[10px] text-cyan-300 font-bold hover:bg-cyan-900 transition-all flex-shrink-0 flex items-center gap-1"
              title="Open folder in Windows Explorer"
            >
              <span>EXPLORER</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>

          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search files or extension..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-all"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-3 pointer-events-none" />
          </form>
        </div>

        {/* File Table Content */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1 min-h-[260px] max-h-[420px] rounded-xl bg-slate-950/60 p-2 border border-slate-800">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 gap-2 font-mono text-xs text-cyan-400 animate-pulse">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Scanning system directory...</span>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 font-mono text-xs text-slate-500">
              <Folder className="w-8 h-8 text-slate-700 mb-2" />
              <span>No items found in this directory.</span>
            </div>
          ) : (
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] text-slate-400">
                  <th className="py-2 px-3">Name</th>
                  <th className="py-2 px-3 hidden sm:table-cell">Size</th>
                  <th className="py-2 px-3 hidden md:table-cell">Modified</th>
                  <th className="py-2 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {filteredItems.map((item, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-cyan-950/20 transition-colors group cursor-pointer"
                    onClick={() => {
                      if (item.is_dir) {
                        handleFolderClick(item.path);
                      }
                    }}
                  >
                    <td className="py-2 px-3 flex items-center gap-2.5">
                      {item.is_dir ? (
                        <Folder className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                      ) : (
                        <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      )}
                      <span
                        className={`truncate max-w-xs md:max-w-md ${
                          item.is_dir
                            ? "text-cyan-200 font-semibold group-hover:text-cyan-100"
                            : "text-slate-200"
                        }`}
                      >
                        {item.name}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400 hidden sm:table-cell">
                      {item.is_dir ? "—" : `${item.size_kb} KB`}
                    </td>
                    <td className="py-2 px-3 text-slate-500 hidden md:table-cell">
                      {item.modified}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenNative(item.path, item.is_dir);
                        }}
                        className="px-2 py-1 rounded bg-slate-900 hover:bg-cyan-500 hover:text-slate-950 border border-slate-700 text-[10px] font-bold transition-all inline-flex items-center gap-1"
                        title={item.is_dir ? "Open folder" : "Open file"}
                      >
                        <span>{item.is_dir ? "OPEN" : "LAUNCH"}</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] font-mono text-slate-500">
            Tip: Say <em>&quot;Hey LARA, show files in Downloads&quot;</em> or <em>&quot;Open folder Desktop&quot;</em>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs shadow-glow-sm transition-all"
          >
            DONE
          </button>
        </div>
      </div>
    </div>
  );
};
