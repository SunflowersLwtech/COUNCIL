"use client";

import { Globe } from "lucide-react";
import { useI18n, type Locale } from "@/lib/i18n";

export default function LanguageToggle() {
  const { locale, setLocale } = useI18n();
  const next: Locale = locale === "en" ? "zh" : "en";
  return (
    <button
      onClick={() => setLocale(next)}
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
      style={{
        background: "var(--bg-hover)",
        color: "var(--text-secondary)",
        border: "1px solid var(--border)",
      }}
      title={locale === "en" ? "Switch to Chinese" : "Switch to English"}
    >
      <Globe size={14} />
      {locale === "en" ? "EN" : "ZH"}
    </button>
  );
}
