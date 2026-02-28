"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[COUNCIL] Root error boundary caught:", error);
  }, [error]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "#060612",
        color: "#e0e0e0",
        fontFamily: "system-ui, sans-serif",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>!</div>
      <h2 style={{ fontSize: "1.25rem", marginBottom: "0.5rem", color: "#fff" }}>
        Something went wrong
      </h2>
      <p
        style={{
          fontSize: "0.875rem",
          color: "#888",
          maxWidth: "480px",
          marginBottom: "1.5rem",
          wordBreak: "break-word",
        }}
      >
        {error.message}
      </p>
      <button
        onClick={reset}
        style={{
          padding: "0.5rem 1.5rem",
          borderRadius: "0.5rem",
          border: "1px solid #333",
          background: "#111",
          color: "#fff",
          cursor: "pointer",
          fontSize: "0.875rem",
        }}
      >
        Retry
      </button>
    </div>
  );
}
