"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, FileText, Loader2, Sparkles } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { useI18n } from "@/lib/i18n";

export default function DocumentUpload() {
  const { t } = useI18n();
  const {
    phase,
    parseProgress,
    error,
    scenarios,
    uploadDocument,
    uploadText,
    loadScenario,
    loadScenarios,
  } = useGameState();

  const [isDragOver, setIsDragOver] = useState(false);
  const [textInput, setTextInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) uploadDocument(file);
    },
    [uploadDocument]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadDocument(file);
    },
    [uploadDocument]
  );

  const handleTextSubmit = useCallback(() => {
    const trimmed = textInput.trim();
    if (trimmed) uploadText(trimmed);
  }, [textInput, uploadText]);

  const isParsing = phase === "parsing";

  if (isParsing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <div className="glass-card p-12 max-w-md w-full text-center space-y-6">
          <Loader2
            size={48}
            className="animate-spin-custom mx-auto"
            style={{ color: "var(--accent)" }}
          />
          <div>
            <p
              className="text-lg font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              {parseProgress || t("game.upload.parsing")}
            </p>
            <p
              className="text-sm mt-2"
              style={{ color: "var(--text-muted)" }}
            >
              {t("game.upload.generating")}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Title */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold welcome-gradient-text">
            {t("game.title")}
          </h1>
          <p className="text-lg" style={{ color: "var(--text-secondary)" }}>
            {t("game.subtitle")}
          </p>
        </div>

        {/* Upload zone */}
        <div className="glass-card p-8 space-y-6">
          <div className="text-center space-y-1">
            <h2
              className="text-xl font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              {t("game.upload.title")}
            </h2>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              {t("game.upload.description")}
            </p>
          </div>

          {/* Dropzone */}
          <div
            className={`dropzone ${isDragOver ? "dropzone-active" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload
              size={32}
              className="mx-auto mb-3"
              style={{
                color: isDragOver ? "var(--accent)" : "var(--text-muted)",
              }}
            />
            <p style={{ color: "var(--text-secondary)" }}>
              {t("game.upload.dropzone")}
            </p>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".txt,.md,.pdf,.doc,.docx"
              onChange={handleFileSelect}
            />
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4">
            <div
              className="flex-1 h-px"
              style={{ background: "var(--border)" }}
            />
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-muted)" }}
            >
              {t("game.upload.orText")}
            </span>
            <div
              className="flex-1 h-px"
              style={{ background: "var(--border)" }}
            />
          </div>

          {/* Text input */}
          <div className="space-y-3">
            <textarea
              className="w-full p-4 rounded-xl text-sm resize-none"
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                minHeight: "120px",
              }}
              placeholder={t("game.upload.textPlaceholder")}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
            />
            <button
              className="demo-btn w-full flex items-center justify-center gap-2"
              onClick={handleTextSubmit}
              disabled={!textInput.trim()}
            >
              <FileText size={16} />
              {t("game.upload.createFromText")}
            </button>
          </div>
        </div>

        {/* Example scenarios */}
        {scenarios.length > 0 && (
          <div className="space-y-3">
            <p
              className="text-sm font-medium text-center"
              style={{ color: "var(--text-muted)" }}
            >
              {t("game.upload.exampleScenarios")}
            </p>
            <div className="grid grid-cols-2 gap-3">
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  className="welcome-card p-4 text-left"
                  onClick={() => loadScenario(s.id)}
                >
                  <div className="flex items-center gap-2">
                    <Sparkles
                      size={14}
                      style={{ color: "var(--accent)" }}
                    />
                    <span
                      className="text-sm font-medium"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {s.name}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            className="p-3 rounded-lg text-sm text-center animate-fade-in"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              color: "var(--critical)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
