"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Trash2, Sparkles, AlertCircle, Mic, MicOff, Volume2, Radio, ShieldAlert } from "lucide-react";
import { MessageBubble, Message } from "./MessageBubble";
import { AudioOrb } from "./AudioOrb";
import { VoiceState } from "@/hooks/useVoiceAssistant";

interface ChatInterfaceProps {
  briefingMode: boolean;
  voiceState: VoiceState;
  interimTranscript: string;
  isWakeWordActive: boolean;
  micPermission: "prompt" | "granted" | "denied";
  onRequestMicAccess: () => void;
  onToggleWakeWord: () => void;
  onStartManualListening: () => void;
  onStopManualListening: () => void;
  messages: Message[];
  isLoading: boolean;
  errorMessage: string | null;
  onSendMessage: (text: string, speakResponse?: boolean) => Promise<void>;
  onClearHistory: () => void;
}

const STARTER_PROMPTS = [
  "Run system diagnostic and report status",
  "Provide an architectural briefing of LARA",
  "What is your identity and core persona?",
  "Test end-to-end latency and round trip",
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  briefingMode,
  voiceState,
  interimTranscript,
  isWakeWordActive,
  micPermission,
  onRequestMicAccess,
  onToggleWakeWord,
  onStartManualListening,
  onStopManualListening,
  messages,
  isLoading,
  errorMessage,
  onSendMessage,
  onClearHistory,
}) => {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, interimTranscript]);

  const handleSend = useCallback(
    async (textOverride?: string, speakResponse: boolean = false) => {
      const textToSend = textOverride !== undefined ? textOverride : input;
      if (!textToSend.trim() || isLoading) return;

      setInput("");
      await onSendMessage(textToSend, speakResponse);
      setTimeout(() => textareaRef.current?.focus(), 100);
    },
    [input, isLoading, onSendMessage]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(undefined, false);
    }
  };

  return (
    <div className="flex flex-col max-w-5xl mx-auto w-full px-2 py-2 mb-4">
      <div className="flex flex-col rounded-3xl p-4 glass-locker-card border border-cyan-500/30 shadow-[0_0_40px_rgba(0,240,255,0.15)] min-h-[420px] max-h-[560px]">
        {/* Top Chat Deck Header */}
        <div className="flex items-center justify-between pb-3 mb-2 border-b border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_rgba(0,240,255,0.8)]" />
            <div>
              <div className="text-xs font-mono text-cyan-300 font-bold tracking-wider flex items-center gap-2">
                <span>LARA NEURAL CONSOLE // LIVE FEED</span>
              </div>
              <div className="text-[10px] font-mono text-slate-500 flex items-center gap-2">
                <span>{briefingMode ? "Mode: Briefing" : "Mode: Adaptive"}</span>
                <span>•</span>
                <span className="text-emerald-400">Jenny Neural 0-Echo Audio</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onToggleWakeWord}
              className={`p-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border transition-all ${
                isWakeWordActive
                  ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-glow-sm"
                  : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
              }`}
              title="Toggle continuous wake-word listening"
            >
              {isWakeWordActive ? <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" /> : <MicOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">
                {isWakeWordActive ? "WAKE-WORD ON" : "ENABLE WAKE-WORD"}
              </span>
            </button>

            <button
              onClick={onClearHistory}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 border border-transparent hover:border-rose-500/30 transition-all text-xs flex items-center gap-1 font-mono"
              title="Clear console buffer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">CLEAR</span>
            </button>
          </div>
        </div>

        {/* Microphone Permission Prompt Banner */}
        {micPermission !== "granted" && (
          <div className="mb-2 p-2.5 rounded-xl bg-gradient-to-r from-cyan-950/80 via-slate-900/90 to-cyan-950/80 border border-cyan-400/60 flex items-center justify-between gap-3 shadow-[0_0_20px_rgba(0,240,255,0.25)]">
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-200">
              <Mic className="w-4 h-4 text-cyan-400 animate-pulse flex-shrink-0" />
              <span>
                <strong>Microphone access needed:</strong> Click &quot;ALLOW MICROPHONE&quot; to enable hands-free voice &amp; &quot;Hey LARA&quot; activation.
              </span>
            </div>
            <button
              onClick={onRequestMicAccess}
              className="px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs rounded-lg shadow-[0_0_12px_rgba(0,240,255,0.5)] transition-all cursor-pointer flex-shrink-0"
            >
              ALLOW MICROPHONE
            </button>
          </div>
        )}

        {/* Messages Scroll View */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-1">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Live speech transcription stream */}
          {voiceState === "listening" && (
            <div className="flex items-center gap-3 my-3 p-3 rounded-lg glass-panel-glow border-emerald-400/50 bg-emerald-950/30">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <div className="text-xs font-mono text-emerald-300">
                <span className="font-bold uppercase tracking-wide">Listening: </span>
                <span className="text-slate-100 italic">
                  {interimTranscript || "Speak your command (e.g. 'Hey LARA open notepad')..."}
                </span>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex items-center gap-3 my-4 p-3 rounded-lg glass-panel max-w-sm border-cyan-500/30">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono text-cyan-300">
                LARA is synthesizing response...
              </span>
            </div>
          )}

          {errorMessage && (
            <div className="my-4 p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Starter Prompts */}
        {messages.length <= 2 && (
          <div className="py-2">
            <div className="text-[11px] font-mono text-slate-400 mb-1.5 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>Suggested Directives (Voice or Click):</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {STARTER_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt, false)}
                  className="text-left text-xs font-mono p-2.5 rounded-lg glass-panel hover:border-cyan-400/50 hover:bg-cyan-950/30 transition-all text-slate-300 hover:text-white"
                >
                  &gt; {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Form Bar */}
        <div className="mt-2 pt-2 border-t border-cyan-500/20">
          <div className="relative glass-panel rounded-xl p-2 focus-within:border-cyan-400/70 focus-within:shadow-glow-sm transition-all">
            <textarea
              ref={textareaRef}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isWakeWordActive
                  ? "Say 'Hey LARA' or type a command... (Enter to transmit)"
                  : "Command LARA... (Press Enter to execute, or click Mic for voice)"
              }
              className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none resize-none px-2 py-1 font-sans"
              disabled={isLoading}
            />

            <div className="flex items-center justify-between pt-1 px-2 border-t border-slate-800 text-[11px] font-mono text-slate-400">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500 hidden sm:inline">
                  Wake-word: &quot;Hey LARA&quot; • Web Speech STT/TTS
                </span>
              </div>

              <div className="flex items-center gap-2">
                {/* Push-to-Talk Mic Button */}
                <button
                  type="button"
                  onMouseDown={() => {
                    onRequestMicAccess();
                    onStartManualListening();
                  }}
                  onMouseUp={onStopManualListening}
                  onTouchStart={() => {
                    onRequestMicAccess();
                    onStartManualListening();
                  }}
                  onTouchEnd={onStopManualListening}
                  className={`p-1.5 rounded-md text-xs font-mono flex items-center gap-1 transition-all ${
                    voiceState === "listening"
                      ? "bg-emerald-500 text-black font-bold animate-pulse shadow-[0_0_12px_rgba(52,211,153,0.6)]"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white"
                  }`}
                  title="Hold to talk (Push-to-Talk)"
                >
                  <Mic className="w-3.5 h-3.5" />
                  <span className="text-[10px] hidden sm:inline">
                    {voiceState === "listening" ? "RECORDING..." : "HOLD MIC"}
                  </span>
                </button>

                {/* Transmit Button */}
                <button
                  onClick={() => handleSend(undefined, false)}
                  disabled={!input.trim() || isLoading}
                  className={`px-3 py-1 rounded-md text-xs font-mono flex items-center gap-1.5 transition-all ${
                    input.trim() && !isLoading
                      ? "bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 shadow-glow-sm cursor-pointer"
                      : "bg-slate-800 text-slate-500 cursor-not-allowed"
                  }`}
                >
                  <span>TRANSMIT</span>
                  <Send className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
