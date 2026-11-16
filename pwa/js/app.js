import { playWithFallback } from "./encoders.js";
import * as player from "./player.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const state = {
  catalog: [],
  queue: [],
  queueIndex: 0,
  current: null,
  proposalId: null,
  playlist: [],
  filter: "",
  chip: "All sounds",
  favorites: JSON.parse(localStorage.getItem("jsm_favs") || "[]"),
  recent: JSON.parse(localStorage.getItem("jsm_recent") || "[]"),
};

const FEATURED = [
  { key: "ocean", title: "Ocean Drive", sub: "For the scenic route", className: "art-ocean" },
  { key: "jazz", title: "Midnight Jazz", sub: "Ease into the after hours", className: "art-jazz" },
  { key: "island", title: "Island Time", sub: "A little sunshine, on demand", className: "art-island" },
  { key: "sunday", title: "Sunday Morning", sub: "Room to breathe and reset", className: "art-sunday" },
];

const CHIPS = ["All sounds", "Chill & focus", "Jazz & soul", "Island vibes", "Sunday reset"];
const PAGE_META = {
  home: { title: "Home", eyebrow: "Good music. Every mood." },
  discover: { title: "Discover", eyebrow: "Welcome to your next favorite." },
  genres: { title: "Genres", eyebrow: "Browse by sound." },
  artists: { title: "Artists", eyebrow: "Who you're vibing with." },
  library: { title: "My Library", eyebrow: "Your saved mixes." },
  favorites: { title: "Favorites", eyebrow: "Liked songs." },
};

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || data.reason || "Request failed");
  return data;
}

function fmtTime(sec) {
  if (!sec || !Number.isFinite(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function trackUrl(s) {
  return { ...s, stream_url: `/media/track_${s.id}.wav`, duration_label: "0:22" };
}

function saveFavs() {
  localStorage.setItem("jsm_favs", JSON.stringify(state.favorites));
}
function saveRecent() {
  localStorage.setItem("jsm_recent", JSON.stringify(state.recent.slice(0, 12)));
}

function isFav(id) {
  return state.favorites.includes(id);
}
function toggleFav(id) {
  if (isFav(id)) state.favorites = state.favorites.filter((x) => x !== id);
  else state.favorites.push(id);
  saveFavs();
  renderFavorites();
  updatePlayerFav();
}

function pushRecent(track) {
  state.recent = [track.id, ...state.recent.filter((x) => x !== track.id)].slice(0, 12);
  saveRecent();
  renderRecent();
}

function moodClass(song) {
  const g = song.genre.toLowerCase();
  if (g.includes("jazz")) return "Jazz & soul";
  if (song.mood === "chill") return "Chill & focus";
  if (g.includes("hip")) return "Island vibes";
  return "Sunday reset";
}

function filteredSongs() {
  let list = [...state.catalog];
  const q = state.filter.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        s.artist.toLowerCase().includes(q) ||
        s.mood.toLowerCase().includes(q) ||
        s.genre.toLowerCase().includes(q)
    );
  }
  if (state.chip !== "All sounds") {
    list = list.filter((s) => moodClass(s) === state.chip);
  }
  return list;
}

function renderTrackRow(song, index, host, { showPlay = true } = {}) {
  const row = document.createElement("div");
  row.className = "track-row" + (state.current?.id === song.id ? " playing" : "");
  const fav = isFav(song.id) ? "♥" : "♡";
  row.innerHTML = `
    <span class="idx">${index}</span>
    <span class="thumb"></span>
    <div>
      <strong>${song.title}</strong><br/>
      <span class="muted">${song.artist} · JS Studio</span>
    </div>
    <span class="mood-pill">${song.genre}</span>
    <span class="time">${song.duration_label || "0:22"}</span>
    <button type="button" class="row-heart ${isFav(song.id) ? "on" : ""}">${fav}</button>
  `;
  row.addEventListener("click", (e) => {
    if (e.target.closest(".row-heart")) {
      toggleFav(song.id);
      return;
    }
    playSong(song);
  });
  host.appendChild(row);
}

function renderTrackTable(host, songs) {
  host.innerHTML = "";
  songs.forEach((s, i) => renderTrackRow(trackUrl(s), i + 1, host));
}

function renderFeatured() {
  const host = $("#featured-cards");
  if (!host) return;
  host.innerHTML = "";
  FEATURED.forEach((f, i) => {
    const song = state.catalog[i % state.catalog.length];
    const card = document.createElement("article");
    card.className = `mix-card ${f.className}`;
    card.innerHTML = `
      <button type="button" class="card-heart" data-fav="${song?.id || ""}">♡</button>
      <h4>${f.title}</h4>
      <p>${f.sub}</p>
      <button type="button" class="card-play" title="Play">▶</button>
    `;
    card.querySelector(".card-play").addEventListener("click", (e) => {
      e.stopPropagation();
      if (song) playSong(trackUrl(song));
    });
    host.appendChild(card);
  });
}

function renderChips() {
  const host = $("#mood-chips");
  host.innerHTML = "";
  CHIPS.forEach((c) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip" + (state.chip === c ? " active" : "");
    b.textContent = c;
    b.addEventListener("click", () => {
      state.chip = c;
      renderChips();
      renderHomeSections();
    });
    host.appendChild(b);
  });
}

