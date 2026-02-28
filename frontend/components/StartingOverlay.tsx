"use client";

interface StartingOverlayProps {
  progress: number;
  statusText: string;
}

export default function StartingOverlay({ progress, statusText }: StartingOverlayProps) {
  return (
    <div className="starting-overlay">
      <div className="starting-overlay-card">
        <p className="starting-status-text">{statusText}</p>
        <div className="starting-progress-track">
          <div
            className="starting-progress-bar"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        <p className="starting-progress-pct">
          {Math.round(Math.min(progress, 100))}%
        </p>
      </div>
    </div>
  );
}
