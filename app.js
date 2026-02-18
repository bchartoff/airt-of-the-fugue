'use strict';

// ─────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────
const PLAYHEAD_X = 200;     // px from left edge to playhead line
const NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const PADDING_SEMITONES = 2; // extra semitones above/below each voice range

// Sequential palette for the 8 subject positions.
// RColorBrewer "YlOrRd" 8-class: light yellow → deep red.
// Encodes how far through the subject a note is (pos 0 = early/bright, pos 7 = late/deep).
const SUBJECT_COLORS = [
  '#ffffcc', // pos 0
  '#ffeda0', // pos 1
  '#fed976', // pos 2
  '#feb24c', // pos 3
  '#fd8d3c', // pos 4
  '#fc4e2a', // pos 5
  '#e31a1c', // pos 6
  '#800026', // pos 7
];

// Cool palette for the secondary subject (C IX descending-scale theme).
// RColorBrewer "YlGnBu" 9-class: light yellow-green → deep blue.
const SUBJECT2_COLORS = [
  '#ffffd9', // pos 0
  '#edf8b1', // pos 1
  '#c7e9b4', // pos 2
  '#7fcdbb', // pos 3
  '#41b6c4', // pos 4
  '#1d91c0', // pos 5
  '#225ea8', // pos 6
  '#253494', // pos 7
  '#081d58', // pos 8 (9-note subject has 9 positions)
];

const FUZZY_COLOR = '#999999'; // grey for untagged / fuzzy-only notes

// Parse a hex color to [r,g,b] 0-255
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b];
}

// Interpolate between two hex colors by fraction t (0-1)
function lerpColor(hexA, hexB, t) {
  const [r1, g1, b1] = hexToRgb(hexA);
  const [r2, g2, b2] = hexToRgb(hexB);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
}

// Organ-style synth config:
// - sawtooth4 = sawtooth wave with 4 harmonics (warm, principal-pipe character)
// - flat envelope: instant on, full sustain, fast release (no piano decay)
const SYNTH_CONFIG = {
  oscillator: { type: 'sawtooth4' },
  envelope: { attack: 0.01, decay: 0.0, sustain: 1.0, release: 0.08 },
};

// Shared FX chain (created once, reused across piece loads)
let organReverb = null;
let organFilter = null;
let organChorus = null;

function getOrganFX() {
  if (!organReverb) {
    organReverb = new Tone.Reverb({ decay: 4.5, preDelay: 0.04, wet: 0.38 });
    organReverb.toDestination();
  }
  if (!organFilter) {
    // Low-pass at 2200Hz rolls off high harmonics — mimics pipe resonance
    organFilter = new Tone.Filter({ frequency: 2200, type: 'lowpass', rolloff: -24 });
    organFilter.connect(organReverb);
  }
  if (!organChorus) {
    // Subtle chorus for pipe-organ "ensemble" shimmer
    organChorus = new Tone.Chorus({ frequency: 1.2, delayTime: 3.5, depth: 0.15, wet: 0.25 }).start();
    organChorus.connect(organFilter);
  }
  return organChorus;
}

// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────
let data = null;
let synths = [];
let isPlaying = false;
let rafId = null;
let pxPerSec = 24;

// Active note tracking
let activeNoteIndices = new Set();
let nextNoteIdx = 0;

// Always in theme mode
const themeMode = true;

// Per-lane data: { voiceId, canvas, ctx, dpr, w, h, pitchMin, pitchMax, pitchRange, noteH, notes[] }
let lanes = [];


// DOM refs
let timeDisplay, tooltip, progressBarFill, progressBarContainer;
let mutedVoices = new Set();

// Info panel state
let infoPanelOpen = false;

// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────
function midiToFreq(pitch) {
  return 440 * Math.pow(2, (pitch - 69) / 12);
}

