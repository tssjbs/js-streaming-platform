let audio = null;
let callbacks = { onTick: () => {}, onEnded: () => {} };

export function setPlayerCallbacks(cb) {
  callbacks = { ...callbacks, ...cb };
}

export function ensureAudio() {
  if (!audio) {
    audio = new Audio();
    audio.preload = "metadata";
    audio.addEventListener("timeupdate", () => callbacks.onTick());
    audio.addEventListener("ended", () => callbacks.onEnded());
  }
  return audio;
}

export async function playTrack(track) {
  const a = ensureAudio();
  a.src = track.stream_url || `/media/track_${track.id}.wav`;
  try {
    await a.play();
  } catch (_) {
    /* user gesture may be required */
  }
  return a;
}

export function togglePlay() {
  const a = ensureAudio();
  if (!a.src) return false;
  if (a.paused) {
    a.play();
    return true;
  }
  a.pause();
  return false;
}

export function seek(ratio) {
  const a = ensureAudio();
  if (!a.duration) return;
  a.currentTime = a.duration * Math.max(0, Math.min(1, ratio));
}

export function setVolume(v) {
  const a = ensureAudio();
  a.volume = Math.max(0, Math.min(1, v));
}

export function getState() {
  const a = audio;
  if (!a) return { paused: true, current: 0, duration: 0, volume: 1 };
  return {
    paused: a.paused,
    current: a.currentTime || 0,
    duration: a.duration || 0,
    volume: a.volume,
  };
}