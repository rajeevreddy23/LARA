/**
 * API client library for communicating with LARA backend orchestrator (Phases 0-5).
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface RecalledMemoryItem {
  text: string;
  relevance_score: number;
  timestamp: string;
}

export interface ToolExecutionItem {
  tool_name: string;
  output: any;
  success: boolean;
  latency_ms: number;
  mutated_state?: boolean;
}

export interface PendingActionItem {
  ticket_id: string;
  tool_name: string;
  params: Record<string, any>;
  risk_level: string;
  rationale: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  user_id: string;
  tool_name: string;
  parameters: Record<string, any>;
  risk_level: string;
  status: string;
  rationale: string;
  confirmed_by?: string;
  execution_latency_ms: number;
}

export interface ChatRequest {
  message: string;
  user_name?: string;
  user_id?: string;
  session_id?: string;
  conversation_history?: { role: string; content: string }[];
  briefing_mode?: boolean;
  speak_response?: boolean;
}

export interface ChatResponse {
  response: string;
  model: string;
  status: "success" | "fallback" | "pending_confirmation" | "error";
  latency_ms: number;
  tool_execution?: ToolExecutionItem;
  pending_action?: PendingActionItem;
  recalled_memories?: RecalledMemoryItem[];
  extracted_facts?: string[];
  audio_base64?: string;
  task?: AgentTask;
  timestamp: string;
}

export interface AgentTask {
  id: string;
  user_id: string;
  session_id: string;
  prompt: string;
  status: string;
  created_at: string;
  steps: { tool_name: string; status: string; attempts: number; pending_action?: PendingActionItem | null }[];
}

export interface AgentEvent {
  event: string;
  text?: string;
  task?: AgentTask;
  response?: ChatResponse;
}

export interface EpisodicMemory {
  id: string;
  text: string;
  source?: string;
  created_at: string;
  embedding_version?: string;
}

export async function streamChatMessage(payload: ChatRequest, onEvent: (event: AgentEvent) => void): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) throw new Error(`Chat request failed [${response.status}]`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed: ChatResponse | undefined;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const data = frame.split("\n").filter((line) => line.startsWith("data: ")).map((line) => line.slice(6)).join("\n");
        if (!data) continue;
        const event: AgentEvent = JSON.parse(data);
        if (event.event === "error") throw new Error(event.text || "Chat stream failed.");
        onEvent(event);
        if (event.event === "done") completed = event.response;
      }
      if (done) break;
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
  if (!completed) throw new Error("Connection ended before the task completed. Check task activity before retrying.");
  return completed;
}

export async function getAgentTasks(): Promise<AgentTask[]> {
  return memoryRequest("/api/tasks");
}

async function memoryRequest(path: string, method = "GET", body?: unknown) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method, headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }), cache: "no-store",
  });
  if (!response.ok) throw new Error(`Request failed [${response.status}]: ${await response.text()}`);
  return response.json();
}

export const deleteFact = (key: string) => memoryRequest(`/api/memory/fact/${encodeURIComponent(key)}`, "DELETE");
export const deleteProject = (id: string) => memoryRequest(`/api/memory/project/${encodeURIComponent(id)}`, "DELETE");
export const updateProject = (id: string, project: Pick<ProjectItem, "name" | "summary" | "status" | "pending_actions">) =>
  memoryRequest(`/api/memory/project/${encodeURIComponent(id)}`, "PUT", project);
export const getEpisodes = (): Promise<EpisodicMemory[]> => memoryRequest("/api/memory/episodes");
export const deleteEpisode = (id: string) => memoryRequest(`/api/memory/episodes/${encodeURIComponent(id)}`, "DELETE");
export const editEpisode = (id: string, text: string) => memoryRequest(`/api/memory/episodes/${encodeURIComponent(id)}`, "PUT", { text });

export interface ProjectItem {
  id: string;
  name: string;
  status: "active" | "blocked" | "completed" | "paused";
  summary: string;
  pending_actions: string[];
  last_updated: string;
}

export interface MemoryProfileResponse {
  user_id: string;
  user_name: string;
  facts: Record<string, string>;
  projects: ProjectItem[];
  recent_session_turns: number;
  total_episodic_memories: number;
  storage_backend: string;
}

export interface ProactiveNotificationItem {
  id: string;
  type: "project_followup" | "reminder_alert" | "briefing";
  title: string;
  message: string;
  priority?: string;
  timestamp: string;
}

export interface ExecutiveBriefingResponse {
  title: string;
  briefing: string;
  project_count: number;
  pending_reminder_count: number;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  name: string;
  version: string;
  phase: string;
  model_configured: boolean;
  active_model: string;
  active_skills?: string[];
  memory_backend?: string;
  guardrails_active?: boolean;
  timestamp: string;
}

/**
 * Health check query.
 */