function pitchName(midi) {
  const octave = Math.floor(midi / 12) - 1;
  return NOTE_NAMES[midi % 12] + octave;
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function hexToRgba(hex, alpha) {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${alpha})`;
}

function getScrollX(t) {
  return Math.max(0, t * pxPerSec - PLAYHEAD_X);
}

// ─────────────────────────────────────────────
// LANE SETUP
// ─────────────────────────────────────────────
function buildLanes() {
  lanes = [];
  const lanesEl = document.getElementById('lanes');

  // Rebuild lane divs to match the number of voices in this piece
  lanesEl.innerHTML = '';
  data.voices.forEach(voice => {
    const div = document.createElement('div');
    div.className = 'lane';
    div.dataset.voice = voice.id;
    div.innerHTML = `<div class="lane-label">${voice.name}</div><canvas class="lane-canvas"></canvas>`;
    lanesEl.appendChild(div);
  });

  document.querySelectorAll('.lane').forEach(div => {
    const voiceId = parseInt(div.dataset.voice, 10);
    const canvas = div.querySelector('.lane-canvas');
    const ctx = canvas.getContext('2d');
    const voice = data.voices[voiceId];

    const pitchMin = voice.pitch_min - PADDING_SEMITONES;
    const pitchMax = voice.pitch_max + PADDING_SEMITONES;
    const pitchRange = pitchMax - pitchMin;

    const voiceNotes = data.notes
      .map((n, idx) => ({ ...n, _globalIdx: idx }))
      .filter(n => n.voice === voiceId);

    lanes.push({
      voiceId, div, canvas, ctx,
      dpr: 1, w: 0, h: 0,
      pitchMin, pitchMax, pitchRange,
      noteH: 0,
      notes: voiceNotes,
      color: voice.color,
      name: voice.name,
    });
  });
}

function sizeLanes() {
  const dpr = window.devicePixelRatio || 1;

  lanes.forEach(lane => {
    const w = lane.div.clientWidth;
    const h = lane.div.clientHeight;

    lane.dpr = dpr;
    lane.w = w;
    lane.h = h;
    lane.noteH = h / lane.pitchRange;

    lane.canvas.width = w * dpr;
    lane.canvas.height = h * dpr;
    lane.canvas.style.width = w + 'px';
    lane.canvas.style.height = h + 'px';

    lane.ctx.setTransform(1, 0, 0, 1, 0, 0);
    lane.ctx.scale(dpr, dpr);
  });
}

// ─────────────────────────────────────────────
// DRAWING
// ─────────────────────────────────────────────
function noteRectInLane(note, lane) {
  const x = note.start * pxPerSec;
  const y = (lane.pitchMax - note.pitch - 1) * lane.noteH;
  const w = Math.max(2, note.duration * pxPerSec - 1);
  const h = Math.max(2, lane.noteH - 1);
  return { x, y, w, h };
}

// Return the definite palette color for a tagged note (subject/head/tail family).
// Returns null for fuzzy/untagged notes.
function getMotifColor(note) {
  if (!note.motif) return null;
  const pos = note.motif_pos >= 0 ? note.motif_pos : (note.best_pos ?? 0);
  if (note.motif === 'subject2') {
    return SUBJECT2_COLORS[Math.min(pos, 8)];
  }
  return SUBJECT_COLORS[Math.min(pos, 7)];
}

// Return color for a note, with grace-note tweening.
// voiceNotes: sorted array of all notes in this voice (for neighbor lookup).
// noteIdx: index of this note within voiceNotes.
function getNoteColor(note, voiceNotes, noteIdx) {
  if (!themeMode) {
    const lane = lanes.find(l => l.voiceId === note.voice);
    return lane ? lane.color : '#888';
  }

  // Tagged note → exact palette color
  const own = getMotifColor(note);
  if (own) return own;

  // Untagged note — color by fuzzy similarity score.
  // Every note has best_pos (0–7, which subject position it resembles)
  // and similarity (0.0–1.0, how confident the match is).
  // Blend the palette color for best_pos with grey based on similarity.
  const sim = note.similarity != null ? note.similarity : 0;
  const pos = note.best_pos != null ? note.best_pos : 0;
  const paletteColor = SUBJECT_COLORS[Math.min(pos, 7)];
  // similarity drives how much palette color shows through vs grey
  return lerpColor(FUZZY_COLOR, paletteColor, sim);
}

function drawFrame(t) {
  const scrollX = getScrollX(t);

  lanes.forEach(lane => {
    drawLane(lane, t, scrollX);
  });

  // Keep info panel in sync even when paused
  buildInfoPanel();
}

function drawLane(lane, t, scrollX) {
  const { ctx, w, h, notes } = lane;

  ctx.clearRect(0, 0, w, h);

  ctx.save();
  ctx.translate(-scrollX, 0);

  // Pre-compute color for every note (needs neighbor context for tweening)
  const noteColors = notes.map((n, i) => getNoteColor(n, notes, i));
  const isFuzzy = notes.map(n => !n.motif);

  // Background — tinted by active note if it's a tagged note
  let bgColor = '#ffffff';
  let activeNote = null;
  let activeNoteIdx = -1;
  for (let i = 0; i < notes.length; i++) {
    const n = notes[i];
    if (activeNoteIndices.has(n._globalIdx)) {
      if (!isFuzzy[i]) {
        bgColor = hexToRgba(noteColors[i], 1.0);
      }
      if (!activeNote) { activeNote = n; activeNoteIdx = i; }
    }
  }
  ctx.fillStyle = bgColor;
  ctx.fillRect(scrollX, 0, w, h);

  // Grid
  drawLaneGrid(lane, scrollX);

  // Notes — pass 1: all notes
  // Tagged notes: full opaque color. Fuzzy/grey notes: muted alpha.
  for (let i = 0; i < notes.length; i++) {
    const n = notes[i];
    const r = noteRectInLane(n, lane);
    if (r.x + r.w < scrollX || r.x > scrollX + w) continue;

    const color = noteColors[i];
    // Tagged notes: bold. Untagged: alpha scales with similarity (0.22 → 0.65).
    const sim = n.similarity != null ? n.similarity : 0;
    const alpha = isFuzzy[i] ? (0.22 + 0.43 * sim) : 0.85;
    ctx.fillStyle = hexToRgba(color, alpha);
    ctx.fillRect(r.x, r.y, r.w, r.h);
  }

  // Notes — pass 2: active notes with glow (only tagged notes get full glow)
  for (let i = 0; i < notes.length; i++) {
    const n = notes[i];
    if (!activeNoteIndices.has(n._globalIdx)) continue;
    const r = noteRectInLane(n, lane);
    const color = noteColors[i];

    if (!isFuzzy[i]) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
    }
    ctx.fillStyle = hexToRgba(color, isFuzzy[i] ? 0.35 : 1.0);
    ctx.fillRect(r.x, r.y, r.w, r.h);
    ctx.shadowBlur = 0;
  }

  // ── Measure number labels ──
  drawMeasureLabels(lane, scrollX);

  // ── Subject entry markers (▼ triangle at top of lane) ──
  drawSubjectMarkers(lane, scrollX);

  // Playhead
  const px = scrollX + PLAYHEAD_X;
  ctx.beginPath();
  ctx.moveTo(px, 0);
  ctx.lineTo(px, h);
  ctx.strokeStyle = 'rgba(0,0,0,0.4)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.restore();

  // ── Large note + interval overlay (screen-space, not scrolled) ──
  if (activeNote) {
    drawNoteOverlay(lane, activeNote, activeNoteIdx, notes, t);
  }
}

function getNoteMotifLabel(note) {
  const m = note.motif;
  const pos = note.motif_pos >= 0 ? note.motif_pos : note.best_pos;
  const sim = note.similarity != null ? note.similarity : 0;
  const pct = Math.round(sim * 100);

  if (m === 'subject') {
    return { prefix: '★', label: `subject  ${pos + 1}/8` };
  } else if (m === 'subject_inv') {
    return { prefix: '☆', label: `inv. subject  ${pos + 1}/8` };
  } else if (m === 'tail') {
    return { prefix: '~', label: `tail  ${pos - 2}/5` };
  } else if (m === 'tail_inv') {
    return { prefix: '↕', label: `inv. tail  ${pos - 2}/5` };
  } else if (m === 'head') {
    return { prefix: '↗', label: `head  ${pos + 1}/5` };
  } else if (m === 'head_inv') {
    return { prefix: '↙', label: `inv. head  ${pos + 1}/5` };
  } else if (m === 'subject2') {
    return { prefix: '♦', label: `2nd subject  ${pos + 1}/9` };
  } else {
    return { prefix: '≈', label: `pos ${pos + 1}/8  ${pct}%` };
  }
}

function drawNoteOverlay(lane, note, noteIdx, voiceNotes, t) {
  const { ctx, w, h } = lane;

  const color = getNoteColor(note, voiceNotes, noteIdx);
  const isFuzzyNote = !note.motif;
  const name = pitchName(note.pitch);
  const { prefix, label } = getNoteMotifLabel(note);

  // When info panel is open, pull the overlay left so it stays visible
  const INFO_PANEL_W = 360;
  const PAD_RIGHT = infoPanelOpen ? INFO_PANEL_W + 16 : 16;

  const noteFontSize = Math.floor(h * 0.55);
  const labelFontSize = Math.floor(h * 0.22);

  ctx.save();
  ctx.textAlign = 'right';
  ctx.textBaseline = 'alphabetic';
  ctx.shadowColor = 'rgba(0,0,0,0.5)';
  ctx.shadowBlur = 8;

  // Vertically center the two-line block
  const noteAscent = noteFontSize * 0.75;
  const labelAscent = labelFontSize * 0.75;
  const gap = Math.floor(h * 0.04);
  const totalH = noteAscent + gap + labelAscent;
  const blockTop = (h - totalH) / 2;
  const noteBaseline = blockTop + noteAscent;
  const labelBaseline = noteBaseline + gap + labelAscent;

  // Fuzzy notes: grey and dimmer. Tagged: full color.
  const nameColor = isFuzzyNote ? 'rgba(160,160,160,0.7)' : color;
  const labelColor = isFuzzyNote ? 'rgba(140,140,140,0.5)' : hexToRgba(color, 0.85);

  ctx.font = `700 ${noteFontSize}px 'Helvetica Neue', Helvetica, Arial, sans-serif`;
  ctx.fillStyle = nameColor;
  ctx.fillText(name, w - PAD_RIGHT, noteBaseline);

  ctx.font = `500 ${labelFontSize}px 'Helvetica Neue', Helvetica, Arial, sans-serif`;
  ctx.fillStyle = labelColor;
  ctx.fillText(`${prefix} ${label}`, w - PAD_RIGHT, labelBaseline);

  ctx.restore();
}

function drawLaneGrid(lane, scrollX) {
  const { ctx, w, h, pitchMin, pitchMax, noteH } = lane;

  // Horizontal lines at C notes
  for (let pitch = pitchMin; pitch <= pitchMax; pitch++) {
    if (pitch % 12 !== 0) continue;
    const y = (pitchMax - pitch) * noteH;
    ctx.beginPath();
    ctx.moveTo(scrollX, y);
    ctx.lineTo(scrollX + w, y);
    ctx.strokeStyle = pitch === 60 ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.08)';
    ctx.lineWidth = pitch === 60 ? 1 : 0.5;
    ctx.stroke();
  }

  // Vertical bar lines
  const secPerMeasure = 2.0;
  const totalMeasures = data ? data.metadata.total_measures : 80;

  for (let m = 0; m <= totalMeasures; m++) {
    const x = m * secPerMeasure * pxPerSec;
    if (x < scrollX - 10 || x > scrollX + w + 10) continue;

    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.strokeStyle = m % 4 === 0 ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)';
    ctx.lineWidth = m % 4 === 0 ? 1 : 0.5;
    ctx.stroke();
  }
}

function drawMeasureLabels(lane, scrollX) {
  const { ctx, w, h } = lane;
  const secPerMeasure = 2.0;
  const totalMeasures = data ? data.metadata.total_measures : 80;
  const fontSize = Math.max(9, Math.min(12, h * 0.12));

  ctx.font = `400 ${fontSize}px 'Helvetica Neue', Helvetica, Arial, sans-serif`;
  ctx.fillStyle = 'rgba(0,0,0,0.28)';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';

  for (let m = 1; m <= totalMeasures; m++) {
    if (m % 4 !== 1) continue; // label every 4 measures
    const x = m * secPerMeasure * pxPerSec;
    if (x < scrollX - 40 || x > scrollX + w + 40) continue;
    ctx.fillText(m, x + 3, h - 3);
  }
}

function drawSubjectMarkers(lane, scrollX) {
  const { ctx, w, h, notes } = lane;
  const size = Math.max(6, Math.min(10, h * 0.12));

  for (const n of notes) {
    if ((n.motif !== 'subject' && n.motif !== 'subject_inv' && n.motif !== 'subject2') || n.motif_pos !== 0) continue;
    const x = n.start * pxPerSec;
    if (x < scrollX - size || x > scrollX + w + size) continue;

    // Marker color: warm for main subject, cool for secondary
    const color = n.motif === 'subject2' ? '#081d58'
               : n.motif === 'subject_inv' ? '#444488' : '#800026';

    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.3)';
    ctx.shadowBlur = 3;
    ctx.fillStyle = color;
    // Downward-pointing triangle at top of lane
    ctx.beginPath();
    ctx.moveTo(x - size / 2, 0);
    ctx.lineTo(x + size / 2, 0);
    ctx.lineTo(x, size);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }
}

// ─────────────────────────────────────────────
// ACTIVE NOTE TRACKING
// ─────────────────────────────────────────────
function resetActiveNotes(fromTime = 0) {
  activeNoteIndices.clear();
  let lo = 0, hi = data.notes.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (data.notes[mid].start < fromTime) lo = mid + 1;
    else hi = mid;
  }
  nextNoteIdx = lo;
}

function updateActiveNotes(t) {
  while (nextNoteIdx < data.notes.length && data.notes[nextNoteIdx].start <= t) {
    activeNoteIndices.add(nextNoteIdx);
    nextNoteIdx++;
  }
  for (const idx of activeNoteIndices) {
    const n = data.notes[idx];
    if (t >= n.start + n.duration + 0.05) {
      activeNoteIndices.delete(idx);
    }
  }
}

// ─────────────────────────────────────────────
// TONE.JS AUDIO
// ─────────────────────────────────────────────
function createSynths() {
  const fx = getOrganFX();
  // Slight volume shaping by register (bass a touch louder, soprano softer)
  const voiceVolumes = [-10, -11, -11, -9]; // soprano, alto, tenor, bass
  synths = data.voices.map((v, i) => {
    const s = new Tone.PolySynth(Tone.Synth, SYNTH_CONFIG);
    s.volume.value = voiceVolumes[i] !== undefined ? voiceVolumes[i] : -10;
    s.connect(fx);
    return s;
  });
}

function scheduleAllNotes(fromTime = 0) {
  Tone.Transport.cancel(fromTime);

  for (const note of data.notes) {
    if (note.start + note.duration < fromTime) continue;

    const synth = synths[note.voice];
    const freq = midiToFreq(note.pitch);
    const dur = Math.max(0.05, note.duration);
    const startTime = Math.max(0, note.start);

    Tone.Transport.schedule((audioTime) => {
      if (!mutedVoices.has(note.voice)) {
        synth.triggerAttackRelease(freq, dur, audioTime);
      }
    }, startTime);
  }
}

// ─────────────────────────────────────────────
// ANIMATION LOOP
// ─────────────────────────────────────────────
function startLoop() {
  function frame() {
    const t = Tone.Transport.seconds;
    updateActiveNotes(t);
    drawFrame(t);

    const totalDur = data.metadata.total_duration_seconds;
    timeDisplay.textContent = formatTime(t) + ' / ' + formatTime(totalDur);

    // Update progress bar
    if (progressBarFill && totalDur > 0) {
      progressBarFill.style.width = Math.min(100, (t / totalDur) * 100) + '%';
    }

    // Update info panel (live, ~60fps)
    buildInfoPanel();

    if (t >= totalDur) {
      stopPlayback();
      // Autoplay next piece after a brief pause
      const nextIdx = currentPieceIdx + 1;
      if (nextIdx < pieces.length) {
        setTimeout(() => loadPiece(nextIdx, true), 1200);
      }
      return;
    }

    rafId = requestAnimationFrame(frame);
  }
  rafId = requestAnimationFrame(frame);
}

function stopLoop() {
  if (rafId) {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
}

// ─────────────────────────────────────────────
// PLAYBACK CONTROLS
// ─────────────────────────────────────────────
async function startPlayback() {
  await Tone.start();
  // Ensure reverb IR is generated before playback begins
  if (organReverb) await organReverb.ready;
  resetActiveNotes(0);
  Tone.Transport.stop();
  Tone.Transport.seconds = 0;
  scheduleAllNotes(0);
  Tone.Transport.start();
  isPlaying = true;
  startLoop();
  document.getElementById('btn-play').textContent = '\u23F8';
}

function stopPlayback() {
  Tone.Transport.stop();
  Tone.Transport.cancel();
  stopLoop();
  isPlaying = false;
  resetActiveNotes(0);
  drawFrame(0);
  timeDisplay.textContent = '0:00 / ' + formatTime(data.metadata.total_duration_seconds);
  document.getElementById('btn-play').textContent = '\u25B6';
}

async function togglePlay() {
  if (!isPlaying) {
    if (Tone.Transport.state === 'paused') {
      await Tone.start();
      Tone.Transport.start();
      isPlaying = true;
      startLoop();
      document.getElementById('btn-play').textContent = '\u23F8';
    } else {
      await startPlayback();
    }
  } else {
    Tone.Transport.pause();
    stopLoop();
    isPlaying = false;
    document.getElementById('btn-play').textContent = '\u25B6';
  }
}

// ─────────────────────────────────────────────
// CLICK HANDLING — SEEK + TOOLTIP
// ─────────────────────────────────────────────
function handleLaneClick(e, lane) {
  if (!data) return;

  const rect = lane.canvas.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const clickY = e.clientY - rect.top;

  const t = Tone.Transport.seconds;
  const scrollX = getScrollX(t);
  const worldX = clickX + scrollX;
  const clickTime = worldX / pxPerSec;

  if (clickTime < 0 || clickTime > data.metadata.total_duration_seconds) return;

  // Check for note hit
  const hitNote = findNoteInLane(worldX, clickY, lane);
  if (hitNote) {
    showTooltip(e.clientX, e.clientY, hitNote);
    return;
  }

  // Seek
  const wasPlaying = isPlaying;
  if (isPlaying) {
    Tone.Transport.pause();
    stopLoop();
    isPlaying = false;
  }

  Tone.Transport.cancel();
  Tone.Transport.seconds = clickTime;
  resetActiveNotes(clickTime);
  drawFrame(clickTime);

  if (wasPlaying) {
    scheduleAllNotes(clickTime);
    Tone.Transport.start();
    isPlaying = true;
    startLoop();
    document.getElementById('btn-play').textContent = '\u23F8';
  }
}

function findNoteInLane(worldX, localY, lane) {
  for (const n of lane.notes) {
    const r = noteRectInLane(n, lane);
    if (worldX >= r.x && worldX <= r.x + r.w &&
        localY >= r.y && localY <= r.y + r.h) {
      return n;
    }
  }
  return null;
}

function getSectionAt(t) {
  if (!data || !data.sections) return null;
  return data.sections.find(s => t >= s.start && t < s.end) || null;
}

function showTooltip(clientX, clientY, note) {
  const voice = data.voices[note.voice];
  let motifLine = '';
  const m = note.motif;
  if (m === 'subject') {
    motifLine = `\u2605 Subject note ${note.motif_pos + 1}/8<br>`;
  } else if (m === 'subject_inv') {
    motifLine = `\u2606 Inv. subject note ${note.motif_pos + 1}/8<br>`;
  } else if (m === 'tail') {
    motifLine = `\u223C Tail fragment (subject pos ${note.motif_pos + 1}/8)<br>`;
  } else if (m === 'tail_inv') {
    motifLine = `\u2922 Inverted tail note ${note.motif_pos + 1}/5<br>`;
  } else if (m === 'head') {
    motifLine = `\u2197 Head fragment note ${note.motif_pos + 1}/5<br>`;
  } else if (m === 'head_inv') {
    motifLine = `\u2199 Inv. head fragment note ${note.motif_pos + 1}/5<br>`;
  } else if (note.best_pos != null) {
    const sim = note.similarity != null ? note.similarity : 0;
    const pct = Math.round(sim * 100);
    motifLine = `\u223D Resembles subject pos ${note.best_pos + 1}/8 (${pct}%)<br>`;
  }
  const sec = getSectionAt(note.start);
  const sectionLine = sec
    ? `<span style="color:${sec.color}">\u25A0</span> ${sec.label}<br>`
    : '';
  tooltip.innerHTML =
    `<strong>${voice.name}</strong><br>` +
    `Note: ${pitchName(note.pitch)} (MIDI ${note.pitch})<br>` +
    `Measure ${note.measure}, beat ${note.beat.toFixed(1)}<br>` +
    motifLine +
    sectionLine +
    `Duration: ${note.duration.toFixed(3)}s`;
  tooltip.style.left = (clientX + 12) + 'px';
  tooltip.style.top = (clientY - 10) + 'px';
  tooltip.hidden = false;

  setTimeout(() => { tooltip.hidden = true; }, 2500);
}

// ─────────────────────────────────────────────
// INFO PANEL
// ─────────────────────────────────────────────

// The subject notes at each position, for both forms:
const SUBJECT_NOTES_SUBJ = ['D', 'A', 'F', 'D', 'C#', 'D', 'E', 'F'];
const SUBJECT_NOTES_ANS  = ['A', 'D', 'C', 'A', 'G#', 'A', 'B', 'C'];
const SUBJECT_INTERVALS_DISPLAY = ['+7 (P5↑)', '−4 (M3↓)', '−3 (m3↓)', '−1 (m2↓)', '+1 (m2↑)', '+2 (M2↑)', '+1 (m2↑)'];
const ANSWER_INTERVALS_DISPLAY  = ['+5 (P4↑)', '−2 (M2↓)', '−3 (m3↓)', '−1 (m2↓)', '+1 (m2↑)', '+2 (M2↑)', '+1 (m2↑)'];
const MOTIF_NAMES = {
  subject:     { icon: '★', label: 'Subject / answer entry',      desc: 'Exact 8-note interval match: +7,−4,−3,−1,+1,+2,+1 (rectus) or +5,−2,−3,−1,+1,+2,+1 (answer). Transposition-invariant — caught at any pitch level.' },
  subject_inv: { icon: '☆', label: 'Inverted subject entry',      desc: 'Subject played upside-down: −7,+4,+3,+1,−1,−2,−1 (inv. rectus) or −5,+2,+3,+1,−1,−2,−1 (inv. answer). Transposition-invariant.' },
  tail:        { icon: '~', label: 'Tail fragment',                desc: 'Last 5 notes of subject (intervals: −1,+1,+2,+1). Tagged only when no full-subject overlap exists.' },
  tail_inv:    { icon: '↕', label: 'Inverted tail fragment',      desc: 'Tail played upside-down (intervals: +1,−1,−2,−1). Classic stretto and augmentation device.' },
  head:        { icon: '↗', label: 'Head fragment',               desc: 'First 5 notes of subject (+7,−4,−3,−1) or answer (+5,−2,−3,−1). Transposition-invariant.' },
  head_inv:    { icon: '↙', label: 'Inverted head fragment',      desc: 'Head played upside-down (−7,+4,+3,+1 or −5,+2,+3,+1). Transposition-invariant.' },
  subject2:    { icon: '♦', label: 'Secondary subject (C IX)',    desc: 'Descending-scale countersubject: octave leap up, then stepwise descent over an octave. Unique to Contrapunctus IX.' },
  '':          { icon: '≈', label: 'Fuzzy match only',            desc: 'Not part of any recognized motif. Color and opacity driven purely by similarity score from local interval context.' },
};

const INTERVAL_NAMES = {
  0: 'unison', 1: 'm2', 2: 'M2', 3: 'm3', 4: 'M3', 5: 'P4',
  6: 'tritone', 7: 'P5', 8: 'm6', 9: 'M6', 10: 'm7', 11: 'M7', 12: 'P8',
};

function intervalName(semitones) {
  const abs = Math.abs(semitones);
  const name = INTERVAL_NAMES[abs] || `${abs} st`;
  return semitones >= 0 ? `+${semitones} (${name}↑)` : `${semitones} (${name}↓)`;
}

function field(key, val, cls = '') {
  return `<div class="info-field"><span class="info-field-key">${key}</span><span class="info-field-val ${cls}">${val}</span></div>`;
}

function sep() {
  return '<hr class="info-section-sep">';
}

function barHtml(frac, color) {
  const pct = Math.round(frac * 100);
  return `<div class="info-bar-wrap">
    <div class="info-bar-track"><div class="info-bar-fill" style="width:${pct}%;background:${color}"></div></div>
    <span class="info-field-val" style="min-width:32px;font-size:11px">${pct}%</span>
  </div>`;
}

function buildNoteInfoHtml(note, voiceName, voiceColor) {
  if (!note) {
    return `<div class="info-voice-idle">— resting —</div>`;
  }

  const color = getMotifColor(note) || FUZZY_COLOR;
  const motif = note.motif || '';
  const motifInfo = MOTIF_NAMES[motif] || MOTIF_NAMES[''];
  const simPct = note.similarity != null ? note.similarity : 0;
  const pos = note.motif_pos >= 0 ? note.motif_pos : note.best_pos;

  // ── Section 1: Identity ──
  let html = '';
  html += field('MIDI pitch', `${note.pitch}`, '');
  html += field('Note name', `<strong style="color:${color};font-size:13px">${pitchName(note.pitch)}</strong>`, '');
  html += field('Measure / beat', `m${note.measure}, beat ${note.beat.toFixed(2)}`);
  html += field('Duration', `${note.duration.toFixed(3)} s`);
  html += field('Velocity', `${note.velocity != null ? note.velocity : 'n/a'}`);

  html += sep();

  // ── Section 2: Motif classification ──
  html += field('Motif tag', `<strong>${motifInfo.icon} ${motifInfo.label}</strong>`, 'highlight');
  html += `<div class="info-field"><span class="info-field-key"></span><span class="info-field-val dim" style="font-size:10.5px;line-height:1.4;max-width:220px;white-space:normal">${motifInfo.desc}</span></div>`;

  if (motif === 'subject' || motif === 'subject_inv') {
    const subjNote = SUBJECT_NOTES_SUBJ[pos];
    const ansNote  = SUBJECT_NOTES_ANS[pos];
    const intBefore = pos > 0 ? SUBJECT_INTERVALS_DISPLAY[pos - 1] : '—';
    const intAfter  = pos < 7 ? SUBJECT_INTERVALS_DISPLAY[pos] : '—';
    html += sep();
    html += field('Position in motif', `${pos + 1} / 8`, 'highlight');
    html += field('Matched at pitch', pitchName(note.pitch));
    if (motif === 'subject') {
      html += field('Canonical subj. note', subjNote);
      html += field('Canonical ans. note', ansNote);
      html += field('Interval before', pos > 0 ? intBefore : '— (first note)');
      html += field('Interval after',  pos < 7 ? intAfter  : '— (last note)');
    } else {
      html += field('Inverted — intervals', 'all signs negated');
      html += field('Interval before', pos > 0 ? '(negated) ' + intBefore : '— (first note)');
      html += field('Interval after',  pos < 7 ? '(negated) ' + intAfter  : '— (last note)');
    }
  } else if (motif === 'tail' || motif === 'tail_inv') {
    html += sep();
    html += field('Position in tail', `${note.motif_pos - 2} / 5`);
    html += field('Tail intervals', motif === 'tail' ? '−1, +1, +2, +1' : '+1, −1, −2, −1');
    html += field('Corresponds to', `subject pos ${note.motif_pos + 1}/8`);
  } else if (motif === 'head' || motif === 'head_inv') {
    html += sep();
    html += field('Position in head', `${note.motif_pos + 1} / 5`);
    if (motif === 'head') {
      html += field('Subject form', `+7, −4, −3, −1`);
      html += field('Answer form',  `+5, −2, −3, −1`);
    } else {
      html += field('Inv. subject form', `−7, +4, +3, +1`);
      html += field('Inv. answer form',  `−5, +2, +3, +1`);
    }
  }

  html += sep();

  // ── Section 3: Fuzzy similarity scoring ──
  const bp = note.best_pos != null ? note.best_pos : 0;
  html += field('Best subject pos', `${bp + 1} / 8 (${SUBJECT_NOTES_SUBJ[bp]})`);
  html += field('Similarity score', '');
  html += `<div class="info-field"><span class="info-field-key"></span><div style="flex:1;max-width:220px">${barHtml(simPct, color)}</div></div>`;
  html += `<div class="info-field"><span class="info-field-key"></span><span class="info-field-val dim" style="font-size:10.5px;white-space:normal;max-width:220px">Scored by comparing local intervals (up to 3 before & after) against each of the 8 subject positions. Weighted: nearest interval counts 4×, next 2×, farthest 1×. Normalized to 0–1.</span></div>`;

  html += sep();

  // ── Section 4: Color derivation ──
  html += field('Palette', 'RColorBrewer YlOrRd (8-class)');
  html += field('Color source', motif !== '' ? 'subject position (exact)' : 'fuzzy → grey');
  if (motif !== '') {
    html += field('Subject pos used', `${bp + 1} / 8`);
    html += field('Color assigned', `<span class="info-inline-swatch" style="background:${color};border:1px solid rgba(255,255,255,0.2)"></span><code style="color:#ddd">${color}</code>`, '');
  } else {
    html += field('Grace-note tween', 'interpolated from nearest tagged neighbors');
    html += field('Color assigned', `<span class="info-inline-swatch" style="background:${color};border:1px solid rgba(255,255,255,0.2)"></span><code style="color:#999">${color}</code>`, '');
  }
  const drawAlpha = motif !== '' ? 0.85 : 0.22;
  html += field('Draw opacity', drawAlpha.toFixed(2) + (motif !== '' ? ' (tagged → opaque)' : ' (untagged → dimmed)'));
  if (activeNoteIndices.has(note._globalIdx)) {
    html += field('Active glow', motif !== '' ? 'full color + shadow blur 10px' : 'dim, no glow', motif !== '' ? 'highlight' : 'dim');
  }

  // ── Interval context ──
  const voiceNotes = data.notes.filter(n => n.voice === note.voice);
  const idx = voiceNotes.findIndex(n => n.start === note.start && n.pitch === note.pitch);
  if (idx >= 0) {
    html += sep();
    html += field('Voice index', `note #${idx + 1} of ${voiceNotes.length}`);
    if (idx > 0) {
      const prev = voiceNotes[idx - 1];
      const int = note.pitch - prev.pitch;
      html += field('Interval from prev', intervalName(int));
      html += field('Previous note', pitchName(prev.pitch));
    } else {
      html += field('Interval from prev', '— (first note)');
    }
    if (idx < voiceNotes.length - 1) {
      const next = voiceNotes[idx + 1];
      const int = next.pitch - note.pitch;
      html += field('Interval to next', intervalName(int));
      html += field('Next note', pitchName(next.pitch));
    } else {
      html += field('Interval to next', '— (last note)');
    }
  }

  return html;
}

