/**
 * Four streaming encoders with automatic fallback.
 * Order is adjusted from server guardrails when available.
 */

const ENCODER_TIMEOUT_MS = 4500;

function parseYouTubeId(url) {
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtu.be")) return u.pathname.slice(1);
    if (u.searchParams.get("v")) return u.searchParams.get("v");
    const m = u.pathname.match(/\/embed\/([^/]+)/);
    return m ? m[1] : null;
  } catch {
    return null;
  }
}

function mountStage(stage, node) {
  stage.innerHTML = "";
  stage.appendChild(node);
}

export const encoders = {
  async direct_audio(url, stage) {
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = url;
    audio.crossOrigin = "anonymous";
    mountStage(stage, audio);
    await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("direct_audio timeout")), ENCODER_TIMEOUT_MS);
      audio.addEventListener(
        "canplay",
        () => {
          clearTimeout(t);
          audio.play().catch(() => {});
          resolve();
        },
        { once: true }
      );
      audio.addEventListener(
        "error",
        () => {
          clearTimeout(t);
          reject(new Error("direct_audio error"));
        },
        { once: true }
      );
    });
    return { type: "direct_audio", element: audio };
  },

  async video_element(url, stage) {
    const video = document.createElement("video");
    video.controls = true;
    video.src = url;
    video.crossOrigin = "anonymous";
    mountStage(stage, video);
    await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("video_element timeout")), ENCODER_TIMEOUT_MS);
      video.addEventListener(
        "loadeddata",
        () => {
          clearTimeout(t);
          video.play().catch(() => {});
          resolve();
        },
        { once: true }
      );
      video.addEventListener(
        "error",
        () => {
          clearTimeout(t);
          reject(new Error("video_element error"));
        },
        { once: true }
      );
    });
    return { type: "video_element", element: video };
  },

  async iframe_embed(url, stage) {
    const yt = parseYouTubeId(url);
    const iframe = document.createElement("iframe");
    iframe.allow =
      "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    iframe.style.width = "100%";
    iframe.style.aspectRatio = "16/9";
    iframe.style.border = "0";
    iframe.style.borderRadius = "12px";
    if (yt) {
      iframe.src = `https://www.youtube-nocookie.com/embed/${yt}?autoplay=1`;
    } else if (/soundcloud\.com/i.test(url)) {
      iframe.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true`;
    } else {
      iframe.src = url;
    }
    mountStage(stage, iframe);
    await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("iframe_embed timeout")), ENCODER_TIMEOUT_MS);
      iframe.addEventListener(
        "load",
        () => {
          clearTimeout(t);
          resolve();
        },
        { once: true }
      );
      iframe.addEventListener(
        "error",
        () => {
          clearTimeout(t);
          reject(new Error("iframe_embed error"));
        },
        { once: true }
      );
    });
    return { type: "iframe_embed", element: iframe };
  },

  async fetch_blob(url, stage) {
    const res = await fetch(url, { mode: "cors" });
    if (!res.ok) throw new Error("fetch_blob http " + res.status);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = blobUrl;
    mountStage(stage, audio);
    await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("fetch_blob timeout")), ENCODER_TIMEOUT_MS);
      audio.addEventListener(
        "canplay",
        () => {
          clearTimeout(t);
          audio.play().catch(() => {});
          resolve();
        },
        { once: true }
      );
      audio.addEventListener(
        "error",
        () => {
          clearTimeout(t);
          reject(new Error("fetch_blob play error"));
        },
        { once: true }
      );
    });
    return { type: "fetch_blob", element: audio, cleanup: () => URL.revokeObjectURL(blobUrl) };
  },
};

const DEFAULT_ORDER = ["direct_audio", "fetch_blob", "video_element", "iframe_embed"];

export async function playWithFallback(url, stage, order, onStatus) {
  const sequence = (order && order.length ? order : DEFAULT_ORDER).filter((k) => encoders[k]);
  let lastErr = null;
  for (let i = 0; i < sequence.length; i++) {
    const key = sequence[i];
    onStatus?.(`Trying encoder ${i + 1}/4: ${key.replace("_", " ")}…`);
    try {
      const result = await encoders[key](url, stage);
      onStatus?.(`Playing via ${key.replace("_", " ")}`);
      return { ...result, encoderUsed: key, attempts: i + 1 };
    } catch (err) {
      lastErr = err;
      onStatus?.(`${key} failed — switching encoder…`);
    }
  }
  throw lastErr || new Error("All encoders failed");
}