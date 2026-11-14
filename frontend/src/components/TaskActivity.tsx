"use client";
import { AgentTask } from "@/lib/api";

export function TaskActivity({ tasks, status }: { tasks: AgentTask[]; status: string }) {
  if (!tasks.length && !status) return null;
  return (
    <section aria-label="Agent task activity" className="w-full max-w-5xl mx-auto px-4 py-2">
      <div className="glass-panel rounded-xl border border-cyan-500/30 p-4 space-y-3">
        <h2 className="text-xs font-mono text-cyan-300 tracking-widest">TASK ACTIVITY</h2>
        {status && <p role="status" className="text-xs text-slate-300">{status}</p>}
        {tasks.slice(0, 3).map((task) => (
          <div key={task.id} className="space-y-2 text-xs">
            <div className="flex gap-3 justify-between"><p className="text-slate-200 truncate">{task.prompt}</p>
              <span className="text-cyan-300 whitespace-nowrap">{task.status.replace(/_/g, " ")}</span></div>
            <ol className="flex flex-wrap gap-2">
              {task.steps.map((step, i) => <li key={i} className={`rounded border px-2 py-1 ${step.status === "failed" ? "border-rose-500 text-rose-300" : step.status === "pending_approval" ? "border-amber-500 text-amber-200" : "border-slate-700 text-slate-300"}`}>
                {i + 1}. {step.tool_name} · {step.status.replace(/_/g, " ")}{step.attempts > 1 ? ` (${step.attempts} attempts)` : ""}
              </li>)}
            </ol>
            {task.status === "interrupted" && <p className="text-amber-200">Execution was interrupted. Check the result before sending this task again.</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