function buildInfoPanel() {
  if (!infoPanelOpen || !data) return;

  const body = document.getElementById('info-body');
  if (!body) return;

  const t = Tone.Transport.seconds;

  // Find active note per voice
  let html = '';
  lanes.forEach(lane => {
    const voiceColor = lane.color;
    let activeNote = null;
    for (const n of lane.notes) {
      if (activeNoteIndices.has(n._globalIdx)) {
        activeNote = n;
        break;
      }
    }
    const color = activeNote ? (getMotifColor(activeNote) || FUZZY_COLOR) : voiceColor;
    html += `<div class="info-voice">`;
    html += `<div class="info-voice-header">`;
    html += `<span class="info-voice-swatch" style="background:${color}"></span>`;
    html += `<span class="info-voice-name">${lane.name}</span>`;
    if (activeNote) {
      html += `<span class="info-voice-note" style="color:${color}">${pitchName(activeNote.pitch)}</span>`;
    }
    html += `</div>`;
    html += buildNoteInfoHtml(activeNote, lane.name, voiceColor);
    html += `</div>`;
  });

  if (!html) {
    html = '<div style="padding:16px;color:#444;font-size:12px">No data loaded yet.</div>';
  }

  // Preserve scroll position
  const scrollTop = body.scrollTop;
  body.innerHTML = html;
  body.scrollTop = scrollTop;
}

