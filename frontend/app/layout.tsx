import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "COUNCIL — AI 社交推理游戏",
  description: "由 Mistral AI 驱动的多角色社交推理体验",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