function renderRecent() {
  const host = $("#recent-tracks");
  const songs = state.recent
    .map((id) => state.catalog.find((s) => s.id === id))
    .filter(Boolean)
    .map(trackUrl);
  if (!songs.length) {
    host.innerHTML = `<p class="muted" style="padding:1rem">Play a track to fill recently played.</p>`;
    return;
  }
  renderTrackTable(host, songs);
}

function renderHomeSections() {
  const base = filteredSongs();
  const trending = [...state.catalog].sort((a, b) => b.popularity - a.popularity).slice(0, 5);
  const newest = [...state.catalog].sort((a, b) => b.id - a.id).slice(0, 4);
  renderTrackTable($("#trending-tracks"), trending);
  const rel = $("#new-releases");
  rel.innerHTML = "";
  newest.forEach((s) => {
    const card = document.createElement("article");
    card.className = "mix-card art-jazz";
    card.style.minHeight = "120px";
    card.innerHTML = `<h4>${s.title}</h4><p class="muted">${s.artist}</p>
      <button type="button" class="card-play">▶</button>`;
    card.querySelector(".card-play").addEventListener("click", () => playSong(trackUrl(s)));
    rel.appendChild(card);
  });
  if (base.length !== state.catalog.length) {
    renderTrackTable($("#trending-tracks"), base.slice(0, 6));
  }
}

function renderGenres() {
  const host = $("#genres-grid");
  const genres = [...new Set(state.catalog.map((s) => s.genre))];
  host.innerHTML = "";
  genres.forEach((g) => {
    const card = document.createElement("article");
    card.className = "mix-card art-ocean";
    card.innerHTML = `<h4>${g}</h4><p>Browse ${g} tracks</p>
      <button type="button" class="card-play">▶</button>`;
    card.querySelector(".card-play").addEventListener("click", () => {
      const s = state.catalog.find((x) => x.genre === g);
      if (s) playSong(trackUrl(s));
    });
    host.appendChild(card);
  });
}

function renderArtists() {
  const host = $("#artists-grid");
  const artists = [...new Set(state.catalog.map((s) => s.artist))];
  host.innerHTML = "";
  artists.forEach((a) => {
    const card = document.createElement("article");
    card.className = "artist-card";
    card.innerHTML = `<div class="artist-av"></div><strong>${a}</strong>`;
    card.addEventListener("click", () => {
      const s = state.catalog.find((x) => x.artist === a);
      if (s) playSong(trackUrl(s));
    });
    host.appendChild(card);
  });
}

function renderLibrary() {
  const host = $("#library-list");
  if (!state.playlist.length) {
    host.innerHTML = `<p class="muted" style="padding:1rem">Approve tracks in Discover to build your library.</p>`;
    return;
  }
  renderTrackTable(
    host,
    state.playlist.map((t) => ({ ...t, artist: t.artist || "JS Studio", duration_label: "0:22" }))
  );
}

function renderFavorites() {
  const host = $("#favorites-list");
  const songs = state.favorites.map((id) => state.catalog.find((s) => s.id === id)).filter(Boolean);
  if (!songs.length) {
    host.innerHTML = `<p class="muted" style="padding:1rem">Tap ♡ on any track to save favorites.</p>`;
    return;
  }
  renderTrackTable(host, songs);
}

function updatePlayerUI() {
  const t = state.current;
  $("#pb-title").textContent = t?.title || "—";
  $("#pb-artist").textContent = t ? `${t.artist} · JS Studio` : "Select a track";
  $("#pb-art").style.background = t
    ? "linear-gradient(135deg, var(--lime), #3a4020)"
    : "var(--card)";
  const btn = $("#btn-play");
  const st = player.getState();
  if (btn) btn.textContent = st.paused ? "▶" : "⏸";
  updatePlayerFav();
}

function updatePlayerFav() {
  const btn = $("#pb-fav");
  if (!btn || !state.current) return;
  btn.textContent = isFav(state.current.id) ? "♥" : "♡";
}

function syncProgress() {
  const st = player.getState();
  $("#time-cur").textContent = fmtTime(st.current);
  $("#time-end").textContent = fmtTime(st.duration);
  const seek = $("#seek");
  if (seek && st.duration) seek.value = String(Math.round((st.current / st.duration) * 1000));
  const btn = $("#btn-play");
  if (btn) btn.textContent = st.paused ? "▶" : "⏸";
}

async function playSong(song) {
  state.current = song;
  state.queue = filteredSongs().length ? filteredSongs().map(trackUrl) : state.catalog.map(trackUrl);
  state.queueIndex = state.queue.findIndex((s) => s.id === song.id);
  if (state.queueIndex < 0) state.queueIndex = 0;
  pushRecent(song);
  await player.playTrack(song);
  updatePlayerUI();
  $$(".track-row").forEach((r) => r.classList.remove("playing"));
}