export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Health check failed with HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Send chat message to LARA.
 */
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Chat request failed [${response.status}]: ${errorText}`);
  }

  return response.json();
}

/**
 * Confirm or reject a pending tool action ticket.
 */
export async function confirmPendingAction(ticketId: string, confirmed: boolean = true, userId: string = "default_user") {
  const response = await fetch(`${API_BASE_URL}/api/guardrails/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticket_id: ticketId, confirmed, user_id: userId }),
  });
  if (!response.ok) {
    throw new Error(`Approval request failed [${response.status}]`);
  }
  return response.json();
}

/**
 * Retrieve audit log entries.
 */
export async function getAuditLogs(limit: number = 50, userId: string = "default_user"): Promise<AuditLogItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/guardrails/audit-logs?limit=${limit}&user_id=${encodeURIComponent(userId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) return [];
  return response.json();
}

/**
 * Retrieve user memory profile.
 */
export async function getMemoryProfile(
  userId: string = "default_user",
  sessionId: string = "default_session"
): Promise<MemoryProfileResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/memory/profile?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch memory profile [${response.status}]`);
  }

  return response.json();
}

/**
 * Explicitly record user fact.
 */
export async function addUserFact(key: string, value: string, userId: string = "default_user") {
  const response = await fetch(`${API_BASE_URL}/api/memory/fact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value, user_id: userId }),
  });
  return response.json();
}

/**
 * Explicitly track project.
 */
export async function addProject(project: {
  name: string;
  summary: string;
  status?: string;
  pending_actions?: string[];
  user_id?: string;
}) {
  const response = await fetch(`${API_BASE_URL}/api/memory/project`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: project.name,
      summary: project.summary,
      status: project.status || "active",
      pending_actions: project.pending_actions || [],
      user_id: project.user_id || "default_user",
    }),
  });
  return response.json();
}

/**
 * Clear session memory buffer.
 */
export async function clearSessionMemory(userId: string = "default_user", sessionId: string = "default_session") {
  const response = await fetch(
    `${API_BASE_URL}/api/memory/session?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
    }
  );
  return response.json();
}

/**
 * Fetch autonomous executive briefing.
 */
export async function getExecutiveBriefing(userId: string = "default_user"): Promise<ExecutiveBriefingResponse> {
  const response = await fetch(`${API_BASE_URL}/api/proactivity/briefing?user_id=${encodeURIComponent(userId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch executive briefing [${response.status}]`);
  }
  return response.json();
}

/**
 * Fetch proactive follow-ups.
 */
export async function getProactiveFollowups(userId: string = "default_user"): Promise<ProactiveNotificationItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/proactivity/followups?user_id=${encodeURIComponent(userId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    return [];
  }
  return response.json();
}

export interface DeviceInfoResponse {
  hostname: string;
  primary_ip: string;
  all_ips: string[];
  frontend_port: number;
  backend_port: number;
  mobile_web_url: string;
  backend_api_url: string;
  qr_code_target: string;
  status: string;
}

export interface EmailItem {
  id: string;
  sender: string;
  sender_name?: string;
  subject: string;
  snippet?: string;
  body?: string;
  timestamp: string;
  unread: boolean;
  priority?: string;
}

export interface MailInboxResponse {
  inbox: EmailItem[];
  drafts: any[];
  unread_count: number;
}

export interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size_kb: number;
  modified: string;
}

export interface FileBrowseResponse {
  path: string;
  parent_path?: string;
  total_items: number;
  items: FileItem[];
  error?: string;
}

/**
 * Fetch cross-device pairing and network info.
 */
export async function getDeviceInfo(): Promise<DeviceInfoResponse> {
  const response = await fetch(`${API_BASE_URL}/api/device/info`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch device info [${response.status}]`);
  }
  return response.json();
}

/**
 * Fetch mail inbox and unread summary.
 */
export async function getMailInbox(): Promise<MailInboxResponse> {
  const response = await fetch(`${API_BASE_URL}/api/mail/inbox`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    return { inbox: [], drafts: [], unread_count: 0 };
  }
  return response.json();
}

/**
 * Browse system directory files.
 */
export async function browseSystemFiles(path: string = "D:\\LARA"): Promise<FileBrowseResponse> {
  const response = await fetch(`${API_BASE_URL}/api/files/browse?path=${encodeURIComponent(path)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    return { path, total_items: 0, items: [] };
  }
  return response.json();
}

export interface SystemAppItem {
  name: string;
  path: string;
  category: string;
  icon?: string;
  is_shortcut?: boolean;
}

export interface SystemAppsResponse {
  total: number;
  apps: SystemAppItem[];
}

/**
 * Fetch scanned installed system applications.
 */
export async function getInstalledApps(): Promise<SystemAppsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/system/apps`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    return { total: 0, apps: [] };
  }
  return response.json();
}