function toggleInfoPanel() {
  infoPanelOpen = !infoPanelOpen;
  const overlay = document.getElementById('info-overlay');
  const btn = document.getElementById('btn-info');
  overlay.hidden = !infoPanelOpen;
  btn.classList.toggle('active', infoPanelOpen);
  if (infoPanelOpen) buildInfoPanel();
}

// ─────────────────────────────────────────────
// WIRE LANE EVENTS (called after buildLanes)
// ─────────────────────────────────────────────
function wireLaneEvents() {
  // Reset mute state on piece switch
  mutedVoices.clear();

  lanes.forEach(lane => {
    lane.canvas.addEventListener('click', e => handleLaneClick(e, lane));
    lane.canvas.addEventListener('mousemove', () => { tooltip.hidden = true; });

    // Click the label to mute/unmute
    const label = lane.div.querySelector('.lane-label');
    label.style.cursor = 'pointer';
    // Remove old listeners by replacing the node
    const fresh = label.cloneNode(true);
    label.parentNode.replaceChild(fresh, label);
    fresh.addEventListener('click', () => {
      const muted = mutedVoices.has(lane.voiceId);
      if (muted) {
        mutedVoices.delete(lane.voiceId);
        synths[lane.voiceId].volume.value = -8;
        fresh.classList.remove('muted');
        lane.div.classList.remove('lane-muted');
      } else {
        mutedVoices.add(lane.voiceId);
        synths[lane.voiceId].volume.value = -Infinity;
        fresh.classList.add('muted');
        lane.div.classList.add('lane-muted');
      }
      drawFrame(Tone.Transport.seconds);
    });
  });
}

