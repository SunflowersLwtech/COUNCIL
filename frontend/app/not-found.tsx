export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <h1 className="text-4xl font-bold" style={{ color: "var(--accent)" }}>
        404
      </h1>
      <p style={{ color: "var(--text-secondary)" }}>
        页面未找到
      </p>
      <a
        href="/"
        className="px-4 py-2 rounded-lg text-sm font-medium text-white"
        style={{ background: "var(--accent)" }}
      >
        返回首页
      </a>
    </div>
  );
}
