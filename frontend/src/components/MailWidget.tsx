"use client";

import React, { useState, useEffect } from "react";
import {
  Mail,
  Inbox,
  Send,
  Search,
  RefreshCw,
  ExternalLink,
  X,
  Plus,
  Clock,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { getMailInbox, EmailItem, MailInboxResponse } from "@/lib/api";

interface MailWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteCommand: (command: string) => void;
}

export const MailWidget: React.FC<MailWidgetProps> = ({
  isOpen,
  onClose,
  onExecuteCommand,
}) => {
  const [mailData, setMailData] = useState<MailInboxResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"inbox" | "compose" | "connect">("inbox");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Compose form state
  const [toField, setToField] = useState<string>("");
  const [subjectField, setSubjectField] = useState<string>("");
  const [bodyField, setBodyField] = useState<string>("");

  const fetchMail = async () => {
    setIsLoading(true);
    try {
      const data = await getMailInbox();
      setMailData(data);
    } catch (err) {
      console.error("Mail fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchMail();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleComposeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!toField.trim()) return;
    const cmd = `Compose email to ${toField.trim()} subject ${subjectField.trim() || "Update"} body ${bodyField.trim() || "Sent via LARA OS."}`;
    onExecuteCommand(cmd);
    setToField("");
    setSubjectField("");
    setBodyField("");
    setActiveTab("inbox");
  };

  const handleOpenWebmail = (client: string = "gmail") => {
    onExecuteCommand(`Open ${client}`);
  };

  const handleAIAnalyze = () => {
    onExecuteCommand("Analyze my mail");
    onClose();
  };

  const filteredEmails = (mailData?.inbox || []).filter((email) => {
    const q = searchQuery.toLowerCase();
    return (
      email.subject.toLowerCase().includes(q) ||
      (email.sender_name || "").toLowerCase().includes(q) ||
      email.sender.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-3xl max-h-[85vh] flex flex-col glass-panel border border-cyan-500/40 rounded-2xl p-6 shadow-[0_0_50px_rgba(0,240,255,0.25)] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-950/80 border border-purple-400/50 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono font-bold text-lg text-white tracking-wider">
                  MAIL &amp; EMAIL HUB
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-purple-950 border border-purple-400/50 text-[10px] font-mono font-bold text-purple-300">
                  {mailData?.unread_count || 0} UNREAD
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Real-time inbox intelligence, AI email analysis &amp; live Gmail integration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchMail}
              className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 hover:border-cyan-400 transition-all"
              title="Refresh inbox"
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

        {/* Tab & Action Bar */}
        <div className="flex items-center justify-between py-3 border-b border-slate-800/80 gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("inbox")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all border ${
                activeTab === "inbox"
                  ? "bg-purple-600/30 border-purple-400 text-purple-200 shadow-glow-sm"
                  : "bg-slate-900/80 border-slate-700 text-slate-300 hover:text-white"
              }`}
            >
              <Inbox className="w-3.5 h-3.5" />
              <span>INBOX ({mailData?.inbox.length || 0})</span>
            </button>

            <button
              onClick={() => setActiveTab("compose")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all border ${
                activeTab === "compose"
                  ? "bg-purple-600/30 border-purple-400 text-purple-200 shadow-glow-sm"
                  : "bg-slate-900/80 border-slate-700 text-slate-300 hover:text-white"
              }`}
            >
              <Plus className="w-3.5 h-3.5" />
              <span>COMPOSE</span>
            </button>

            <button
              onClick={() => setActiveTab("connect")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all border ${
                activeTab === "connect"
                  ? "bg-cyan-600/30 border-cyan-400 text-cyan-200 shadow-glow-sm"
                  : "bg-slate-900/80 border-slate-700 text-slate-300 hover:text-white"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span>CONNECT REAL GMAIL</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAIAnalyze}
              className="px-2.5 py-1.5 rounded-lg bg-purple-950/60 border border-purple-400/50 text-purple-300 hover:bg-purple-900/60 text-xs font-mono flex items-center gap-1 transition-all"
              title="Analyze inbox with Gemini AI"
            >
              <span>GEMINI AI ANALYZE</span>
            </button>

            <button
              onClick={() => handleOpenWebmail("gmail")}
              className="px-2.5 py-1.5 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-300 hover:bg-rose-900/60 text-xs font-mono flex items-center gap-1 transition-all"
              title="Launch Gmail in browser"
            >
              <span>GMAIL</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Tab 1: Inbox View */}
        {activeTab === "inbox" && (
          <div className="flex-1 flex flex-col min-h-[300px] mt-3">
            {/* Search filter */}
            <div className="mb-3 relative">
              <input
                type="text"
                placeholder="Search emails by sender, subject, or keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-all"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-3 pointer-events-none" />
            </div>

            {/* Email list scroll */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-2 max-h-[400px]">
              {isLoading ? (
                <div className="flex items-center justify-center h-48 gap-2 font-mono text-xs text-purple-400 animate-pulse">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Checking inbox telemetry...</span>
                </div>
              ) : filteredEmails.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 font-mono text-xs text-slate-500">
                  <Inbox className="w-8 h-8 text-slate-700 mb-2" />
                  <span>No emails match your query.</span>
                </div>
              ) : (
                filteredEmails.map((email) => (
                  <div
                    key={email.id}
                    className={`p-3.5 rounded-xl border transition-all ${
                      email.unread
                        ? "bg-slate-900/90 border-purple-500/40 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
                        : "bg-slate-950/60 border-slate-800 text-slate-400"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {email.unread && (
                          <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping flex-shrink-0" />
                        )}
                        <span className="font-mono text-xs font-bold text-slate-100">
                          {email.sender_name || email.sender}
                        </span>
                        <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                          &lt;{email.sender}&gt;
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {email.priority && (
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                              email.priority === "HIGH"
                                ? "bg-rose-950 border border-rose-500/50 text-rose-300"
                                : "bg-slate-900 text-slate-400"
                            }`}
                          >
                            {email.priority}
                          </span>
                        )}
                        <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{email.timestamp}</span>
                        </span>
                      </div>
                    </div>

                    <div className="mt-1.5 font-mono text-xs text-cyan-300 font-semibold">
                      {email.subject}
                    </div>

                    <p className="mt-1 text-xs text-slate-300 font-sans leading-relaxed">
                      {email.snippet || email.body}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Compose Draft View */}
        {activeTab === "compose" && (
          <form onSubmit={handleComposeSubmit} className="flex-1 flex flex-col space-y-3 mt-3">
            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">To Email Address:</label>
              <input
                type="email"
                required
                placeholder="recipient@example.com"
                value={toField}
                onChange={(e) => setToField(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono text-slate-100 focus:outline-none focus:border-purple-400"
              />
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">Subject:</label>
              <input
                type="text"
                placeholder="Project Directive or Subject..."
                value={subjectField}
                onChange={(e) => setSubjectField(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-mono text-slate-100 focus:outline-none focus:border-purple-400"
              />
            </div>

            <div className="flex-1 flex flex-col">
              <label className="text-[11px] font-mono text-slate-400 block mb-1">Message Body:</label>
              <textarea
                rows={5}
                placeholder="Compose your message content..."
                value={bodyField}
                onChange={(e) => setBodyField(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700 text-xs font-sans text-slate-100 focus:outline-none focus:border-purple-400 resize-none flex-1"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveTab("inbox")}
                className="px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-white"
              >
                CANCEL
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-mono font-bold text-xs flex items-center gap-1.5 shadow-[0_0_15px_rgba(168,85,247,0.4)]"
              >
                <span>RECORD DRAFT</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        )}

        {/* Tab 3: Connect Real Gmail Guide View */}
        {activeTab === "connect" && (
          <div className="flex-1 flex flex-col space-y-4 mt-3 overflow-y-auto max-h-[420px] pr-1">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/40 shadow-[0_0_20px_rgba(0,240,255,0.15)]">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="font-mono font-bold text-sm text-white">
                  CONNECT YOUR REAL GMAIL INBOX (30 SECONDS)
                </h3>
              </div>
              <p className="text-xs font-sans text-slate-300 leading-relaxed mb-3">
                LARA connects directly to your Google account using an encrypted SSL IMAP bridge. Your normal Google password is never used; instead, Google generates a secure 16-letter App Password specifically for LARA.
              </p>

              <div className="space-y-3 text-xs font-mono text-slate-200">
                <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-[11px] flex-shrink-0">
                    1
                  </span>
                  <div>
                    <span className="text-slate-100 font-bold">Open Google App Passwords:</span>
                    <p className="text-slate-400 mt-0.5 text-[11px]">
                      Visit <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-cyan-400 underline hover:text-cyan-300">myaccount.google.com/apppasswords</a> (make sure 2-Step Verification is on).
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-[11px] flex-shrink-0">
                    2
                  </span>
                  <div>
                    <span className="text-slate-100 font-bold">Generate Password for LARA:</span>
                    <p className="text-slate-400 mt-0.5 text-[11px]">
                      Type app name <strong>&quot;LARA OS&quot;</strong> and copy the 16-letter password shown (e.g. <code>abcd efgh ijkl mnop</code>).
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-[11px] flex-shrink-0">
                    3
                  </span>
                  <div>
                    <span className="text-slate-100 font-bold">Add to backend/.env:</span>
                    <p className="text-slate-400 mt-0.5 text-[11px]">
                      Add these two lines to <code>d:\LARA\backend\.env</code>:
                    </p>
                    <div className="mt-1.5 p-2 rounded bg-slate-900 border border-slate-700 text-cyan-300 text-[11px]">
                      GMAIL_USER=your_email@gmail.com<br />
                      GMAIL_APP_PASSWORD=your_16_letter_password
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800">
                <a
                  href="https://myaccount.google.com/apppasswords"
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs flex items-center gap-1.5 shadow-glow-sm transition-all"
                >
                  <span>OPEN GOOGLE APP PASSWORDS</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <button
                  type="button"
                  onClick={fetchMail}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 transition-all flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>TEST LIVE CONNECTION</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] font-mono text-slate-500">
            Tip: Say <em>&quot;Hey LARA, check my mail&quot;</em> or <em>&quot;Analyze my emails with Gemini&quot;</em>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-mono font-bold text-xs shadow-glow-sm transition-all"
          >
            DISMISS
          </button>
        </div>
      </div>
    </div>
  );
};
