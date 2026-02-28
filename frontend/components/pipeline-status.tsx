"use client";

import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";

type StageStatus = "pending" | "active" | "completed" | "error";

interface PipelineStage {
  id: string;
  labelKey: string;
  status: StageStatus;
  detail?: string;
}

interface StatusEvent {
  event: string;
  phase?: string;
  status?: string;
  agent?: string;
  findings?: number;
  files?: number;
}

interface PipelineStatusProps {
  isRunning: boolean;
  events: StatusEvent[];
}

const defaultStages: PipelineStage[] = [
  { id: "ingest", labelKey: "pipeline.ingest", status: "pending" },
  { id: "scan", labelKey: "pipeline.scan", status: "pending" },
  { id: "alignment", labelKey: "pipeline.alignment", status: "pending" },
  { id: "chatroom", labelKey: "pipeline.chatroom", status: "pending" },
];

export default function PipelineStatus({
  isRunning,
  events,
}: PipelineStatusProps) {
  const { t } = useI18n();
  const [stages, setStages] = useState<PipelineStage[]>(defaultStages);

  useEffect(() => {
    if (!isRunning && events.length === 0) {
      setStages(
        defaultStages.map((s) => ({ ...s, status: "pending" as StageStatus }))
      );
      return;
    }

    const updated: PipelineStage[] = defaultStages.map((s) => ({ ...s }));
    const agentsDone: string[] = [];

    for (const ev of events) {
      if (ev.event === "phase" && ev.phase) {
        const idx = updated.findIndex((s) => s.id === ev.phase);
        if (idx >= 0) {
          if (ev.status === "started") {
            updated[idx].status = "active";
          } else if (
            ev.status === "completed" ||
            ev.status === "ready"
          ) {
            updated[idx].status = "completed";
            if (ev.files) updated[idx].detail = t("pipeline.files", { count: ev.files });
          }
        }
      }
      if (ev.event === "agent_done" && ev.agent) {
        agentsDone.push(ev.agent);
      }
    }

    if (agentsDone.length > 0) {
      const scanIdx = updated.findIndex((s) => s.id === "scan");
      if (scanIdx >= 0) {
        updated[scanIdx].detail = t("pipeline.agentsDone", { count: agentsDone.length });
      }
    }

    setStages(updated);
  }, [events, isRunning, t]);

  return (
    <div className="p-4 rounded-lg" style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>
      <h3
        className="text-sm font-semibold mb-3"
        style={{ color: "var(--text-secondary)" }}
      >
        {t("pipeline.title")}
      </h3>
      <div className="space-y-1">
        {stages.map((stage, idx) => (
          <div key={stage.id}>
            <div className="pipeline-step">
              <div className={`pipeline-dot pipeline-dot-${stage.status}`} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{t(stage.labelKey)}</div>
                {stage.detail && (
                  <div
                    className="text-xs truncate"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {stage.detail}
                  </div>
                )}
              </div>
              {stage.status === "active" && (
                <div
                  className="w-4 h-4 rounded-full border-2 animate-spin-custom"
                  style={{
                    borderColor: "var(--accent)",
                    borderTopColor: "transparent",
                  }}
                />
              )}
              {stage.status === "completed" && (
                <span style={{ color: "var(--positive)", fontSize: 14 }}>&#10003;</span>
              )}
            </div>
            {idx < stages.length - 1 && (
              <div
                className="pipeline-connector"
                style={{
                  background:
                    stage.status === "completed"
                      ? "var(--positive)"
                      : "var(--border)",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
