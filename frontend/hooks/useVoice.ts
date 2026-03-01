"use client";

import { useState, useRef, useCallback } from "react";
import { generateTTS } from "@/lib/api";
import { agentRoleToId } from "@/lib/agent-utils";
import { playManagedAudio, stopManagedAudio } from "@/lib/audio-manager";

export type VoiceStatus =
  | "idle"
  | "connecting"
  | "listening"
  | "processing"
  | "speaking";

interface UseVoiceOptions {
  onTranscript: (text: string) => void;
  onError?: (message: string) => void;
}

interface TtsQueueItem {
  text: string;
  agentRole: string;
}

// Check browser Web Speech API support
function getWebSpeechRecognition(): (new () => any) | null {
  if (typeof window === "undefined") return null;
  return (
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition ||
    null
  );
}

export function useVoice({ onTranscript, onError }: UseVoiceOptions) {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [partialTranscript, setPartialTranscript] = useState("");
  const [speakingAgentId, setSpeakingAgentId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const scribeRef = useRef<any>(null);
  const webSpeechRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const ttsQueueRef = useRef<TtsQueueItem[]>([]);
  const ttsProcessingRef = useRef(false);
  const queueAbortRef = useRef<AbortController | null>(null);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const usingWebSpeechRef = useRef(false);

  const showError = useCallback(
    (msg: string) => {
      setErrorMessage(msg);
      onError?.(msg);
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
      errorTimerRef.current = setTimeout(() => setErrorMessage(null), 4000);
    },
    [onError]
  );

  // ── Web Speech API fallback ────────────────────────────────────────

  const startWebSpeech = useCallback(() => {
    const SpeechRecognitionClass = getWebSpeechRecognition();
    if (!SpeechRecognitionClass) {
      showError("Browser does not support speech recognition");
      setStatus("idle");
      return false;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = navigator.language || "zh-CN";

      recognition.onresult = (event: any) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            final += result[0].transcript;
          } else {
            interim += result[0].transcript;
          }
        }
        if (interim) setPartialTranscript(interim);
        if (final) {
          onTranscript(final.trim());
          setPartialTranscript("");
        }
      };

      recognition.onerror = (event: any) => {
        console.error("Web Speech error:", event.error);
        if (event.error === "not-allowed") {
          showError("Microphone permission denied");
        } else if (event.error !== "aborted") {
          showError(`Speech recognition error: ${event.error}`);
        }
        setStatus("idle");
        setPartialTranscript("");
        webSpeechRef.current = null;
        usingWebSpeechRef.current = false;
      };

      recognition.onend = () => {
        if (usingWebSpeechRef.current) {
          setStatus("idle");
          setPartialTranscript("");
          webSpeechRef.current = null;
          usingWebSpeechRef.current = false;
        }
      };

      recognition.start();
      webSpeechRef.current = recognition;
      usingWebSpeechRef.current = true;
      setStatus("listening");
      return true;
    } catch (err) {
      console.error("Web Speech start error:", err);
      showError("Failed to start speech recognition");
      setStatus("idle");
      return false;
    }
  }, [onTranscript, showError]);

  // ── STT (ElevenLabs Scribe with Web Speech fallback) ───────────────

  const startListening = useCallback(async () => {
    if (status !== "idle") return;
    setStatus("connecting");
    setPartialTranscript("");
    setErrorMessage(null);

    try {
      // 1. Try ElevenLabs Scribe first
      const tokenRes = await fetch("/api/voice/scribe-token", {
        method: "POST",
      });

      if (!tokenRes.ok) {
        throw new Error("Scribe token unavailable");
      }

      const data = await tokenRes.json();
      if (!data.token) {
        throw new Error("No token in response");
      }

      // 2. Dynamic import to avoid SSR issues
      const { Scribe, RealtimeEvents } = await import("@elevenlabs/client");

      // 3. Connect
      const scribe = Scribe.connect({
        token: data.token,
        modelId: "scribe_v2_realtime",
        microphone: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      scribeRef.current = scribe;

      scribe.on(RealtimeEvents.OPEN, () => {
        setStatus("listening");
      });

      scribe.on(RealtimeEvents.ERROR, (ev: any) => {
        console.error("Scribe error:", ev);
        // Close Scribe to release microphone before falling back
        scribeRef.current = null;
        try { scribe.close(); } catch {}
        // Fall back to Web Speech API
        // Delay to allow microphone release
        setTimeout(() => {
          if (!startWebSpeech()) {
            showError("Voice connection error");
            setStatus("idle");
          }
        }, 500);
      });

      scribe.on(RealtimeEvents.AUTH_ERROR, (ev: any) => {
        console.error("Scribe auth error:", ev);
        scribeRef.current = null;
        try { scribe.close(); } catch {}
        // Fall back to Web Speech API
        setTimeout(() => {
          if (!startWebSpeech()) {
            showError("Voice authentication failed");
            setStatus("idle");
          }
        }, 500);
      });

      scribe.on(RealtimeEvents.PARTIAL_TRANSCRIPT, (ev: any) => {
        setPartialTranscript(ev.text ?? "");
      });

      scribe.on(RealtimeEvents.COMMITTED_TRANSCRIPT, (ev: any) => {
        const final = ev.text?.trim();
        if (final) {
          onTranscript(final);
        }
      });

      scribe.on(RealtimeEvents.CLOSE, () => {
        // Don't reset status if we've already fallen back to Web Speech
        if (!usingWebSpeechRef.current) {
          setStatus("idle");
          setPartialTranscript("");
        }
        scribeRef.current = null;
      });
    } catch (err) {
      console.warn("ElevenLabs Scribe unavailable, using Web Speech API:", err);
      scribeRef.current = null;

      // Fall back to Web Speech API
      if (!startWebSpeech()) {
        showError("Voice recognition unavailable");
        setStatus("idle");
        setPartialTranscript("");
      }
    }
  }, [status, onTranscript, showError, startWebSpeech]);

  const stopListening = useCallback(() => {
    // Stop Web Speech API if active
    if (usingWebSpeechRef.current && webSpeechRef.current) {
      setStatus("processing");
      try {
        webSpeechRef.current.stop();
      } catch {
        // already stopped
      }
      usingWebSpeechRef.current = false;
      webSpeechRef.current = null;
      setTimeout(() => setStatus("idle"), 300);
      return;
    }

    // Stop ElevenLabs Scribe
    const scribe = scribeRef.current;
    if (!scribe) return;
    setStatus("processing");

    try {
      scribe.commit();
      setTimeout(() => {
        try {
          scribe.close();
        } catch {
          // already closed
        }
      }, 300);
    } catch {
      setStatus("idle");
      setPartialTranscript("");
      scribeRef.current = null;
    }
  }, []);

  // ── TTS (single) ──────────────────────────────────────────────────

  const playAgentResponse = useCallback(
    async (text: string, agentRole: string) => {
      const agentId = agentRoleToId(agentRole);
      setStatus("speaking");

      try {
        const blob = await generateTTS(text, agentId);
        if (!blob) {
          setStatus("idle");
          return;
        }

        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          URL.revokeObjectURL(url);
          audioRef.current = null;
          setSpeakingAgentId(null);
          setStatus("idle");
        };
        audio.onerror = () => {
          URL.revokeObjectURL(url);
          audioRef.current = null;
          setSpeakingAgentId(null);
          setStatus("idle");
        };

        setSpeakingAgentId(agentId);
        await audio.play();
      } catch {
        setSpeakingAgentId(null);
        setStatus("idle");
      }
    },
    []
  );

  // ── TTS Queue (multi-agent) ───────────────────────────────────────

  const processQueue = useCallback(async () => {
    if (ttsProcessingRef.current) return;
    ttsProcessingRef.current = true;
    setStatus("speaking");

    const abortController = new AbortController();
    queueAbortRef.current = abortController;

    let prefetchedBlob: Blob | null = null;
    let prefetchedItem: TtsQueueItem | null = null;

    while (ttsQueueRef.current.length > 0 || prefetchedBlob) {
      if (abortController.signal.aborted) break;

      let blob: Blob | null;
      let item: TtsQueueItem;

      if (prefetchedBlob && prefetchedItem) {
        blob = prefetchedBlob;
        item = prefetchedItem;
        prefetchedBlob = null;
        prefetchedItem = null;
      } else {
        item = ttsQueueRef.current.shift()!;
        const agentId = agentRoleToId(item.agentRole);
        try {
          blob = await generateTTS(item.text, agentId);
        } catch {
          blob = null;
        }
      }

      if (!blob) continue;
      if (abortController.signal.aborted) break;

      // Pre-fetch next item while current audio plays (Bug 3: save reference)
      let prefetchPromise: Promise<Blob | null> | null = null;
      let prefetchRef: TtsQueueItem | null = null;
      if (ttsQueueRef.current.length > 0) {
        prefetchRef = ttsQueueRef.current[0];
        const nextAgentId = agentRoleToId(prefetchRef.agentRole);
        prefetchPromise = generateTTS(prefetchRef.text, nextAgentId).catch(() => null);
      }

      // Play audio via global audio manager (Bug 4)
      const audio = playManagedAudio(blob, () => {
        audioRef.current = null;
        setSpeakingAgentId(null);
      });
      audioRef.current = audio;

      // Wait for playback to finish, with abort support (Bug 2)
      await new Promise<void>((resolve) => {
        const onAbort = () => resolve();
        abortController.signal.addEventListener('abort', onAbort, { once: true });

        const originalOnended = audio.onended;
        audio.onended = (ev) => {
          abortController.signal.removeEventListener('abort', onAbort);
          if (typeof originalOnended === 'function') originalOnended.call(audio, ev);
          resolve();
        };
        const originalOnerror = audio.onerror;
        audio.onerror = (ev) => {
          abortController.signal.removeEventListener('abort', onAbort);
          if (typeof originalOnerror === 'function') (originalOnerror as any).call(audio, ev);
          resolve();
        };

        setSpeakingAgentId(agentRoleToId(item.agentRole));
        audio.play().catch(() => {
          abortController.signal.removeEventListener('abort', onAbort);
          resolve();
        });
      });

      if (abortController.signal.aborted) break;

      // Collect pre-fetched result (Bug 3: match by reference, not blind shift)
      if (prefetchPromise && prefetchRef) {
        try {
          prefetchedBlob = await prefetchPromise;
          if (prefetchedBlob) {
            const idx = ttsQueueRef.current.indexOf(prefetchRef);
            if (idx >= 0) {
              prefetchedItem = ttsQueueRef.current.splice(idx, 1)[0];
            } else {
              // Item was consumed elsewhere, discard prefetched blob
              prefetchedBlob = null;
            }
          }
        } catch {
          prefetchedBlob = null;
          prefetchedItem = null;
        }
      }
    }

    ttsProcessingRef.current = false;
    queueAbortRef.current = null;
    setStatus("idle");
  }, []);

  const queueAgentResponses = useCallback(
    (items: TtsQueueItem[]) => {
      ttsQueueRef.current.push(...items);
      processQueue();
    },
    [processQueue]
  );

  const queueSingleResponse = useCallback(
    (text: string, agentRole: string) => {
      ttsQueueRef.current.push({ text, agentRole });
      processQueue();
    },
    [processQueue]
  );

  const stopSpeaking = useCallback(() => {
    ttsQueueRef.current = [];
    queueAbortRef.current?.abort();
    queueAbortRef.current = null;

    stopManagedAudio();
    audioRef.current = null;
    setSpeakingAgentId(null);
    setStatus("idle");
  }, []);

  return {
    status,
    partialTranscript,
    errorMessage,
    isListening: status === "listening",
    isSpeaking: status === "speaking",
    speakingAgentId,
    startListening,
    stopListening,
    playAgentResponse,
    queueAgentResponses,
    queueSingleResponse,
    stopSpeaking,
  };
}
