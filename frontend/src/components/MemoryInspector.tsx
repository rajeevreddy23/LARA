"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  FolderGit2,
  Database,
  Plus,
  X,
  Sparkles,
  CheckCircle2,
  Clock,
  Trash2,
  RefreshCw,
  HardDrive
} from "lucide-react";
import { MemoryProfileResponse, addUserFact, addProject, clearSessionMemory, deleteFact, deleteProject,
  updateProject, ProjectItem, EpisodicMemory, getEpisodes, editEpisode, deleteEpisode } from "@/lib/api";

interface MemoryInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  memoryProfile: MemoryProfileResponse | null;
  onRefresh: () => void;
}

export const MemoryInspector: React.FC<MemoryInspectorProps> = ({
  isOpen,
  onClose,
  memoryProfile,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<"facts" | "projects" | "episodes" | "stats">("facts");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editingFact, setEditingFact] = useState(false);
  const [editingProject, setEditingProject] = useState<string | null>(null);
  const [projectStatus, setProjectStatus] = useState<ProjectItem["status"]>("active");
  const [projectActions, setProjectActions] = useState("");
  const [episodes, setEpisodes] = useState<EpisodicMemory[]>([]);
  const [episodeEdit, setEpisodeEdit] = useState<string | null>(null);
  const [episodeText, setEpisodeText] = useState("");
  const [episodesLoading, setEpisodesLoading] = useState(false);
  const [newFactKey, setNewFactKey] = useState("");
  const [newFactValue, setNewFactValue] = useState("");
  const [isAddingFact, setIsAddingFact] = useState(false);

  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectSummary, setNewProjectSummary] = useState("");
  const [isAddingProject, setIsAddingProject] = useState(false);

  useEffect(() => {
    if (!isOpen || activeTab !== "episodes") return;
    let alive = true;
    setEpisodesLoading(true);
    getEpisodes().then((items) => { if (alive) setEpisodes(items); })
      .catch((err) => { if (alive) setError(err.message); })
      .finally(() => { if (alive) setEpisodesLoading(false); });
    return () => { alive = false; };
  }, [isOpen, activeTab, memoryProfile?.total_episodic_memories]);

  if (!isOpen) return null;

  const mutate = async (action: () => Promise<unknown>) => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await action();
      if (activeTab === "episodes") setEpisodes(await getEpisodes());
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Memory update failed.");
    } finally { setBusy(false); }
  };

  const handleCreateFact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFactKey.trim() || !newFactValue.trim()) return;
    if (busy) return;
    setBusy(true); setError("");
    try {
      await addUserFact(newFactKey.trim(), newFactValue.trim());
      setNewFactKey("");
      setNewFactValue("");
      setIsAddingFact(false);
      setEditingFact(false);
      onRefresh();
    } catch (err) {
      console.error("Failed to add fact:", err);
      setError(err instanceof Error ? err.message : "Failed to save fact.");
    } finally {
      setBusy(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim() || !newProjectSummary.trim()) return;
    if (busy) return;
    setBusy(true); setError("");
    try {
      const project = {
        name: newProjectName.trim(),
        summary: newProjectSummary.trim(),
        status: projectStatus,
        pending_actions: projectActions.split("\n").map((line) => line.trim()).filter(Boolean),
      };
      if (editingProject) await updateProject(editingProject, project);
      else await addProject(project);
      setNewProjectName("");
      setNewProjectSummary("");
      setIsAddingProject(false);
      setEditingProject(null);
      setProjectActions(""); setProjectStatus("active");
      onRefresh();
    } catch (err) {
      console.error("Failed to add project:", err);
      setError(err instanceof Error ? err.message : "Failed to save project.");
    } finally {
      setBusy(false);
    }
  };

  const handleClearSession = async () => {
    if (confirm("Reset current conversation buffer in memory?")) {
      await mutate(() => clearSessionMemory());
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-3xl glass-panel-glow border-cyan-500/40 rounded-2xl flex flex-col max-h-[85vh] shadow-[0_0_50px_rgba(0,240,255,0.2)] overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-cyan-500/20 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-cyan-300 shadow-glow-sm">
              <Brain className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono font-bold text-white text-sm tracking-wider">
                  LARA INTEL & MEMORY BANK
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
                  MEMORY
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-400">
                Persistent Structured State & Vector Cognitive Recall
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition-all"
              title="Refresh memory store"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              title="Close Intel HUD"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center border-b border-slate-800 px-4 bg-slate-950/40 text-xs font-mono">
          <button onClick={() => setActiveTab("episodes")} className={`py-2.5 px-3 border-b-2 ${activeTab === "episodes" ? "border-cyan-400 text-cyan-300" : "border-transparent text-slate-400"}`}>Recall</button>
          <button
            onClick={() => setActiveTab("facts")}
            className={`py-2.5 px-4 border-b-2 font-medium flex items-center gap-1.5 transition-all ${
              activeTab === "facts"
                ? "border-cyan-400 text-cyan-300 bg-cyan-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>User Facts ({Object.keys(memoryProfile?.facts || {}).length})</span>
          </button>

          <button
            onClick={() => setActiveTab("projects")}
            className={`py-2.5 px-4 border-b-2 font-medium flex items-center gap-1.5 transition-all ${
              activeTab === "projects"
                ? "border-cyan-400 text-cyan-300 bg-cyan-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Tracked Projects ({memoryProfile?.projects.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab("stats")}
            className={`py-2.5 px-4 border-b-2 font-medium flex items-center gap-1.5 transition-all ${
              activeTab === "stats"
                ? "border-cyan-400 text-cyan-300 bg-cyan-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>Storage & Telemetry</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-sm">
          {error && <p role="alert" className="p-2 text-rose-300 border border-rose-500/40 rounded">{error}</p>}
          {busy && <p role="status" className="text-cyan-300 text-xs">Saving changes…</p>}
          <p className="text-xs text-slate-400">Editing or deleting saved knowledge also clears saved conversation context to prevent stale recall.</p>
          {activeTab === "episodes" && <div className="space-y-3">
            {episodesLoading && <p role="status">Loading saved memories…</p>}
            {!episodesLoading && !episodes.length && <p className="text-slate-400">No saved recall entries yet.</p>}
            {episodes.map((memory) => <div key={memory.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <p className="text-xs text-cyan-300">{memory.source || "Conversation memory"}</p>
              {episodeEdit === memory.id ? <form onSubmit={(event) => { event.preventDefault(); mutate(async () => { await editEpisode(memory.id, episodeText); setEpisodeEdit(null); }); }} className="space-y-2">
                <textarea aria-label="Memory text" value={episodeText} onChange={(event) => setEpisodeText(event.target.value)} required maxLength={4000} className="w-full rounded bg-slate-950 p-2" />
                <button disabled={busy} className="px-3 py-1 text-cyan-300">Save</button>
                <button type="button" onClick={() => setEpisodeEdit(null)} className="px-3 py-1">Cancel</button>
              </form> : <p>{memory.text}</p>}
              <div className="flex gap-3 text-xs">
                {!memory.source && <button disabled={busy} onClick={() => { setEpisodeEdit(memory.id); setEpisodeText(memory.text); }} className="text-cyan-300">Edit</button>}
                <button disabled={busy} onClick={() => { if (confirm("Delete this memory and any linked fact or project?")) mutate(() => deleteEpisode(memory.id)); }} className="text-rose-300">Delete</button>
                {memory.source && <span className="text-slate-500">Edit in the linked facts or projects tab.</span>}
              </div>
            </div>)}
          </div>}
          {/* TAB 1: USER FACTS */}
          {activeTab === "facts" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-mono text-slate-400">
                  Autonomous & explicit facts recorded about the user:
                </p>
                <button
                  onClick={() => { setEditingFact(false); setNewFactKey(""); setNewFactValue(""); setIsAddingFact(!isAddingFact); }}
                  className="px-2.5 py-1 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-900/40 text-xs font-mono flex items-center gap-1 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Record Fact</span>
                </button>
              </div>

              {isAddingFact && (
                <form onSubmit={handleCreateFact} className="p-3 rounded-xl glass-panel border-cyan-500/30 space-y-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="Fact Key (e.g. timezone, preferred_ide)"
                      value={newFactKey}
                      disabled={editingFact}
                      onChange={(e) => setNewFactKey(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:border-cyan-400 focus:outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Fact Value (e.g. UTC+5:30, Cursor)"
                      value={newFactValue}
                      onChange={(e) => setNewFactValue(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIsAddingFact(false)}
                      className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={busy}
                      className="px-3 py-1 bg-cyan-500 text-slate-950 font-bold rounded-lg text-xs font-mono hover:bg-cyan-400"
                    >
                      Save Fact
                    </button>
                  </div>
                </form>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(memoryProfile?.facts || {}).map(([key, val]) => (
                  <div
                    key={key}
                    className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/30 transition-all flex flex-col justify-between"
                  >
                    <div className="text-[11px] font-mono text-cyan-400 font-semibold uppercase tracking-wider">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="text-sm text-slate-200 mt-1">{val}</div>
                    <div className="flex gap-3 mt-2 text-xs">
                      <button disabled={busy} className="text-cyan-300" onClick={() => { setNewFactKey(key); setNewFactValue(val); setEditingFact(true); setIsAddingFact(true); }}>Edit</button>
                      <button disabled={busy} className="text-rose-300" onClick={() => { if (confirm(`Delete saved fact "${key}"?`)) mutate(() => deleteFact(key)); }}>Delete</button>
                    </div>
                  </div>
                ))}
                {Object.keys(memoryProfile?.facts || {}).length === 0 && (
                  <div className="col-span-full py-8 text-center text-xs font-mono text-slate-500">
                    No user facts registered yet. Talk with LARA to automatically build your knowledge graph.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: PROJECTS */}
          {activeTab === "projects" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-mono text-slate-400">
                  Tracked ongoing projects & action items:
                </p>
                <button
                  onClick={() => { setEditingProject(null); setNewProjectName(""); setNewProjectSummary(""); setProjectActions(""); setProjectStatus("active"); setIsAddingProject(!isAddingProject); }}
                  className="px-2.5 py-1 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-900/40 text-xs font-mono flex items-center gap-1 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Track Project</span>
                </button>
              </div>

              {isAddingProject && (
                <form onSubmit={handleCreateProject} className="p-3 rounded-xl glass-panel border-cyan-500/30 space-y-2">
                  <select aria-label="Project status" value={projectStatus} onChange={(event) => setProjectStatus(event.target.value as ProjectItem["status"])} className="bg-slate-900 border border-slate-700 rounded p-2">
                    {["active", "blocked", "paused", "completed"].map((status) => <option key={status}>{status}</option>)}
                  </select>
                  <textarea aria-label="Pending actions, one per line" placeholder="Pending actions (one per line)" value={projectActions} onChange={(event) => setProjectActions(event.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2" />
                  <input
                    type="text"
                    placeholder="Project Name (e.g. BEKKI Telephony Hub)"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:border-cyan-400 focus:outline-none"
                  />
                  <textarea
                    rows={2}
                    placeholder="Summary & status details..."
                    value={newProjectSummary}
                    onChange={(e) => setNewProjectSummary(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:border-cyan-400 focus:outline-none resize-none"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIsAddingProject(false)}
                      className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-3 py-1 bg-cyan-500 text-slate-950 font-bold rounded-lg text-xs font-mono hover:bg-cyan-400"
                    >
                      Save Project
                    </button>
                  </div>
                </form>
              )}

              <div className="space-y-2">
                {memoryProfile?.projects.map((proj) => (
                  <div
                    key={proj.id}
                    className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/30 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-white flex items-center gap-2">
                        <span>{proj.name}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950 border border-cyan-500/40 text-cyan-300 uppercase">
                          {proj.status}
                        </span>
                      </div>
                      <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(proj.last_updated).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-300">{proj.summary}</p>
                    <div className="flex gap-3 text-xs">
                      <button disabled={busy} className="text-cyan-300" onClick={() => { setEditingProject(proj.id); setNewProjectName(proj.name); setNewProjectSummary(proj.summary); setProjectStatus(proj.status); setProjectActions(proj.pending_actions.join("\n")); setIsAddingProject(true); }}>Edit</button>
                      <button disabled={busy} className="text-rose-300" onClick={() => { if (confirm(`Delete project "${proj.name}"?`)) mutate(() => deleteProject(proj.id)); }}>Delete</button>
                    </div>
                    {proj.pending_actions && proj.pending_actions.length > 0 && (
                      <div className="pt-2 border-t border-slate-800">
                        <div className="text-[11px] font-mono text-slate-400 mb-1">Pending Actions:</div>
                        <ul className="space-y-1">
                          {proj.pending_actions.map((act, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-center gap-1.5">
                              <CheckCircle2 className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                              <span>{act}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: STATS & TELEMETRY */}
          {activeTab === "stats" && (
            <div className="space-y-4 font-mono text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase">Storage Engine</div>
                  <div className="text-base font-bold text-cyan-300 mt-1 uppercase">
                    {memoryProfile?.storage_backend || "Local JSON"}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase">Vector Episodic Index</div>
                  <div className="text-base font-bold text-purple-300 mt-1">
                    {memoryProfile?.total_episodic_memories || 0} Records
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase">Session Turns Cached</div>
                  <div className="text-base font-bold text-emerald-300 mt-1">
                    {memoryProfile?.recent_session_turns || 0} Turns
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl glass-panel border-cyan-500/20 space-y-3">
                <div className="font-bold text-slate-200 flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span>Session Memory Buffer Management</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  LARA maintains a sliding short-term conversation context buffer namespaced by session ID. You can reset the active buffer without clearing long-term user facts or project history.
                </p>
                <button
                  onClick={handleClearSession}
                  className="px-3 py-1.5 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 hover:bg-rose-900/50 flex items-center gap-1.5 transition-all text-xs font-mono"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Clear Short-Term Session Buffer</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
