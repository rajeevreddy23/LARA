"use client";

import React, { useState } from "react";
import { Copy, Check, Bot, User, Sparkles, AlertCircle, Terminal, Calendar, Globe, Cpu } from "lucide-react";
import { ToolExecutionItem } from "@/lib/api";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  model?: string;
  status?: "success" | "fallback" | "pending_confirmation" | "error";
  latency_ms?: number;
  tool_execution?: ToolExecutionItem;
}

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isAssistant = message.role === "assistant";
  const isSystem = message.role === "system";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/40 border border-cyan-500/20 text-cyan-400/80 flex items-center gap-1.5">
          <Sparkles className="w-3 h-3" />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case "run_code":
        return <Terminal className="w-3 h-3 text-emerald-400" />;
      case "calendar_reminders":
        return <Calendar className="w-3 h-3 text-cyan-400" />;
      case "web_search":
        return <Globe className="w-3 h-3 text-indigo-400" />;
      default:
        return <Cpu className="w-3 h-3 text-cyan-400" />;
    }
  };

  return (
    <div
      className={`flex w-full my-3 ${
        isAssistant ? "justify-start" : "justify-end"
      }`}
    >
      <div
        className={`flex gap-3 max-w-[92%] sm:max-w-[80%] ${
          isAssistant ? "flex-row" : "flex-row-reverse"
        }`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border font-mono text-xs ${
            isAssistant
              ? "bg-cyan-950/80 border-cyan-400/40 text-cyan-300 shadow-glow-sm"
              : "bg-slate-800 border-slate-600 text-slate-200"
          }`}
        >
          {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
        </div>

        {/* Message Card */}
        <div
          className={`relative rounded-xl p-4 transition-all duration-200 ${
            isAssistant
              ? "glass-panel-glow text-slate-100 border-cyan-500/30"
              : "bg-cyan-950/30 border border-cyan-500/20 text-slate-200"
          }`}
        >
          {/* Header Metadata */}
          <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-slate-700/40 text-[11px] font-mono text-slate-400">
            <span className="font-semibold text-cyan-400/90">
              {isAssistant ? "LARA" : "YOU"}
            </span>

            <div className="flex items-center gap-2">
              {message.model && (
                <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-[10px] text-slate-300">
                  {message.model}
                </span>
              )}
              {message.latency_ms && (
                <span className="text-[10px] text-cyan-400/70">
                  {message.latency_ms}ms
                </span>
              )}
              <span suppressHydrationWarning>{message.timestamp}</span>
              <button
                onClick={handleCopy}
                className="hover:text-cyan-300 p-0.5 transition-colors"
                title="Copy message"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>

          {/* Tool Execution Badge if triggered */}
          {message.tool_execution && (
            <div className="mb-2 p-2 rounded-lg bg-slate-900/80 border border-cyan-500/30 flex items-center justify-between gap-2 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-slate-200">
                {getToolIcon(message.tool_execution.tool_name)}
                <span className="font-bold uppercase text-cyan-300">
                  TOOL: {message.tool_execution.tool_name}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px]">
                {message.tool_execution.mutated_state && (
                  <span className="px-1.5 py-0.2 rounded bg-amber-950/80 border border-amber-500/40 text-amber-300">
                    STATE MUTATED
                  </span>
                )}
                <span className="text-slate-400">
                  {message.tool_execution.latency_ms}ms
                </span>
              </div>
            </div>
          )}

          {/* Content Body */}
          <div className="text-sm font-sans whitespace-pre-wrap leading-relaxed space-y-2">
            {message.content.split(/(\[[^\]]+\]\(https?:\/\/[^\)]+\))/g).map((part, idx) => {
              const linkMatch = /^\[([^\]]+)\]\((https?:\/\/[^\)]+)\)$/.exec(part);
              if (linkMatch) {
                return (
                  <a
                    key={idx}
                    href={linkMatch[2]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-400 underline hover:text-cyan-300 inline-flex items-center gap-1 font-mono text-xs font-semibold"
                  >
                    <span>{linkMatch[1]}</span>
                    <Globe className="w-3 h-3 inline" />
                  </a>
                );
              }
              return part;
            })}
          </div>

          {/* Fallback mode indicator warning if active */}
          {message.status === "fallback" && !message.tool_execution && (
            <div className="mt-2 pt-1.5 border-t border-slate-700/30 flex items-center gap-1.5 text-[11px] font-mono text-amber-400/80">
              <AlertCircle className="w-3 h-3" />
              <span>Phase 1-2 Local Fallback (Set GEMINI_API_KEY for live reasoning)</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
