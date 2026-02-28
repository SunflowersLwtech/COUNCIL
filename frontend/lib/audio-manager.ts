let currentAudio: HTMLAudioElement | null = null;
let currentCleanup: (() => void) | null = null;

export function playManagedAudio(blob: Blob, onEnd: () => void): HTMLAudioElement {
  // Stop previous audio
  stopManagedAudio();

  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  currentAudio = audio;

  const cleanup = () => {
    URL.revokeObjectURL(url);
    if (currentAudio === audio) {
      currentAudio = null;
      currentCleanup = null;
    }
    onEnd();
  };
  currentCleanup = cleanup;

  audio.onended = cleanup;
  audio.onerror = cleanup;
  return audio;
}

export function stopManagedAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
  }
  currentCleanup?.();
  currentAudio = null;
  currentCleanup = null;
}

export function isAudioPlaying(): boolean {
  return currentAudio !== null && !currentAudio.paused;
}
