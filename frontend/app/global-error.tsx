"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={{ margin: 0, background: "#060612", color: "#e4e4e7" }}>
        <div
          style={{
            height: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "16px",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <p style={{ fontSize: "18px", fontWeight: 600 }}>Something went wrong</p>
          <p style={{ fontSize: "14px", color: "#71717a", maxWidth: "400px", textAlign: "center" }}>
            {error.message}
          </p>
          <button
            onClick={reset}
            style={{
              padding: "8px 20px",
              borderRadius: "8px",
              background: "#ff6b35",
              color: "white",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