// ─────────────────────────────────────────────
// PIECE SWITCHING
// ─────────────────────────────────────────────
let pieces = [];
let currentPieceIdx = 0;

function loadPiece(idx, autoplay = false) {
  // Stop any playback
  if (isPlaying) {
    Tone.Transport.stop();
    Tone.Transport.cancel();
    stopLoop();
    isPlaying = false;
    document.getElementById('btn-play').textContent = '\u25B6';
  }

  // Destroy existing synths
  synths.forEach(s => s.dispose());
  synths = [];

  currentPieceIdx = idx;
  const piece = pieces[idx];

  // Update tab active state
  document.querySelectorAll('#piece-tabs button').forEach((btn, i) => {
    btn.classList.toggle('active', i === idx);
  });

  fetch(piece.file + '?v=' + Date.now())
    .then(r => {
      if (!r.ok) throw new Error('Failed to load ' + piece.file);
      return r.json();
    })
    .then(loadedData => {
      data = loadedData;
      buildLanes();
      sizeLanes();
      wireLaneEvents();
      createSynths();
      resetActiveNotes(0);
      timeDisplay.textContent = '0:00 / ' + formatTime(data.metadata.total_duration_seconds);
      // Reset progress bar
      if (progressBarFill) progressBarFill.style.width = '0%';
      // Update page title
      document.title = `AIrt of the Fugue — ${data.metadata.title.replace('The Art of the Fugue, ', '')}`;
      drawFrame(0);
      if (autoplay) startPlayback();
    })
    .catch(err => console.error(err));
}

