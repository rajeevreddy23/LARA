"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { StatusHeader } from "@/components/StatusHeader";
import { ChatInterface } from "@/components/ChatInterface";
import { MemoryInspector } from "@/components/MemoryInspector";
import { ProactiveAlertBanner } from "@/components/ProactiveAlertBanner";
import { RiskConfirmationModal } from "@/components/RiskConfirmationModal";
import { SystemControlWidget } from "@/components/SystemControlWidget";
import { DeviceBridgeModal } from "@/components/DeviceBridgeModal";
import { FileExplorerWidget } from "@/components/FileExplorerWidget";
import { MailWidget } from "@/components/MailWidget";
import { AppsExplorerWidget } from "@/components/AppsExplorerWidget";
import { HolographicGlobeVisualizer } from "@/components/HolographicGlobeVisualizer";
import { AppViewerStage, ActiveAppItem } from "@/components/AppViewerStage";
import { Message } from "@/components/MessageBubble";
import { TaskActivity } from "@/components/TaskActivity";
import {
  checkBackendHealth,
  sendChatMessage,
  streamChatMessage,
  getAgentTasks,
  AgentTask,
  getMemoryProfile,
  getExecutiveBriefing,
  getProactiveFollowups,
  getMailInbox,
  getInstalledApps,
  confirmPendingAction,
  HealthResponse,
  MemoryProfileResponse,
  ProactiveNotificationItem,
  PendingActionItem,
} from "@/lib/api";
import { useVoiceAssistant } from "@/hooks/useVoiceAssistant";

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [briefingMode, setBriefingMode] = useState<boolean>(false);
  const [lastLatency, setLastLatency] = useState<number | null>(null);
  const [memoryProfile, setMemoryProfile] = useState<MemoryProfileResponse | null>(null);
  const [isMemoryOpen, setIsMemoryOpen] = useState<boolean>(false);
  const [isDeviceBridgeOpen, setIsDeviceBridgeOpen] = useState<boolean>(false);
  const [isFilesOpen, setIsFilesOpen] = useState<boolean>(false);
  const [isMailOpen, setIsMailOpen] = useState<boolean>(false);
  const [isAppsOpen, setIsAppsOpen] = useState<boolean>(false);
  const [mailUnreadCount, setMailUnreadCount] = useState<number>(0);
  const [appsCount, setAppsCount] = useState<number>(0);
  const [proactiveNotification, setProactiveNotification] = useState<ProactiveNotificationItem | null>(null);
  const [activePendingAction, setActivePendingAction] = useState<PendingActionItem | null>(null);
  const [activeApp, setActiveApp] = useState<ActiveAppItem | null>(null);
  const [agentTasks, setAgentTasks] = useState<AgentTask[]>([]);
  const [agentStatus, setAgentStatus] = useState("");
  const commandBusyRef = useRef(false);
  const [approvalBusy, setApprovalBusy] = useState(false);

  const recordTask = useCallback((task: AgentTask) => {
    setAgentTasks((prev) => [task, ...prev.filter((item) => item.id !== task.id)].slice(0, 20));
  }, []);

  const fetchTasks = useCallback(async () => {
    try {
      const tasks = await getAgentTasks();
      setAgentTasks(tasks);
      const pending = tasks.flatMap((task) => task.status === "pending_approval" ? task.steps : [])
        .find((step) => step.status === "pending_approval")?.pending_action;
      setActivePendingAction(pending || null);
    } catch { /* The health indicator reports backend connectivity. */ }
  }, []);

  // Chat conversation state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init-1",
      role: "assistant",
      content:
        "LARA OS online. Wake-word detection ready. Say \"Hey LARA\" or type your command, Bunty.",
      timestamp: "ONLINE",
      model: "system-core",
    },
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await checkBackendHealth();
      setHealth(data);
      setIsConnected(true);
    } catch {
      setIsConnected(false);
    }
  }, []);

  const fetchMemory = useCallback(async () => {
    try {
      const memData = await getMemoryProfile();
      setMemoryProfile(memData);
    } catch (err) {
      console.debug("Memory fetch deferred:", err);
    }
  }, []);

  const fetchMailData = useCallback(async () => {
    try {
      const mailRes = await getMailInbox();
      setMailUnreadCount(mailRes.unread_count || 0);
    } catch (err) {
      console.debug("Mail count fetch deferred:", err);
    }
  }, []);

  const fetchAppsData = useCallback(async () => {
    try {
      const appsRes = await getInstalledApps();
      setAppsCount(appsRes.total || 0);
    } catch (err) {
      console.debug("Apps fetch deferred:", err);
    }
  }, []);

  const fetchFollowups = useCallback(async () => {
    try {
      const followups = await getProactiveFollowups();
      if (followups && followups.length > 0) {
        setProactiveNotification(followups[0]);
      }
    } catch (err) {
      console.debug("Followups check deferred:", err);
    }
  }, []);

  const voiceAssistantRef = useRef<any>(null);

  // Unified command executor for Text, Voice ("Hey LARA"), and Quick Controls
  const handleExecuteCommand = useCallback(
    async (commandText: string, speakResponse: boolean = true) => {
      const text = commandText.trim();
      if (!text || commandBusyRef.current) return;
      commandBusyRef.current = true;

      const lower = text.toLowerCase();
      const isExplicitOpen = lower.startsWith("open ") || lower.startsWith("launch ") || lower.startsWith("start ");

      if (isExplicitOpen) {
        if (lower.includes("ai studio") || lower.includes("google ai")) {
          setActiveApp({
            id: "aistudio",
            name: "Google AI Studio",
            category: "Development",
            iconType: "brain",
            webUrl: "https://aistudio.google.com",
            status: "active",
            details: "Google AI Studio Web Workspace & Gemini Playground",
          });
        } else if (lower.includes("whatsapp")) {
          setActiveApp({
            id: "whatsapp",
            name: "WhatsApp",
            category: "Communication",
            iconType: "whatsapp",
            webUrl: "https://web.whatsapp.com",
            status: "active",
            details: "WhatsApp Messaging Gateway & Web Client",
          });
        } else if (lower.includes("youtube")) {
          setActiveApp({
            id: "youtube",
            name: "YouTube",
            category: "Media",
            iconType: "youtube",
            webUrl: "https://youtube.com",
            status: "active",
            details: "Video & Media Streaming Engine",
          });
        } else if (lower.includes("chrome") || lower.includes("google")) {
          setActiveApp({
            id: "chrome",
            name: "Google Chrome",
            category: "Internet",
            iconType: "chrome",
            webUrl: "https://google.com",
            status: "active",
            details: "Web Navigation & Search Hub",
          });
        } else if (lower.includes("vs code") || lower.includes("vscode") || lower.includes("code")) {
          setActiveApp({
            id: "vscode",
            name: "VS Code",
            category: "Development",
            iconType: "vscode",
            status: "active",
            details: "Visual Studio Code IDE Host Process",
          });
        } else if (lower.includes("claude code")) {
          setActiveApp({
            id: "claude_code",
            name: "Claude Code",
            category: "CLI Agent",
            iconType: "terminal",
            status: "active",
            details: "Anthropic Claude Code Agentic Terminal Session",
          });
        } else if (lower.includes("claude")) {
          setActiveApp({
            id: "claude",
            name: "Claude AI",
            category: "AI Assistant",
            iconType: "brain",
            webUrl: "https://claude.ai",
            status: "active",
            details: "Anthropic Claude AI Assistant & Workspace",
          });
        } else if (lower.includes("excel")) {
          setActiveApp({
            id: "excel",
            name: "Microsoft Excel",
            category: "Productivity",
            iconType: "excel",
            status: "active",
            details: "Office Spreadsheet & Calculation Engine",
          });
        }
      }

      setErrorMessage(null);

      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: now,
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      const replyId = `lara-stream-${Date.now()}`;
      let streamedText = "";

      try {
        const response = await streamChatMessage({
          message: text,
          user_name: "Bunty",
          briefing_mode: briefingMode,
          speak_response: speakResponse,
        }, (event) => {
          if (event.event === "status") setAgentStatus(event.text || "");
          if (event.task) recordTask(event.task);
          if (event.event === "step_retry") setAgentStatus("Retrying a read-only step…");
          if (event.event === "token") {
            streamedText += event.text || "";
            const content = streamedText;
            setMessages((prev) => prev.some((m) => m.id === replyId)
              ? prev.map((m) => m.id === replyId ? { ...m, content } : m)
              : [...prev, { id: replyId, role: "assistant", content, timestamp: "LIVE" }]);
          }
        });

        setLastLatency(response.latency_ms);

        // Run background telemetry non-blocking
        setTimeout(() => {
          fetchMemory();
          fetchFollowups();
          fetchMailData();
        }, 100);

        const assistantMsg: Message = {
          id: replyId,
          role: "assistant",
          content: response.response,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          model: response.model,
          status: response.status,
          latency_ms: response.latency_ms,
          tool_execution: response.tool_execution,
        };

        setMessages((prev) => [...prev.filter((m) => m.id !== replyId), assistantMsg]);

        if (response.status === "pending_confirmation" && response.pending_action) {
          setActivePendingAction(response.pending_action);
        } else {
          setActivePendingAction(null);
        }

        if (speakResponse) {
          if (response.audio_base64 && voiceAssistantRef.current?.playNeuralAudio) {
            voiceAssistantRef.current.playNeuralAudio(response.audio_base64, response.response);
          } else if (voiceAssistantRef.current?.speakText) {
            voiceAssistantRef.current.speakText(response.response);
          }
        }
      } catch (err: any) {
        console.error("Command processing error:", err);
        setErrorMessage(
          err.message || "Failed to communicate with LARA orchestrator. Ensure backend is running."
        );
      } finally {
        commandBusyRef.current = false;
        setAgentStatus("");
        setIsLoading(false);
      }
    },
    [briefingMode, fetchMemory, fetchFollowups, fetchMailData, recordTask]
  );

  const voiceAssistant = useVoiceAssistant({
    onCommandReceived: (cmd) => handleExecuteCommand(cmd, true),
    enabled: true,
  });
  voiceAssistantRef.current = voiceAssistant;

  const handleClearHistory = () => {
    setMessages([
      {
        id: `init-${Date.now()}`,
        role: "assistant",
        content: "Terminal buffer reset. LARA standing by.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        model: "system-core",
      },
    ]);
  };

  const handleTriggerBriefing = async () => {
    try {
      handleExecuteCommand("Deliver executive daily briefing now.", true);
    } catch (err) {
      console.error("Failed to generate briefing:", err);
    }
  };

  const handleConfirmAction = async () => {
    if (!activePendingAction || approvalBusy) return;
    setApprovalBusy(true);
    try {
      const result = await confirmPendingAction(activePendingAction.ticket_id, true);
      setActivePendingAction(result.chat_response?.pending_action || null);
      if (result.chat_response?.task) recordTask(result.chat_response.task);
      setMessages((prev) => [...prev, {
        id: `approval-${Date.now()}`,
        role: "assistant",
        content: typeof result.output === "string" ? result.output : JSON.stringify(result.output),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: result.chat_response?.status || (result.success ? "success" : "error"),
        model: `lara-guardrail:${result.skill_name}`,
      }]);
      fetchMemory();
    } catch (err) {
      console.error("Action confirmation error:", err);
      setErrorMessage(err instanceof Error ? err.message : "Action approval failed.");
    } finally {
      setApprovalBusy(false);
    }
  };

  const handleRejectAction = async () => {
    if (!activePendingAction || approvalBusy) return;
    setApprovalBusy(true);
    try {
      const result = await confirmPendingAction(activePendingAction.ticket_id, false);
      if (result.chat_response?.task) recordTask(result.chat_response.task);
      setActivePendingAction(null);
      setMessages((prev) => [...prev, {
        id: `rejection-${Date.now()}`,
        role: "assistant",
        content: "Action rejected. It was not executed.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        model: "lara-guardrail:abort",
      }]);
    } catch (err) {
      console.error("Action rejection error:", err);
      setErrorMessage(err instanceof Error ? err.message : "Action rejection failed.");
    } finally {
      setApprovalBusy(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchMemory();
    fetchMailData();
    fetchAppsData();
    fetchFollowups();
    fetchTasks();
    const interval = setInterval(() => {
      fetchHealth();
      fetchMemory();
      fetchMailData();
      fetchAppsData();
      fetchFollowups();
    }, 15000);
    return () => clearInterval(interval);
  }, [fetchHealth, fetchMemory, fetchMailData, fetchAppsData, fetchFollowups, fetchTasks]);

  const totalIntelCount =
    Object.keys(memoryProfile?.facts || {}).length + (memoryProfile?.projects.length || 0);

  return (
    <main className="min-h-screen flex flex-col justify-between">
      <StatusHeader
        health={health}
        isConnected={isConnected}
        briefingMode={briefingMode}
        onToggleBriefing={() => setBriefingMode((prev) => !prev)}
        latency={lastLatency}
        isWakeWordActive={voiceAssistant.isWakeWordActive}
        voiceState={voiceAssistant.voiceState}
        onToggleWakeWord={voiceAssistant.toggleWakeWord}
        onOpenMemory={() => setIsMemoryOpen(true)}
        onTriggerBriefing={handleTriggerBriefing}
        memoryItemCount={totalIntelCount}
        onOpenDeviceBridge={() => setIsDeviceBridgeOpen(true)}
        onOpenFiles={() => setIsFilesOpen(true)}
        onOpenMail={() => setIsMailOpen(true)}
        mailUnreadCount={mailUnreadCount}
        onOpenApps={() => setIsAppsOpen(true)}
        appsCount={appsCount}
      />

      {/* Proactive Intelligence Banner */}
      <ProactiveAlertBanner
        notification={proactiveNotification}
        onDismiss={() => setProactiveNotification(null)}
        onAction={(text) => handleExecuteCommand(text, true)}
      />

      {/* 3D Holographic Rotating Wireframe Globe & Neural Network Centerpiece */}
      <HolographicGlobeVisualizer
        voiceState={voiceAssistant.voiceState}
        interimTranscript={voiceAssistant.interimTranscript}
        isWakeWordActive={voiceAssistant.isWakeWordActive}
        onExecuteCommand={(cmd) => handleExecuteCommand(cmd, true)}
        onStartManualListening={voiceAssistant.startManualListening}
        onStopManualListening={voiceAssistant.stopManualListening}
      />

      {/* In-Page Interactive App Viewer Stage */}
      <AppViewerStage
        activeApp={activeApp}
        onClose={() => setActiveApp(null)}
        onExecuteCommand={(cmd) => handleExecuteCommand(cmd, true)}
      />

      <div className="flex-1 flex flex-col justify-center">
        <TaskActivity tasks={agentTasks} status={agentStatus} />
        <ChatInterface
          briefingMode={briefingMode}
          voiceState={voiceAssistant.voiceState}
          interimTranscript={voiceAssistant.interimTranscript}
          isWakeWordActive={voiceAssistant.isWakeWordActive}
          micPermission={voiceAssistant.micPermission}
          onRequestMicAccess={voiceAssistant.requestMicAccess}
          onToggleWakeWord={voiceAssistant.toggleWakeWord}
          onStartManualListening={voiceAssistant.startManualListening}
          onStopManualListening={voiceAssistant.stopManualListening}
          messages={messages}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSendMessage={(text, speak) => handleExecuteCommand(text, speak ?? false)}
          onClearHistory={handleClearHistory}
        />
      </div>

      <MemoryInspector
        isOpen={isMemoryOpen}
        onClose={() => setIsMemoryOpen(false)}
        memoryProfile={memoryProfile}
        onRefresh={fetchMemory}
      />

      {/* Mobile Device Bridge & QR Pairing Modal */}
      <DeviceBridgeModal
        isOpen={isDeviceBridgeOpen}
        onClose={() => setIsDeviceBridgeOpen(false)}
      />

      {/* System File & Folder Hub Drawer/Modal */}
      <FileExplorerWidget
        isOpen={isFilesOpen}
        onClose={() => setIsFilesOpen(false)}
        onExecuteCommand={(cmd) => handleExecuteCommand(cmd, true)}
      />

      {/* Mail & Email Hub Drawer/Modal */}
      <MailWidget
        isOpen={isMailOpen}
        onClose={() => setIsMailOpen(false)}
        onExecuteCommand={(cmd) => handleExecuteCommand(cmd, true)}
      />

      {/* System Applications Hub Drawer/Modal */}
      <AppsExplorerWidget
        isOpen={isAppsOpen}
        onClose={() => setIsAppsOpen(false)}
        onExecuteCommand={(cmd) => handleExecuteCommand(cmd, true)}
      />

      {/* Security Risk Guardian Modal */}
      <RiskConfirmationModal
        busy={approvalBusy}
        pendingAction={activePendingAction}
        onConfirm={handleConfirmAction}
        onReject={handleRejectAction}
      />
    </main>
  );
}