function playNext(delta) {
  if (!state.queue.length) return;
  state.queueIndex = (state.queueIndex + delta + state.queue.length) % state.queue.length;
  playSong(state.queue[state.queueIndex]);
}

function switchView(view) {
  $$(".panel").forEach((p) => p.classList.remove("active"));
  $$("[data-view]").forEach((b) => b.classList.remove("active"));
  $(`#view-${view}`)?.classList.add("active");
  $$(`[data-view="${view}"]`).forEach((b) => b.classList.add("active"));
  const meta = PAGE_META[view] || PAGE_META.home;
  $("#page-title").textContent = meta.title;
  $("#page-eyebrow").textContent = meta.eyebrow;
  if (view === "genres") renderGenres();
  if (view === "artists") renderArtists();
  if (view === "library") renderLibrary();
  if (view === "favorites") renderFavorites();
}

async function loadCatalog() {
  const data = await api("/api/catalog");
  state.catalog = data.songs || [];
  state.queue = state.catalog.map(trackUrl);
  renderFeatured();
  renderChips();
  renderRecent();
  renderHomeSections();
  renderFavorites();
  const pl = $("#sidebar-playlists");
  pl.innerHTML = ["Night Drive", "Slow Sundays", "Good Energy", "My first mix"]
    .map((n) => `<li>${n}</li>`)
    .join("");
}

async function refreshPlaylist() {
  const data = await api("/api/playlist");
  state.playlist = data.tracks || [];
  renderLibrary();
}

function renderRecs(list) {
  const host = $("#rec-list");
  host.innerHTML = "";
  list.forEach((t) => {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `<h4>${t.title}</h4><p class="muted">${t.artist}</p><p>${t.explanation}</p>`;
    card.addEventListener("click", () => playSong({ ...t, stream_url: t.stream_url }));
    host.appendChild(card);
  });
}

async function discover() {
  $("#discover-btn").disabled = true;
  try {
    const body = {
      query: $("#query").value.trim(),
      genre: $("#genre").value,
      mood: $("#mood").value,
      energy: parseFloat($("#energy").value),
      likes_acoustic: $("#acoustic").checked,
      focus_mode: true,
      k: 5,
    };
    const data = await api("/api/discover", { method: "POST", body: JSON.stringify(body) });
    state.proposalId = data.proposal_id;
    renderRecs(data.recommendations || []);
    $("#plan-steps").textContent = (data.plan_steps || []).join(" → ");
    $("#proposal-note").textContent = data.narrative || "";
    $("#rag-snips").innerHTML = (data.rag_chunks || [])
      .map((c) => `<li><strong>${c.id}</strong>: ${c.snippet}</li>`)
      .join("");
    $("#hitl-panel").hidden = false;
  } catch (err) {
    alert(err.message);
  } finally {
    $("#discover-btn").disabled = false;
  }
}

async function approveProposal(ok) {
  if (!state.proposalId) return;
  const path = ok ? "/api/playlist/approve" : "/api/playlist/reject";
  await api(path, { method: "POST", body: JSON.stringify({ proposal_id: state.proposalId }) });
  await refreshPlaylist();
  $("#hitl-panel").hidden = ok;
}

function initPlayer() {
  player.setPlayerCallbacks({
    onTick: syncProgress,
    onEnded: () => playNext(1),
  });
  $("#btn-play")?.addEventListener("click", () => {
    if (!state.current && state.catalog[0]) playSong(trackUrl(state.catalog[0]));
    else {
      player.togglePlay();
      syncProgress();
    }
  });
  $("#btn-prev")?.addEventListener("click", () => playNext(-1));
  $("#btn-next")?.addEventListener("click", () => playNext(1));
  $("#seek")?.addEventListener("input", (e) => {
    player.seek(Number(e.target.value) / 1000);
  });
  $("#volume")?.addEventListener("input", (e) => {
    player.setVolume(Number(e.target.value) / 100);
  });
  $("#pb-fav")?.addEventListener("click", () => {
    if (state.current) toggleFav(state.current.id);
  });
  $("#hero-play")?.addEventListener("click", () => {
    const mix = [...state.catalog].sort((a, b) => b.popularity - a.popularity).slice(0, 5).map(trackUrl);
    state.queue = mix;
    if (mix[0]) playSong(mix[0]);
  });
}

function initNav() {
  $$("[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });
  $$("[data-goto]").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.goto));
  });
}

$("#search")?.addEventListener("input", (e) => {
  state.filter = e.target.value;
  renderHomeSections();
});
$("#discover-btn")?.addEventListener("click", discover);
$("#approve-btn")?.addEventListener("click", () => approveProposal(true));
$("#reject-btn")?.addEventListener("click", () => approveProposal(false));

player.setVolume(0.8);
initPlayer();
initNav();
loadCatalog().catch(() => {
  $("#content").insertAdjacentHTML(
    "beforeend",
    `<p class="muted">Start server: <code>python -m src.server</code> then open http://127.0.0.1:8790</p>`
  );
});
refreshPlaylist();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});