// ─────────────────────────────────────────────
// BOOTSTRAP
// ─────────────────────────────────────────────
fetch('pieces.json')
  .then(r => {
    if (!r.ok) throw new Error('Failed to load pieces.json: ' + r.status);
    return r.json();
  })
  .then(manifest => {
    pieces = manifest;

    // Build piece tabs
    const tabsEl = document.getElementById('piece-tabs');
    pieces.forEach((p, i) => {
      const btn = document.createElement('button');
      btn.textContent = p.number;
      btn.title = p.title;
      btn.addEventListener('click', () => loadPiece(i));
      tabsEl.appendChild(btn);
    });

    // Wire up persistent controls (only need to do once)
    timeDisplay = document.getElementById('time-display');
    tooltip = document.getElementById('tooltip');
    progressBarFill = document.getElementById('progress-bar-fill');
    progressBarContainer = document.getElementById('progress-bar-container');

    // Progress bar click → seek
    progressBarContainer.addEventListener('click', e => {
      if (!data) return;
      const rect = progressBarContainer.getBoundingClientRect();
      const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const seekTo = frac * data.metadata.total_duration_seconds;
      const wasPlaying = isPlaying;
      if (isPlaying) { Tone.Transport.pause(); stopLoop(); isPlaying = false; }
      Tone.Transport.cancel();
      Tone.Transport.seconds = seekTo;
      resetActiveNotes(seekTo);
      drawFrame(seekTo);
      progressBarFill.style.width = (frac * 100) + '%';
      if (wasPlaying) {
        scheduleAllNotes(seekTo);
        Tone.Transport.start();
        isPlaying = true;
        startLoop();
        document.getElementById('btn-play').textContent = '\u23F8';
      }
    });

    document.getElementById('btn-play').addEventListener('click', togglePlay);
    document.getElementById('btn-stop').addEventListener('click', stopPlayback);
    document.getElementById('btn-info').addEventListener('click', toggleInfoPanel);
    document.getElementById('info-close').addEventListener('click', toggleInfoPanel);

    // Restore saved zoom
    const savedZoom = localStorage.getItem('airtfugue-zoom');
    if (savedZoom) {
      pxPerSec = parseInt(savedZoom, 10);
      document.getElementById('zoom').value = pxPerSec;
    }

    document.getElementById('zoom').addEventListener('input', e => {
      pxPerSec = parseInt(e.target.value, 10);
      localStorage.setItem('airtfugue-zoom', pxPerSec);
      drawFrame(Tone.Transport.seconds);
    });

    document.addEventListener('keydown', e => {
      if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        togglePlay();
      }
    });

    window.addEventListener('resize', () => {
      sizeLanes();
      drawFrame(Tone.Transport.seconds);
    });

    // Load first piece
    loadPiece(0);
  })
  .catch(err => {
    document.body.innerHTML =
      `<div style="padding:40px;color:red;font-family:monospace">` +
      `Error: ${err.message}<br>` +
      `Run: <code>python3 midi_to_json.py --all</code><br>` +
      `and: <code>python3 -m http.server 8000</code></div>`;
  });
