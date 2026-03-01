"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";

// ── Locale types ────────────────────────────────────────────────────

export type Locale = "en" | "zh";

type NestedRecord = { [key: string]: string | NestedRecord };

// ── English translations ────────────────────────────────────────────

const en: NestedRecord = {
  app: {
    title: "COUNCIL",
    subtitle: "AI Social Deduction Game",
    poweredBy: "Powered by Mistral AI",
  },
  header: {
    enterScene: "Enter 3D Roundtable",
    analyzing: "Analyzing...",
  },
  pipeline: {
    title: "Pipeline Status",
    ingest: "Ingest",
    scan: "Scan",
    alignment: "Alignment",
    chatroom: "Chatroom",
    agentsDone: "{count}/4 agents done",
    files: "{count} files",
  },
  findings: {
    title: "Analysis Findings",
    totalIssues: "Found {count} issues",
    noFindings: "No findings yet. Run the analysis to see results.",
    recommendation: "Recommendation:",
    positiveFindings: "Positive Findings",
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
    info: "Info",
  },
  chat: {
    welcome: "Welcome to COUNCIL",
    welcomeDesc: "AI social deduction experience powered by Mistral AI",
    analyzing: "Analyzing with 4 specialist agents...",
    inputPlaceholder: "Ask about the analysis...",
    inputDisabled: "Run analysis first...",
    send: "Send",
    listening: "Listening...",
    error: "Error: {message}",
    unknownError: "Unknown error",
  },
  agents: {
    Orchestrator: "Orchestrator",
    "Architecture Analyst": "Architecture Analyst",
    "Code Quality Analyst": "Code Quality Analyst",
    "Documentation Analyst": "Documentation Analyst",
    "Security Analyst": "Security Analyst",
    System: "System",
  },
  voice: {
    connecting: "Connecting...",
    stopRecording: "Stop recording",
    processing: "Processing...",
    agentSpeaking: "Agent speaking",
    startRecording: "Start recording",
    errorToken: "Failed to get voice token",
    errorConnect: "Voice connection failed",
  },
  analysis: {
    complete:
      "Analysis complete!\n\n{summary}\n\nFound {total} issues: {critical} critical, {high} high, {medium} medium, {low} low.\n\nFeel free to ask me anything about the results!",
    failed: "Analysis failed",
  },
  scene: {
    overview: "Overview",
    focus: "Focus",
    orbit: "Orbit",
    autoFocus: "Auto",
    on: "ON",
    off: "OFF",
    exitScene: "Exit",
    chatTitle: "Discussion",
    inputPlaceholder: "Ask the roundtable...",
    agentsThinking: "Agents are responding...",
    you: "You",
    agent: "Agent",
  },
  tts: {
    playing: "Playing...",
    play: "Play voice",
  },
  game: {
    title: "COUNCIL",
    subtitle: "AI Social Deduction Game",
    upload: {
      title: "Upload a Document",
      description: "Upload any rules, story, or scenario — AI will generate a social deduction game from it",
      dropzone: "Drop file here or click to browse",
      orText: "Or paste text directly",
      textPlaceholder: "Paste your scenario text here...",
      createFromText: "Create Game from Text",
      exampleScenarios: "Try an Example Scenario",
      parsing: "Analyzing document...",
      generating: "Generating characters...",
    },
    lobby: {
      title: "Characters Ready",
      setting: "Setting",
      startGame: "Start Game",
      characters: "Characters",
    },
    board: {
      discussion: "Discussion",
      voting: "Vote Phase",
      inputPlaceholder: "Speak to the council...",
      thinking: "Characters thinking...",
      round: "Round {round}",
    },
    vote: {
      title: "Cast Your Vote",
      confirm: "Confirm Vote",
      waiting: "Counting votes...",
      eliminated: "{name} has been eliminated!",
      noElimination: "No one was eliminated (tie)",
      yourVote: "You voted for {name}",
    },
    reveal: {
      trueRole: "True Role",
      faction: "Faction",
      winCondition: "Win Condition",
      lies: "Deception Timeline",
      continue: "Continue",
    },
    intro: {
      secretIdentity: "Your Secret Identity",
      clickToReveal: "Click to reveal your role",
      faction: "Faction",
      winCondition: "Win Condition",
      allies: "Your Allies",
      enterCouncil: "Enter the Council",
      skipHint: "Press ESC to skip",
    },
    end: {
      title: "Game Over",
      winner: "{faction} wins!",
      playAgain: "Play Again",
      allCharacters: "All Characters Revealed",
    },
    phase: {
      upload: "Upload",
      lobby: "Lobby",
      intro: "Intro",
      discussion: "Discussion",
      voting: "Voting",
      reveal: "Reveal",
      night: "Night",
      ended: "Game Over",
    },
  },
};

// ── Chinese translations ────────────────────────────────────────────

