"use client";

import { useEffect, useRef, useMemo } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import {
  EffectComposer as PMEffectComposer,
  EffectPass,
  RenderPass,
  BloomEffect,
  VignetteEffect,
  BlendFunction,
  KernelSize,
} from "postprocessing";
import type { GamePhase } from "@/lib/game-types";

/* ── Phase-based effect presets ──────────────────────────────────── */

interface PhasePreset {
  bloomIntensity: number;
  bloomThreshold: number;
  vignetteOffset: number;
  vignetteDarkness: number;
}

const PHASE_PRESETS: Record<string, PhasePreset> = {
  discussion: { bloomIntensity: 0.4, bloomThreshold: 0.6, vignetteOffset: 0.3, vignetteDarkness: 0.65 },
  voting:     { bloomIntensity: 0.6, bloomThreshold: 0.5, vignetteOffset: 0.25, vignetteDarkness: 0.80 },
  reveal:     { bloomIntensity: 0.8, bloomThreshold: 0.3, vignetteOffset: 0.2, vignetteDarkness: 0.85 },
  night:      { bloomIntensity: 0.2, bloomThreshold: 0.7, vignetteOffset: 0.2, vignetteDarkness: 0.85 },
};

const DEFAULT_PRESET: PhasePreset = PHASE_PRESETS.discussion;

/* ── Props ───────────────────────────────────────────────────────── */

interface PostProcessingProps {
  gamePhase?: GamePhase;
  round?: number;
}

/**
 * Fully imperative post-processing — bypasses @react-three/postprocessing's
 * JSX wrappers to avoid the R3F reconciler calling JSON.stringify on effect
 * objects with circular references (KawaseBlurPass.resolution.resizable).
 */
export function PostProcessing({ gamePhase = "discussion", round = 1 }: PostProcessingProps) {
  const { gl, scene, camera, size } = useThree();

  // Create effects once
  const bloom = useMemo(
    () =>
      new BloomEffect({
        intensity: DEFAULT_PRESET.bloomIntensity,
        luminanceThreshold: DEFAULT_PRESET.bloomThreshold,
        luminanceSmoothing: 0.9,
        mipmapBlur: true,
        kernelSize: KernelSize.LARGE,
      }),
    [],
  );

  const vignette = useMemo(
    () =>
      new VignetteEffect({
        offset: DEFAULT_PRESET.vignetteOffset,
        darkness: DEFAULT_PRESET.vignetteDarkness,
        blendFunction: BlendFunction.NORMAL,
      }),
    [],
  );

  // Build composer imperatively
  const composer = useMemo(() => {
    const c = new PMEffectComposer(gl);
    c.addPass(new RenderPass(scene, camera));
    c.addPass(new EffectPass(camera, bloom, vignette));
    return c;
  }, [gl, scene, camera, bloom, vignette]);

  // Keep composer in sync with viewport size
  useEffect(() => {
    composer.setSize(size.width, size.height);
  }, [composer, size]);

  // Dispose on unmount
  useEffect(() => {
    return () => {
      composer.dispose();
    };
  }, [composer]);

  // Store mutable lerp targets
  const currentValues = useRef({ ...DEFAULT_PRESET });

  // Per-frame: lerp effect parameters + render
  useFrame((_, delta) => {
    const target = PHASE_PRESETS[gamePhase] || DEFAULT_PRESET;

    // Escalating intensity per round
    const roundEscalation = Math.max(0, (round - 1) * 0.03);
    const bloomEscalation = Math.max(0, (round - 1) * 0.02);

    const targetDarkness = Math.min(1.0, target.vignetteDarkness + roundEscalation);
    const targetBloom = Math.min(1.2, target.bloomIntensity + bloomEscalation);

    // Lerp speed: ~2.5s transition
    const lerpSpeed = 1.5 * delta;
    const cv = currentValues.current;
    cv.bloomIntensity += (targetBloom - cv.bloomIntensity) * lerpSpeed;
    cv.bloomThreshold += (target.bloomThreshold - cv.bloomThreshold) * lerpSpeed;
    cv.vignetteOffset += (target.vignetteOffset - cv.vignetteOffset) * lerpSpeed;
    cv.vignetteDarkness += (targetDarkness - cv.vignetteDarkness) * lerpSpeed;

    // Apply to effects (using typed getters/setters)
    bloom.intensity = cv.bloomIntensity;
    bloom.luminanceMaterial.threshold = cv.bloomThreshold;
    vignette.offset = cv.vignetteOffset;
    vignette.darkness = cv.vignetteDarkness;

    // Render through composer instead of default R3F render
    composer.render(delta);
  }, 1); // Priority 1 = runs after default scene updates but replaces default render

  // Disable R3F's default render loop since we render via composer
  useEffect(() => {
    gl.autoClear = false;
    return () => {
      gl.autoClear = true;
    };
  }, [gl]);

  return null; // No JSX — fully imperative
}
