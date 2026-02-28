"use client";

import { useState } from "react";
import type { Finding, ConsensusSummary } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "var(--critical)",
  high: "var(--high)",
  medium: "var(--medium)",
  low: "var(--low)",
  info: "var(--info)",
};

interface FindingsPanelProps {
  consensus: ConsensusSummary | null;
}

function SeverityBadge({ severity }: { severity: string }) {
  const { t } = useI18n();
  const color = SEVERITY_COLORS[severity] || "var(--info)";
  const label = t(`findings.${severity}`);
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-bold"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 20%, transparent)`,
        color,
      }}
    >
      {label !== `findings.${severity}` ? label : severity}
    </span>
  );
}

function FindingItem({ finding }: { finding: Finding }) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="finding-item"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-2">
        <SeverityBadge severity={finding.severity} />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{finding.category}</div>
          <div
            className="text-xs mt-1"
            style={{ color: "var(--text-muted)" }}
          >
            {finding.file_path}
            {finding.line_range && ` (${finding.line_range})`}
          </div>
        </div>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {expanded ? "\u2212" : "+"}
        </span>
      </div>
      {expanded && (
        <div className="mt-3 space-y-2 animate-fade-in">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {finding.description}
          </p>
          <div className="finding-recommendation">
            <strong>{t("findings.recommendation")}</strong> {finding.recommendation}
          </div>
        </div>
      )}
    </div>
  );
}

function FindingsSection({
  title,
  findings,
  defaultOpen = false,
}: {
  title: string;
  findings: Finding[];
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (findings.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        className="flex items-center gap-2 w-full text-left mb-2"
        onClick={() => setOpen(!open)}
      >
        <span className="text-sm font-semibold">{title}</span>
        <span
          className="ml-auto px-2 py-0.5 rounded-full text-xs font-bold"
          style={{
            background: "var(--bg-hover)",
            color: "var(--text-secondary)",
          }}
        >
          {findings.length}
        </span>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {open ? "\u25BC" : "\u25B6"}
        </span>
      </button>
      {open && (
        <div className="space-y-2">
          {findings.map((f, i) => (
            <FindingItem key={i} finding={f} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FindingsPanel({ consensus }: FindingsPanelProps) {
  const { t } = useI18n();

  if (!consensus) {
    return (
      <div
        className="p-4 rounded-lg text-center"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
      >
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          {t("findings.noFindings")}
        </p>
      </div>
    );
  }

  const total =
    consensus.critical.length +
    consensus.high.length +
    consensus.medium.length +
    consensus.low.length;

  return (
    <div className="p-4 rounded-lg" style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>
      <h3
        className="text-sm font-semibold mb-1"
        style={{ color: "var(--text-secondary)" }}
      >
        {t("findings.title")}
      </h3>
      <p className="text-xs mb-4" style={{ color: "var(--text-muted)" }}>
        {t("findings.totalIssues", { count: total })}
      </p>

      <FindingsSection
        title={t("findings.critical")}
        findings={consensus.critical}
        defaultOpen={true}
      />
      <FindingsSection
        title={t("findings.high")}
        findings={consensus.high}
        defaultOpen={true}
      />
      <FindingsSection title={t("findings.medium")} findings={consensus.medium} />
      <FindingsSection title={t("findings.low")} findings={consensus.low} />

      {consensus.positive.length > 0 && (
        <div
          className="mt-4 pt-4"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <h4
            className="text-sm font-semibold mb-2"
            style={{ color: "var(--positive)" }}
          >
            {t("findings.positiveFindings")}
          </h4>
          <ul className="space-y-1">
            {consensus.positive.map((p, i) => (
              <li
                key={i}
                className="text-sm flex items-start gap-2"
                style={{ color: "var(--text-secondary)" }}
              >
                <span style={{ color: "var(--positive)" }}>+</span>
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