const zh: NestedRecord = {
  app: {
    title: "COUNCIL",
    subtitle: "AI 社交推理游戏",
    poweredBy: "由 Mistral AI 驱动",
  },
  header: {
    enterScene: "进入 3D 圆桌",
    analyzing: "分析中...",
  },
  pipeline: {
    title: "流水线状态",
    ingest: "采集",
    scan: "扫描",
    alignment: "对齐",
    chatroom: "对话",
    agentsDone: "{count}/4 个智能体完成",
    files: "{count} 个文件",
  },
  findings: {
    title: "分析发现",
    totalIssues: "共发现 {count} 个问题",
    noFindings: "暂无发现。请先运行分析以查看结果。",
    recommendation: "修复建议：",
    positiveFindings: "正面发现",
    critical: "严重",
    high: "高危",
    medium: "中危",
    low: "低危",
    info: "信息",
  },
  chat: {
    welcome: "欢迎来到 COUNCIL",
    welcomeDesc: "由 Mistral AI 驱动的 AI 社交推理体验",
    analyzing: "正在使用 4 个专业智能体进行分析...",
    inputPlaceholder: "询问分析结果...",
    inputDisabled: "请先运行分析...",
    send: "发送",
    listening: "正在聆听...",
    error: "错误：{message}",
    unknownError: "未知错误",
  },
  agents: {
    Orchestrator: "协调器",
    "Architecture Analyst": "架构分析师",
    "Code Quality Analyst": "代码质量分析师",
    "Documentation Analyst": "文档分析师",
    "Security Analyst": "安全分析师",
    System: "系统",
  },
  voice: {
    connecting: "连接中...",
    stopRecording: "停止录音",
    processing: "处理中...",
    agentSpeaking: "智能体发言中",
    startRecording: "开始录音",
    errorToken: "获取语音令牌失败",
    errorConnect: "语音连接失败",
  },
  analysis: {
    complete:
      "分析完成！\n\n{summary}\n\n共发现 {total} 个问题：{critical} 个严重、{high} 个高危、{medium} 个中危、{low} 个低危。\n\n可以向我提问关于分析结果的任何问题！",
    failed: "分析失败",
  },
  scene: {
    overview: "全景",
    focus: "聚焦",
    orbit: "环绕",
    autoFocus: "自动",
    on: "开",
    off: "关",
    exitScene: "退出",
    chatTitle: "讨论",
    inputPlaceholder: "向圆桌提问...",
    agentsThinking: "智能体正在回复...",
    you: "你",
    agent: "智能体",
  },
  tts: {
    playing: "播放中...",
    play: "播放语音",
  },
  game: {
    title: "COUNCIL",
    subtitle: "AI 社交推理游戏",
    upload: {
      title: "上传文档",
      description: "上传任意规则书、故事或场景 — AI 将自动生成社交推理游戏",
      dropzone: "拖拽文件到此处或点击浏览",
      orText: "或直接粘贴文本",
      textPlaceholder: "在此粘贴你的场景文本...",
      createFromText: "从文本创建游戏",
      exampleScenarios: "试试示例场景",
      parsing: "正在分析文档...",
      generating: "正在生成角色...",
    },
    lobby: {
      title: "角色就绪",
      setting: "背景设定",
      startGame: "开始游戏",
      characters: "角色",
    },
    board: {
      discussion: "讨论阶段",
      voting: "投票阶段",
      inputPlaceholder: "向议会发言...",
      thinking: "角色思考中...",
      round: "第 {round} 轮",
    },
    vote: {
      title: "投出你的票",
      confirm: "确认投票",
      waiting: "正在计票...",
      eliminated: "{name} 已被淘汰！",
      noElimination: "无人被淘汰（平票）",
      yourVote: "你投给了 {name}",
    },
    reveal: {
      trueRole: "真实身份",
      faction: "阵营",
      winCondition: "胜利条件",
      lies: "谎言时间线",
      continue: "继续",
    },
    intro: {
      secretIdentity: "你的秘密身份",
      clickToReveal: "点击揭示你的角色",
      faction: "阵营",
      winCondition: "胜利条件",
      allies: "你的盟友",
      enterCouncil: "进入议会",
      skipHint: "按 ESC 跳过",
    },
    end: {
      title: "游戏结束",
      winner: "{faction} 获胜！",
      playAgain: "再来一局",
      allCharacters: "所有角色揭示",
    },
    phase: {
      upload: "上传",
      lobby: "大厅",
      intro: "序幕",
      discussion: "讨论",
      voting: "投票",
      reveal: "揭示",
      night: "夜晚",
      ended: "结束",
    },
  },
};

// ── Locale map ──────────────────────────────────────────────────────

const locales: Record<Locale, NestedRecord> = { en, zh };

// ── Helper: resolve dotted key ──────────────────────────────────────

function resolve(obj: NestedRecord, key: string): string {
  const parts = key.split(".");
  let cur: NestedRecord | string = obj;
  for (const p of parts) {
    if (typeof cur === "string") return key;
    cur = cur[p];
    if (cur === undefined) return key;
  }
  return typeof cur === "string" ? cur : key;
}

// ── Interpolate {var} placeholders ──────────────────────────────────

function interpolate(
  template: string,
  vars?: Record<string, string | number>
): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    vars[k] !== undefined ? String(vars[k]) : `{${k}}`
  );
}

// ── Context ─────────────────────────────────────────────────────────

interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue>({
  locale: "en",
  setLocale: () => {},
  t: (key) => key,
});

// ── Provider ────────────────────────────────────────────────────────

export function I18nProvider({
  defaultLocale = "en",
  children,
}: {
  defaultLocale?: Locale;
  children: ReactNode;
}) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);

  // Sync from localStorage after hydration to avoid mismatch
  useEffect(() => {
    const saved = localStorage.getItem("council-locale") as Locale | null;
    if (saved && locales[saved] && saved !== defaultLocale) {
      setLocaleState(saved);
    }
  }, [defaultLocale]);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("council-locale", l);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const raw = resolve(locales[locale], key);
      return interpolate(raw, vars);
    },
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

// ── Hook ────────────────────────────────────────────────────────────

export function useI18n() {
  return useContext(I18nContext);
}
