"use client";

import type { GamePhase } from "@/lib/game-types";

interface PostProcessingProps {
  gamePhase?: GamePhase;
  round?: number;
}

/**
 * PostProcessing placeholder — disabled to prevent WebGL context loss.
 * The bloom/vignette effects were allocating extra framebuffers and
 * taking over R3F's render pipeline (useFrame priority 1), which caused
 * blank screens when the GPU couldn't handle the load.
 *
 * The scene already looks good with the emissive materials + additive
 * blending on ring/glow elements providing a natural bloom-like feel.
 */
export function PostProcessing(_props: PostProcessingProps) {
  return null;
}
