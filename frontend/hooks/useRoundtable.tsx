"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import type { CameraView } from "@/lib/scene-constants";

export type { CameraView };

type SetThinkingAgents = (ids: string[] | ((prev: string[]) => string[])) => void;

interface RoundtableState {
  speakingAgentId: string | null;
  thinkingAgentIds: string[];
  cameraView: CameraView;
  setCameraView: (view: CameraView) => void;
  autoFocusEnabled: boolean;
  toggleAutoFocus: () => void;
  showScene: boolean;
  toggleScene: () => void;
  setSpeakingAgent: (id: string | null) => void;
  setThinkingAgents: SetThinkingAgents;
}

const RoundtableContext = createContext<RoundtableState | null>(null);

export function RoundtableProvider({ children }: { children: ReactNode }) {
  const [speakingAgentId, setSpeakingAgentId] = useState<string | null>(null);
  const [thinkingAgentIds, setThinkingAgentIds] = useState<string[]>([]);
  const [cameraView, setCameraView] = useState<CameraView>("first-person");
  const [autoFocusEnabled, setAutoFocusEnabled] = useState(true);
  const [showScene, setShowScene] = useState(false);

  const setThinkingAgents: SetThinkingAgents = useCallback(
    (idsOrFn) => {
      if (typeof idsOrFn === "function") {
        setThinkingAgentIds(idsOrFn);
      } else {
        setThinkingAgentIds(idsOrFn);
      }
    },
    []
  );

  return (
    <RoundtableContext.Provider
      value={{
        speakingAgentId,
        thinkingAgentIds,
        cameraView,
        setCameraView,
        autoFocusEnabled,
        toggleAutoFocus: () => setAutoFocusEnabled(prev => !prev),
        showScene,
        toggleScene: () => setShowScene(prev => !prev),
        setSpeakingAgent: setSpeakingAgentId,
        setThinkingAgents,
      }}
    >
      {children}
    </RoundtableContext.Provider>
  );
}

export function useRoundtable() {
  const ctx = useContext(RoundtableContext);
  if (!ctx) throw new Error("useRoundtable must be used within RoundtableProvider");
  return ctx;
}
