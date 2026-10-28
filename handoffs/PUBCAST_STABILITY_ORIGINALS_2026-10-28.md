# PubCast originals before the autonomous stability pass

Base commit: `f0c2297f50b33eda6cde9921ccc28a4908a27f46`. Source is preserved verbatim with SHA-256 hashes.

## 2i/index.html

SHA-256: `e183ac8719c7b650f88d5d858cd402a1d4d0b8b2f213256cf89896c66d993e91`

````text
<!DOCTYPE html>
<html lang="en" data-reach-artwork="original">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Reach · Writer’s Room</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&family=Cinzel+Decorative:wght@400;700&display=swap');

/* ═══════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════ */
:root {
  --ivory:#f9f4e6; --ivory-deep:#efe4cc; --ivory-glow:#fffbf0;
  --gold:#cda349; --gold-bright:#eecf83; --gold-deep:#93701f;
  --gold-glow:rgba(238,207,131,0.45); --gold-dim:rgba(205,163,73,0.18);
  --ink:#231f18; --pencil:#4a4032; --pencil-soft:#7c7160;
  --mahogany:#3a2013; --mahogany-deep:#1b0f09;
  --leather:#2c1608; --leather-seam:rgba(0,0,0,0.28);
  --velvet:#2e6b52; --velvet-glow:rgba(46,107,82,0.38);
  --parchment:#ecdfc3; --parchment-soft:#c3b391;
  --danger:#a24a3a; --danger-glow:rgba(162,74,58,0.3);
  --paper:#f6ecd5; --paper-aged:#f1e4c8; --paper-line:rgba(160,140,110,0.22);
  --margin-red:rgba(180,60,50,0.28);
  --glass-border:rgba(205,163,73,0.32);
  --frame-shadow:0 22px 46px -20px rgba(0,0,0,.85),
    inset 0 2px 0 rgba(255,225,150,.18),
    inset 0 -4px 8px rgba(0,0,0,.72);
}
*, *::before, *::after { box-sizing:border-box; }
html, body {
  height:100%; margin:0; overflow:hidden;
  font-family:'Cormorant Garamond',serif;
  color:var(--parchment);
  background:
    radial-gradient(ellipse 55% 32% at 50% 0%, rgba(238,207,131,0.10), transparent 62%),
    radial-gradient(ellipse 45% 30% at 12% 105%, rgba(46,107,82,0.07), transparent 60%),
    linear-gradient(165deg, #2c190f 0%, #1d1009 55%, #130a05 100%);
}

/* ═══════════════════════════════════════════════════════════════
   LAYOUT SHELL
   ═══════════════════════════════════════════════════════════════ */
.app-shell {
  display:grid;
  grid-template-rows: 42px 1fr 32px;
  height:100vh;
}

/* --- TOP BAR --- */
.top-bar {
  display:flex; align-items:center; gap:12px;
  padding:0 16px;
  background:linear-gradient(180deg, rgba(44,22,8,0.95), rgba(27,15,9,0.98));
  border-bottom:1px solid rgba(205,163,73,0.25);
  box-shadow:0 2px 12px rgba(0,0,0,0.5);
  z-index:20;
}
.top-logo {
  font-family:'Cinzel Decorative',serif;
  font-size:14px; font-weight:700;
  color:var(--gold-bright);
  text-shadow:0 1px 3px rgba(0,0,0,0.6), 0 0 12px rgba(238,207,131,0.15);
  white-space:nowrap;
  letter-spacing:0.04em;
}
.top-logo small {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; font-weight:400;
  color:var(--parchment-soft);
  display:block; margin-top:-2px;
  letter-spacing:0.08em;
}
.top-tabs {
  display:flex; gap:2px;
  margin:0 auto;
  background:rgba(0,0,0,0.25);
  border-radius:6px; padding:3px;
}
.top-tab {
  font-family:'IBM Plex Mono',monospace;
  font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
  padding:5px 14px; border-radius:4px;
  border:none; cursor:pointer;
  color:var(--parchment-soft);
  background:transparent;
  transition:all 0.15s ease;
  box-shadow:none;
}
.top-tab:hover { color:var(--parchment); background:rgba(205,163,73,0.12); }
.top-tab.active {
  color:var(--gold-bright);
  background:rgba(205,163,73,0.22);
  box-shadow:inset 0 0 0 1px rgba(205,163,73,0.3);
}
.top-right {
  display:flex; align-items:center; gap:10px;
  margin-left:auto;
}
.mode-badge {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; letter-spacing:0.1em; text-transform:uppercase;
  padding:4px 10px; border-radius:4px;
  border:1px solid var(--glass-border);
  cursor:pointer;
  transition:all 0.15s ease;
}
.mode-badge.write {
  color:#bff2c8; border-color:rgba(46,107,82,0.5);
  background:rgba(46,107,82,0.15);
}
.mode-badge.collab {
  color:var(--gold-bright); border-color:var(--glass-border);
  background:rgba(205,163,73,0.12);
}
.top-icon-btn {
  width:28px; height:28px; border-radius:50%;
  border:1px solid rgba(205,163,73,0.25);
  background:rgba(0,0,0,0.2);
  color:var(--parchment-soft);
  font-size:13px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.15s ease;
  padding:0;
  box-shadow:none;
}
.top-icon-btn:hover { border-color:var(--gold); color:var(--gold-bright); background:rgba(205,163,73,0.12); }

/* --- MAIN AREA --- */
.main-area {
  display:grid;
  grid-template-columns: 280px 1fr;
  min-height:0; overflow:hidden;
  gap:0;
}
.main-area.sidebar-hidden { grid-template-columns: 0px 1fr; }
.main-area.sidebar-hidden .sidebar { display:none; }

/* --- LEFT SIDEBAR --- */
.sidebar {
  display:flex; flex-direction:column;
  background:linear-gradient(180deg, rgba(44,22,8,0.92), rgba(20,11,6,0.96));
  border-right:1px solid rgba(205,163,73,0.18);
  overflow:hidden; min-height:0;
}
.sidebar-section {
  display:flex; flex-direction:column;
  border-bottom:1px solid rgba(205,163,73,0.12);
  min-height:0;
}
.sidebar-section.collapsed > :not(.section-header) { display:none; }
.section-header {
  font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.1em; text-transform:uppercase;
  color:var(--gold);
  padding:10px 14px 8px;
  display:flex; align-items:center; gap:8px;
  cursor:pointer;
  user-select:none;
  border:none; background:none; width:100%; text-align:left;
  box-shadow:none;
}
.section-header::before {
  content:''; width:5px; height:5px; border-radius:50%;
  background:var(--gold);
  box-shadow:0 0 6px rgba(238,207,131,0.6);
  flex-shrink:0;
}
.section-header .collapse-arrow {
  margin-left:auto; font-size:8px; color:var(--parchment-soft);
  transition:transform 0.2s ease;
}
.sidebar-section.collapsed .collapse-arrow { transform:rotate(-90deg); }
.section-body { padding:0 14px 12px; display:flex; flex-direction:column; gap:8px; }

/* Manuscript control */
.mc-row {
  display:flex; justify-content:space-between; align-items:center;
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft);
}
.mc-progress {
  width:100%; height:6px; border-radius:3px;
  background:rgba(0,0,0,0.3);
  border:1px solid rgba(205,163,73,0.15);
  overflow:hidden;
}
.mc-progress-fill {
  height:100%; border-radius:2px;
  background:linear-gradient(90deg, var(--gold-deep), var(--gold-bright));
  transition:width 0.3s ease;
}
.mc-btn-row { display:flex; gap:6px; }
.mc-btn {
  flex:1; font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.04em;
  padding:7px 8px; border-radius:5px;
  cursor:pointer;
  border:1px solid rgba(205,163,73,0.25);
  background:linear-gradient(160deg, rgba(255,255,255,0.04), rgba(0,0,0,0.15));
  color:var(--parchment);
  box-shadow:0 2px 4px rgba(0,0,0,0.3);
  transition:all 0.12s ease;
  text-transform:uppercase;
}
.mc-btn:hover:not(:disabled) {
  border-color:var(--gold);
  background:rgba(205,163,73,0.12);
  box-shadow:0 2px 8px rgba(0,0,0,0.4), 0 0 8px rgba(238,207,131,0.12);
}
.mc-btn:disabled { opacity:0.35; cursor:default; }
.mc-btn.primary {
  background:linear-gradient(155deg, rgba(255,255,255,0.5), transparent 28%),
    linear-gradient(160deg, #fffdf3, #eee1c8 48%, #cdbb98);
  color:#684b18;
  border-color:rgba(100,70,35,0.7);
  box-shadow:0 3px 6px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.9);
}
.mc-btn.primary:hover:not(:disabled) {
  filter:brightness(1.08);
  box-shadow:0 4px 10px rgba(0,0,0,0.5), 0 0 12px rgba(238,207,131,0.2);
}
.mc-btn.danger { border-color:var(--danger); color:#f2c0bf; }

/* Reference archive */
.ref-search {
  display:flex; gap:4px;
}
.ref-search input {
  flex:1; padding:6px 8px; border-radius:5px;
  border:1px solid rgba(205,163,73,0.18);
  background:rgba(0,0,0,0.2);
  color:var(--parchment);
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  outline:none;
}
.ref-search input:focus { border-color:var(--gold); }
.ref-search button {
  width:30px; flex:0 0 30px; padding:0; font-size:12px;
  border-radius:5px;
}
.ref-tabs {
  display:flex; gap:2px;
}
.ref-tab {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; letter-spacing:0.06em; text-transform:uppercase;
  padding:4px 8px; border-radius:3px;
  border:none; cursor:pointer;
  color:var(--parchment-soft); background:transparent;
  box-shadow:none;
}
.ref-tab:hover { color:var(--parchment); }
.ref-tab.active { color:var(--gold-bright); background:rgba(205,163,73,0.18); }
.ref-list-container {
  flex:1; overflow-y:auto; min-height:0;
  display:flex; flex-direction:column; gap:4px;
}
.ref-item {
  display:flex; align-items:flex-start; gap:8px;
  padding:8px; border-radius:5px;
  background:rgba(0,0,0,0.12);
  border:1px solid transparent;
  cursor:pointer;
  transition:all 0.12s ease;
}
.ref-item:hover {
  border-color:rgba(205,163,73,0.3);
  background:rgba(205,163,73,0.06);
}
.ref-icon {
  width:24px; height:24px; border-radius:4px;
  background:rgba(205,163,73,0.12);
  display:flex; align-items:center; justify-content:center;
  font-size:11px; flex-shrink:0;
  color:var(--gold);
  margin-top:2px;
}
.ref-meta {
  flex:1; min-width:0;
}
.ref-meta .ref-name {
  font-family:'Cormorant Garamond',serif;
  font-size:13px; color:var(--parchment);
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.ref-meta .ref-type {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; color:var(--parchment-soft);
}
.ref-meta .ref-date {
  font-family:'IBM Plex Mono',monospace;
  font-size:8.5px; color:var(--parchment-soft);
  opacity:0.7;
}
.ref-actions { display:flex; gap:4px; flex-shrink:0; margin-top:2px; }
.ref-action-btn {
  width:22px; height:22px; border-radius:3px;
  border:1px solid rgba(205,163,73,0.15);
  background:transparent; color:var(--parchment-soft);
  font-size:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  padding:0; box-shadow:none;
}
.ref-action-btn:hover { border-color:var(--gold); color:var(--gold-bright); }

/* Chat pane */
.chat-section { flex:1; min-height:0; }
.chat-section .section-body { flex:1; min-height:0; display:flex; flex-direction:column; }
.chat-log {
  flex:1; overflow-y:auto; min-height:0;
  display:flex; flex-direction:column; gap:6px;
  padding-right:4px;
}
.chat-msg {
  font-size:13px; line-height:1.45;
  padding:7px 10px; border-radius:8px;
  max-width:92%;
}
.chat-msg.pp {
  background:rgba(0,0,0,0.22); border:1px solid rgba(0,0,0,0.15);
  align-self:flex-start; color:var(--parchment);
}
.chat-msg.you {
  background:rgba(46,107,82,0.2); border:1px solid var(--velvet-glow);
  align-self:flex-end; color:var(--parchment);
}
.chat-msg .who {
  font-family:'IBM Plex Mono',monospace;
  font-size:8.5px; text-transform:uppercase; letter-spacing:0.06em;
  color:var(--parchment-soft); display:block; margin-bottom:2px;
}
.chat-msg.thinking { opacity:0.5; font-style:italic; }
.chat-input-row {
  display:flex; gap:4px; margin-top:6px; flex-shrink:0;
}
.chat-input-row input {
  flex:1; font-family:'Cormorant Garamond',serif;
  font-size:13px; padding:7px 9px;
  color:var(--parchment);
  border:1px solid rgba(205,163,73,0.18);
  border-radius:6px; background:rgba(0,0,0,0.2);
  outline:none;
}
.chat-input-row input:focus { border-color:var(--gold); }
.chat-mic-btn {
  width:28px; flex:0 0 28px; padding:0; font-size:12px;
  border-radius:6px;
}
.chat-mic-btn.listening {
  background:linear-gradient(160deg,#c94747,#8a2c2c) !important;
  color:#fff !important;
  animation:micPulse 1s ease-in-out infinite;
}
@keyframes micPulse { 0%,100%{box-shadow:0 0 0 0 rgba(201,71,71,.5)} 50%{box-shadow:0 0 0 5px rgba(201,71,71,0)} }

/* ═══════════════════════════════════════════════════════════════
   NOTEBOOK
   ═══════════════════════════════════════════════════════════════ */
.notebook-frame {
  position:relative;
  display:flex;
  min-height:0; overflow:hidden;
  background:
    radial-gradient(ellipse at 50% 4%, rgba(255,220,145,0.10), transparent 34%),
    radial-gradient(ellipse at 50% 100%, rgba(0,0,0,0.3), transparent 48%),
    linear-gradient(180deg, #2a160d, #160b06 82%);
  border-left:3px solid transparent;
  border-image:linear-gradient(180deg, #e4bd68, #6d4a16 18%, #261609 52%, #c49a48 82%, #5b3d12) 1;
  box-shadow:inset 0 18px 35px rgba(255,215,135,.03), inset 0 -30px 45px rgba(0,0,0,.4);
}
#lanternCanvas {
  position:absolute; inset:0; width:100%; height:100%;
  pointer-events:none; z-index:0;
}

.notebook-inner {
  position:relative; z-index:1;
  display:flex; flex:1; min-height:0; min-width:0;
  margin:8px 8px 8px 0;
}

/* Spiral spine */
.spiral-spine {
  flex:0 0 52px;
  position:relative;
  background:linear-gradient(90deg, #090604, #21150d 12%, #0d0805 27%, #24170e 52%, #090604 76%, #1b1009);
  box-shadow:inset -8px 0 10px -8px rgba(0,0,0,.9), inset 6px 0 8px -8px rgba(238,207,131,.15);
  overflow:hidden;
}
.spiral-spine canvas { width:100%; height:100%; display:block; }

/* Page sheets */
.page-sheets {
  flex:1; min-width:0; min-height:0;
  display:flex; flex-direction:column;
  overflow:hidden;
  border-radius:0 6px 6px 0;
  box-shadow:inset -10px 0 16px -14px rgba(0,0,0,.6), inset 0 2px 0 rgba(255,255,255,.6);
  position:relative;
}

/* Manuscript zone (locked/committed text) */
.manuscript-zone {
  background:var(--paper);
  flex:0 0 auto; max-height:45vh;
  overflow-y:auto;
  position:relative;
  padding:0;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9),
    inset -6px 0 12px rgba(120,84,30,.10),
    inset 0 -6px 12px rgba(90,60,20,.07);
}
.manuscript-zone .zone-label {
  position:sticky; top:0; right:0; z-index:5;
  font-family:'IBM Plex Mono',monospace; font-size:8px;
  letter-spacing:0.12em; color:var(--gold-deep); text-transform:uppercase;
  padding:4px 14px;
  background:linear-gradient(180deg, var(--paper), rgba(246,236,213,0.9));
  text-align:right;
}

/* Solo mode */
.page-sheets.solo-mode .manuscript-zone { flex:1; max-height:none; }
.page-sheets.solo-mode .tortoise-seam { display:none; }
.page-sheets.solo-mode .draft-zone { display:none; }
.page-sheets.solo-mode .solo-editor { display:flex; }
.page-sheets.solo-mode .manuscript-lines { display:none; }

.solo-editor {
  display:none; flex:1; flex-direction:row;
  min-height:0;
}
.line-numbers {
  flex:0 0 44px;
  padding:6px 0;
  text-align:right;
  font-family:'IBM Plex Mono',monospace;
  font-size:12px; line-height:1.55;
  color:rgba(147,112,31,0.4);
  user-select:none;
  overflow-y:auto; overflow-x:hidden;
  scrollbar-width:none;
  border-right:1px solid var(--margin-red);
  padding-right:8px;
}
.line-numbers::-webkit-scrollbar { display:none; }
.solo-textarea {
  flex:1; resize:none; border:none; outline:none;
  font-family:'Cormorant Garamond',serif;
  font-size:15.5px; line-height:1.55;
  color:var(--ink);
  background:transparent;
  padding:6px 24px 40px 14px;
  overflow-y:auto;
}

/* Manuscript lines (co-writing committed) */
.manuscript-lines {
  padding:4px 0;
}
.m-line {
  font-family:'Cormorant Garamond',serif;
  font-size:15px; line-height:1.5;
  color:var(--ink);
  padding:1px 24px 1px 58px;
  cursor:pointer;
  position:relative;
  transition:background 0.1s ease;
  display:flex; align-items:baseline;
}
.m-line:hover { background:rgba(147,112,31,0.06); }
.m-line.selected { background:rgba(205,163,73,0.18); box-shadow:inset 3px 0 0 var(--gold); }
.m-line.locked::after {
  content:'🔒'; position:absolute; right:8px; top:50%; transform:translateY(-50%);
  font-size:10px; opacity:0.4;
}
.m-line .line-num {
  position:absolute; left:8px;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  color:rgba(147,112,31,0.35);
  width:36px; text-align:right;
  user-select:none;
}
.m-line-edit textarea {
  width:100%; font-family:'Cormorant Garamond',serif;
  font-size:15px; line-height:1.5; color:var(--ink);
  background:rgba(255,255,255,0.5);
  border:1px solid var(--gold-deep); border-radius:4px;
  padding:3px 6px; resize:vertical; outline:none;
}
.chapter-heading {
  font-family:'Cinzel Decorative',serif;
  font-size:20px; text-align:center;
  color:var(--ink); padding:18px 24px 6px;
  letter-spacing:0.04em;
}
.chapter-subtitle {
  font-family:'Cormorant Garamond',serif;
  font-style:italic; font-size:16px;
  text-align:center; color:var(--pencil);
  padding:0 24px 12px;
}
.chapter-divider {
  text-align:center; padding:2px 0 10px;
  color:var(--gold-deep); font-size:14px;
  letter-spacing:0.3em;
  opacity:0.5;
}

/* Tortoise seam divider */
.tortoise-seam {
  height:8px; flex-shrink:0;
  background:linear-gradient(90deg, #8a5a22, #c49a48, #8a5a22);
  box-shadow:
    inset 0 2px 2px rgba(255,255,255,0.4),
    inset 0 -2px 3px rgba(0,0,0,0.5),
    0 1px 2px rgba(0,0,0,0.5);
}

/* Draft zone (co-writing buffer) */
.draft-zone {
  background:var(--paper-aged);
  flex:1; min-height:0; overflow-y:auto;
  position:relative;
  padding:0;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.8),
    inset -6px 0 12px rgba(120,84,30,.10);
  scroll-behavior:smooth;
}
.reading-line {
  font-family:'Kalam',cursive;
  font-size:16px; line-height:1.45;
  color:var(--pencil);
  padding:6px 24px 6px 58px;
  background:rgba(205,163,73,0.12);
  border-left:3px solid var(--gold);
  margin:0 0 4px;
  position:relative;
}
.reading-line.reaction { border-left-color:var(--velvet); background:rgba(46,107,82,0.08); }
.draft-area {
  display:block; width:100%; min-height:100px;
  resize:none; border:none; outline:none; overflow-y:auto;
  font-family:'Kalam',cursive;
  font-size:16px; line-height:1.5;
  color:var(--pencil);
  background:transparent;
  padding:4px 24px 30px 58px;
  text-shadow:0 .25px 0 rgba(0,0,0,.18);
}

/* ═══════════════════════════════════════════════════════════════
   BOTTOM STATUS BAR
   ═══════════════════════════════════════════════════════════════ */
.status-bar {
  display:flex; align-items:center; gap:12px;
  padding:0 16px;
  background:linear-gradient(180deg, rgba(27,15,9,0.96), rgba(20,11,6,0.98));
  border-top:1px solid rgba(205,163,73,0.18);
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft);
  z-index:20;
}
.status-dot {
  width:6px; height:6px; border-radius:50%;
  background:var(--parchment-soft);
}
.status-dot.playing { background:var(--velvet); box-shadow:0 0 6px rgba(46,107,82,0.8); }
.status-dot.paused { background:var(--gold); box-shadow:0 0 6px rgba(238,207,131,0.6); }
.status-sep { color:rgba(205,163,73,0.25); }
.llm-pill {
  padding:2px 8px; border-radius:999px;
  border:1px solid var(--glass-border);
  cursor:pointer; font-size:9px;
  transition:all 0.12s ease;
}
.llm-pill.ok { color:#bff2c8; border-color:#4c9a63; }
.llm-pill.err { color:#f2c0bf; border-color:#9a4c4c; }
.status-right {
  margin-left:auto;
  display:flex; align-items:center; gap:10px;
}
.playback-controls {
  display:flex; align-items:center; gap:4px;
}
.pb-btn {
  width:24px; height:24px; border-radius:4px;
  border:1px solid rgba(205,163,73,0.2);
  background:transparent; color:var(--parchment-soft);
  font-size:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  padding:0; box-shadow:none;
  transition:all 0.12s ease;
}
.pb-btn:hover { border-color:var(--gold); color:var(--gold-bright); }
.pb-btn.active { background:rgba(46,107,82,0.2); border-color:var(--velvet); color:#bff2c8; }
.speed-slider {
  width:50px; height:3px;
  accent-color:var(--gold);
}
.save-btn {
  font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.06em; text-transform:uppercase;
  padding:4px 12px; border-radius:4px;
  border:1px solid rgba(205,163,73,0.3);
  background:rgba(205,163,73,0.1);
  color:var(--gold-bright);
  cursor:pointer;
  box-shadow:none;
  transition:all 0.12s ease;
}
.save-btn:hover { background:rgba(205,163,73,0.2); border-color:var(--gold); }

/* ═══════════════════════════════════════════════════════════════
   MODALS
   ═══════════════════════════════════════════════════════════════ */
.modal-backdrop {
  position:fixed; inset:0;
  background:rgba(10,6,3,0.65);
  z-index:100;
  display:none; align-items:center; justify-content:center;
}
.modal-backdrop.open { display:flex; }
.modal {
  width:min(460px, 92vw); max-height:86vh; overflow:auto;
  padding:18px; border-radius:10px;
  background:linear-gradient(160deg, #432516, #1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  box-shadow:0 24px 48px -18px rgba(0,0,0,.9);
  color:var(--parchment);
}
.modal-title {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  letter-spacing:0.1em; text-transform:uppercase;
  color:var(--gold); margin-bottom:12px;
  display:flex; align-items:center; gap:6px;
}
.modal-title::before {
  content:''; width:5px; height:5px; border-radius:50%;
  background:var(--gold); box-shadow:0 0 6px rgba(238,207,131,0.6);
}
.modal-body { display:flex; flex-direction:column; gap:6px; }
.modal-body label {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft); margin-top:6px;
}
.modal-body select, .modal-body input[type=text], .modal-body input[type=password], .modal-body input[type=number] {
  width:100%; padding:7px 9px; border-radius:5px;
  border:1px solid var(--glass-border);
  background:rgba(0,0,0,0.25); color:var(--parchment);
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  outline:none;
}
.modal-body select:focus, .modal-body input:focus { border-color:var(--gold); }
.modal-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:14px; }
.modal-actions button { font-size:11px; padding:6px 14px; }
.test-result {
  margin-top:8px; font-family:'IBM Plex Mono',monospace;
  font-size:11px; min-height:14px;
}
.test-result.ok { color:#bff2c8; }
.test-result.err { color:#f2c0bf; }
.llm-fields { display:none; flex-direction:column; gap:4px; }
.llm-fields.active { display:flex; }

/* Context menu */
.context-menu {
  position:fixed; z-index:200;
  padding:5px; border-radius:8px;
  background:linear-gradient(160deg,#432516,#1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  box-shadow:0 10px 24px -6px rgba(0,0,0,0.7);
  display:none;
  min-width:160px;
}
.context-menu.open { display:block; }
.ctx-btn {
  display:block; width:100%; text-align:left;
  font-family:'IBM Plex Mono',monospace;
  font-size:11px; padding:7px 12px;
  background:transparent; border:none; color:var(--parchment);
  cursor:pointer; border-radius:4px;
  box-shadow:none;
}
.ctx-btn:hover { background:rgba(205,163,73,0.15); }
.ctx-sep { height:1px; background:rgba(205,163,73,0.12); margin:3px 8px; }

/* Ref viewer overlay */
.ref-viewer {
  position:absolute; inset:0; z-index:10;
  background:var(--paper);
  display:none; flex-direction:column;
}
.ref-viewer.open { display:flex; }
.ref-viewer-header {
  display:flex; align-items:center; gap:8px;
  padding:8px 14px;
  border-bottom:1px solid rgba(147,112,31,0.15);
  background:linear-gradient(180deg, var(--paper), var(--paper-aged));
}
.ref-viewer-header .ref-back-btn {
  font-size:11px; padding:4px 10px; border-radius:4px;
  border:1px solid rgba(147,112,31,0.3);
  background:transparent; color:var(--pencil);
  cursor:pointer; box-shadow:none;
}
.ref-viewer-header .ref-title {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--pencil-soft);
}
.ref-viewer-body {
  flex:1; overflow-y:auto; padding:12px 24px;
  font-family:'Cormorant Garamond',serif;
  font-size:15px; line-height:1.6;
  color:var(--ink);
  white-space:pre-wrap;
}

/* Hamburger menu */
.hamburger-menu {
  position:fixed; top:46px; right:12px; z-index:90;
  min-width:220px; padding:6px;
  background:linear-gradient(160deg,#432516,#1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  border-radius:8px;
  box-shadow:0 16px 32px -12px rgba(0,0,0,.9);
  display:none;
}
.hamburger-menu.open { display:block; }
.hm-btn {
  display:flex; align-items:center; gap:8px; width:100%;
  text-align:left; padding:7px 12px; border-radius:5px;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  background:transparent; border:none; color:var(--parchment);
  cursor:pointer; box-shadow:none;
}
.hm-btn:hover { background:rgba(205,163,73,0.12); }
.hm-btn .hm-icon { width:18px; text-align:center; font-size:12px; }
.hm-sep { height:1px; background:rgba(205,163,73,0.12); margin:4px 12px; }
.hm-toggle::after {
  content:'Off'; margin-left:auto;
  font-size:8.5px; padding:2px 6px; border-radius:999px;
  background:rgba(255,255,255,0.06); color:var(--parchment-soft);
}
.hm-toggle.on::after {
  content:'On'; background:rgba(205,163,73,0.25); color:var(--gold-bright);
}

/* Scrollbar */
::-webkit-scrollbar { width:7px; height:7px; }
::-webkit-scrollbar-track { background:rgba(0,0,0,.12); }
::-webkit-scrollbar-thumb {
  background:linear-gradient(180deg,#5a3d15,#cda349,#6b4a18);
  border-radius:8px; border:1.5px solid transparent; background-clip:padding-box;
}

/* Utilities */
.hidden { display:none !important; }
</style>
<link rel="stylesheet" href="./2i-assets/reach.css">
<link rel="stylesheet" href="./2i-assets/artwork.css">
<link rel="stylesheet" href="./2i-assets/phone.css">
<link rel="stylesheet" href="./2i-assets/reader.css">
  <script src="/static/reach_auth.js"></script>
<link rel="stylesheet" href="/static/world_chat.css">
<script src="/static/program_audio_runtime.js"></script>
</head>
<body>
<!-- ═══════════════════════════════════════════════════════════════
     APP SHELL
     ═══════════════════════════════════════════════════════════════ -->
<div class="app-shell">
  <!-- TOP BAR -->
  <div class="top-bar">
    <div class="top-logo">Writer’s Room<small>PUBCAST REACH · 2i</small></div>
    <div class="top-tabs">
      <button class="top-tab active" data-tab="manuscript">Manuscript</button>
      <button class="top-tab" id="shelfBtn">My manuscripts</button>
    </div>
    <div class="top-right">
      <button class="mode-badge write" id="modeBadge" title="Toggle between Write (solo) and Collab (co-writing) mode">Write</button>
      <button class="top-icon-btn" id="sidebarToggle" title="Toggle sidebar">☰</button>
      <button class="top-icon-btn" id="menuToggle" title="Menu">⚙</button>
    </div>
  </div>

  <!-- MAIN AREA -->
  <div class="main-area" id="mainArea">
    <!-- SIDEBAR -->
    <div class="sidebar" id="sidebar">
      <!-- Manuscript Control -->
      <div class="sidebar-section" id="mcSection">
        <button class="section-header" data-toggle-section="mcSection">
          Manuscript Control <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body">
          <div class="mc-row"><span>Draft Status</span><span id="mcDraftStatus">Active</span></div>
          <div class="mc-row"><span id="mcWordProgress">0 / — words</span><span id="mcPercent"></span></div>
          <div class="mc-progress"><div class="mc-progress-fill" id="mcProgressFill" style="width:0"></div></div>
          <div class="mc-btn-row">
            <button class="mc-btn primary" id="lockSceneBtn">🔒 Lock scene</button>
          </div>
          <div class="mc-btn-row">
            <button class="mc-btn" id="unlockBtn">🔓 Unlock</button>
            <button class="mc-btn" id="lockAllBtn">Lock all</button>
          </div>
          <div class="mc-btn-row">
            <button class="mc-btn" id="newChapterBtn">New chapter</button>
            <button class="mc-btn" id="exportBtn">Export</button>
          </div>
          <div class="mc-btn-row" id="collabOnlyControls">
            <button class="mc-btn primary" id="approveBtn">✓ Commit draft</button>
            <button class="mc-btn" id="genBtn">⚡ Generate</button>
          </div>
        </div>
      </div>

      <!-- Reference Archive -->
      <div class="sidebar-section" id="refSection">
        <button class="section-header" data-toggle-section="refSection">
          Reference Archive <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body" style="flex:1; min-height:0;">
          <div class="ref-search">
            <input type="text" id="refSearchInput" placeholder="Search documents…" />
            <button class="mc-btn" style="flex:0 0 28px; padding:0; font-size:11px;" data-reference-search>🔍</button>
          </div>
          <div class="ref-tabs">
            <button class="ref-tab active" data-filter="all">All</button>
            <button class="ref-tab" data-filter="chapter">Chapters</button>
            <button class="ref-tab" data-filter="research">Research</button>
            <button class="ref-tab" data-filter="notes">Notes</button>
          </div>
          <div class="ref-list-container" id="refListContainer"></div>
          <button class="mc-btn" id="addRefBtn" style="flex-shrink:0;">+ Add reference</button>
        </div>
      </div>

      <!-- Shared room is a separate optional surface; PubPartner and manuscript stay private. -->
      <details class="sidebar-section world-room-section" id="worldRoomSection">
        <summary class="section-header">✧ World Chat · shared room</summary>
        <div class="world-chat-widget" data-world-chat>
          <div data-world-status role="status" aria-live="polite">Open to connect to World Chat.</div>
          <button type="button" data-world-export>Save full room log</button>
          <div data-world-messages role="log" aria-label="World Chat messages"></div>
          <form data-world-form><textarea data-world-input aria-label="Message World Chat" placeholder="Say hello to the world…" maxlength="10000"></textarea><button type="submit" data-world-send>Send</button></form>
        </div>
      </details>
      <!-- Chat -->
      <div class="sidebar-section chat-section" id="chatSection">
        <button class="section-header" data-toggle-section="chatSection">
          Your PubPartner <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body">
          <label class="partner-label" for="partnerSelect">At your side</label>
          <select id="partnerSelect" aria-label="Your PubPartner"><option value="alex">Alex</option><option value="craig">Craig</option><option value="friend">Friend</option></select>
          <p class="partner-note" id="partnerNote">A little space to think together.</p>
          <div class="chat-log" id="chatLog" aria-live="polite" aria-label="Conversation"></div>
          <div class="chat-input-row">
            <input id="chatInput" type="text" placeholder="Talk with PubPartner…" />
            <button class="mc-btn chat-mic-btn" id="chatMicBtn" title="Dictate">🎤</button>
            <button class="mc-btn primary" id="chatSendBtn" style="flex:0 0 auto; padding:5px 10px;">Send</button>
          </div>
        </div>
      </div>
    </div>

    <!-- NOTEBOOK -->
    <div class="notebook-frame" id="notebookFrame">
      <canvas id="lanternCanvas"></canvas>
      <div class="notebook-inner">
        <div class="spiral-spine"><canvas id="spineCanvas"></canvas></div>
        <div class="page-sheets" id="pageSheets">
          <!-- Reference viewer overlay -->
          <div class="ref-viewer" id="refViewer">
            <div class="ref-viewer-header">
              <button class="ref-back-btn" data-close-reference>← Back</button>
              <span class="ref-title" id="refViewerTitle"></span>
            </div>
            <div class="ref-viewer-body" id="refViewerBody"></div>
          </div>

          <!-- Manuscript zone (committed text / solo editor) -->
          <div class="manuscript-zone" id="manuscriptZone">
            <div class="zone-label" id="zoneLabel">Manuscript</div>
            <div class="paper-title"><span>THE WRITING DESK</span><h1 id="paperTitle">Untitled manuscript</h1><div>✦</div></div>
            <div class="manuscript-lines" id="manuscriptLines"></div>
            <div class="solo-editor" id="soloEditor">
              <div class="line-numbers" id="lineNumbers"></div>
              <textarea class="solo-textarea" id="soloTextarea" aria-label="Manuscript" placeholder="Every story begins somewhere.&#10;Begin yours here…" spellcheck="true"></textarea>
            </div>
          </div>

          <!-- Seam -->
          <div class="tortoise-seam" id="tortoiseSeam"></div>

          <!-- Draft zone (buffer in co-writing) -->
          <div class="draft-zone" id="draftZone">
            <div id="readingIndicator"></div>
            <textarea class="draft-area" id="draftArea" placeholder="Keep writing…" spellcheck="true"></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- STATUS BAR -->
  <div class="status-bar">
    <span class="status-dot" id="statusDot"></span>
    <span id="statusText">idle</span>
    <span class="status-sep">|</span>
    <span id="docTitleDisplay" style="cursor:pointer;" title="Click to rename"></span>
    <span class="status-sep">|</span>
    <span id="wordCount">0 words</span>
    <span class="status-sep">|</span>
    <span id="llmPill" class="llm-pill" title="Click to configure LLM">no LLM</span>
    <div class="status-right">
      <div class="playback-controls" id="playbackControls">
        <button class="pb-btn" id="stopBtn" title="Stop">■</button>
        <button class="pb-btn" id="playBtn" title="Play/Pause">▶</button>
        <button class="pb-btn" id="skipBtn" title="Skip">⏭</button>
        <input type="range" class="speed-slider" id="speedSlider" min="0.5" max="2.5" step="0.25" value="1" title="Read speed" />
      </div>
      <span id="saveIndicator" role="status">Ready to write</span>
      <button class="save-btn" id="saveBtn">Save</button>
    </div>
  </div>
</div>

<!-- HAMBURGER MENU -->
<div class="hamburger-menu" id="hamburgerMenu">
  <button class="hm-btn" id="hmNewDoc"><span class="hm-icon">📄</span>New document</button>
  <button class="hm-btn" id="hmOpenDoc"><span class="hm-icon">📂</span>Open document…</button>
  <button class="hm-btn" id="hmSaveAs"><span class="hm-icon">💾</span>Save as…</button>
  <button class="hm-btn" id="hmRestoreAutosave"><span class="hm-icon">🔄</span>Restore autosave…</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmFindReplace"><span class="hm-icon">🔍</span>Find &amp; replace</button>
  <button class="hm-btn" id="hmRenameDoc"><span class="hm-icon">✏️</span>Rename document</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmLLMSettings"><span class="hm-icon">⚙</span>LLM provider…</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmKeyboardHelp"><span class="hm-icon">⌨</span>Keyboard shortcuts</button>
</div>

<!-- CONTEXT MENU -->
<div class="context-menu" id="contextMenu">
  <button class="ctx-btn" id="ctxEdit">Edit line</button>
  <button class="ctx-btn" id="ctxInsertAbove">Insert line above</button>
  <button class="ctx-btn" id="ctxInsertBelow">Insert line below</button>
  <div class="ctx-sep"></div>
  <button class="ctx-btn" id="ctxLock">Lock line</button>
  <button class="ctx-btn" id="ctxUnlock">Unlock line</button>
  <button class="ctx-btn" id="ctxDelete">Delete line</button>
</div>

<!-- LLM MODAL -->
<div class="modal-backdrop" id="llmModalBackdrop">
  <div class="modal">
    <div class="modal-title">LLM Provider</div>
    <div class="modal-body">
      <label>Provider</label>
      <select id="llmProvider">
        <option value="claude">Claude (Anthropic API)</option>
        <option value="openai">OpenAI / OpenAI-compatible</option>
        <option value="local">Local (Ollama, LM Studio)</option>
        <option value="pubpartner">PubPartner (local server)</option>
      </select>
      <div id="llmFieldsClaude" class="llm-fields">
        <label>API key</label><input id="llmClaudeKey" type="password" placeholder="sk-ant-…" autocomplete="off" />
        <label>Model</label><input id="llmClaudeModel" type="text" value="claude-sonnet-4-6" />
      </div>
      <div id="llmFieldsOpenai" class="llm-fields">
        <label>API key</label><input id="llmOpenaiKey" type="password" placeholder="sk-…" autocomplete="off" />
        <label>Base URL</label><input id="llmOpenaiEndpoint" type="text" value="https://api.openai.com/v1" />
        <label>Model</label><input id="llmOpenaiModel" type="text" value="gpt-4o-mini" />
      </div>
      <div id="llmFieldsLocal" class="llm-fields">
        <label>Endpoint URL</label><input id="llmLocalEndpoint" type="text" value="http://localhost:11434/v1/chat/completions" />
        <label>Model</label><input id="llmLocalModel" type="text" value="llama3" />
      </div>
      <div id="llmFieldsPubpartner" class="llm-fields">
        <label>PubPartner URL</label><input id="llmPPEndpoint" type="text" value="http://localhost:8000" />
        <label>Auth token (if set)</label><input id="llmPPToken" type="password" autocomplete="off" />
        <label for="reachProvider">Model service</label><select id="reachProvider"><option value="ollama">Local model · Ollama</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="gemini">Gemini</option><option value="openai_compatible">OpenAI compatible</option></select>
        <label for="reachModel">Model name</label><input id="reachModel" placeholder="ministral-pubcast:3b" />
        <label for="reachCredential">Saved BYOK credential ID (optional)</label><input id="reachCredential" />
        <label for="reachBaseURL">Compatible service URL (only if needed)</label><input id="reachBaseURL" placeholder="http://localhost:1234/v1" />
        <p class="partner-note">Keep your partner when you change models. Cloud keys belong in <a href="/static/byok.html" target="_blank" rel="noopener">Reach’s key settings</a>.</p>
      </div>
    </div>
    <div class="modal-actions">
      <button class="mc-btn" id="llmTestBtn">Test</button>
      <button class="mc-btn" id="llmCancelBtn">Cancel</button>
      <button class="mc-btn primary" id="llmSaveBtn">Save</button>
    </div>
    <div id="llmTestResult" class="test-result"></div>
  </div>
</div>

<!-- FIND & REPLACE MODAL -->
<div class="modal-backdrop" id="frModalBackdrop">
  <div class="modal">
    <div class="modal-title">Find &amp; Replace</div>
    <div class="modal-body">
      <label>Find</label><input id="frFind" type="text" placeholder="text to find…" autocomplete="off" />
      <label>Replace with</label><input id="frReplace" type="text" placeholder="replacement…" autocomplete="off" />
    </div>
    <div class="modal-actions">
      <button class="mc-btn" id="frCloseBtn">Close</button>
      <button class="mc-btn primary" id="frReplaceAllBtn">Replace all</button>
    </div>
    <div id="frResult" class="test-result"></div>
  </div>
</div>

<!-- RENAME MODAL -->
<div class="modal-backdrop" id="renameModalBackdrop">
  <div class="modal">
    <div class="modal-title">Rename Document</div>
    <div class="modal-body">
      <label>Title</label><input id="renameInput" type="text" />
    </div>
    <div class="modal-actions">
      <button class="mc-btn" data-close-modal="renameModalBackdrop">Cancel</button>
      <button class="mc-btn primary" id="renameSaveBtn">Save</button>
    </div>
  </div>
</div>

<!-- KEYBOARD SHORTCUTS MODAL -->
<div class="modal-backdrop" id="kbModalBackdrop">
  <div class="modal">
    <div class="modal-title">Keyboard Shortcuts</div>
    <div class="modal-body" style="font-family:'IBM Plex Mono',monospace; font-size:11px; line-height:2;">
      <span style="color:var(--gold)">Ctrl+S</span> — Save document<br>
      <span style="color:var(--gold)">Ctrl+Z</span> — Undo<br>
      <span style="color:var(--gold)">Ctrl+Y</span> — Redo<br>
      <span style="color:var(--gold)">Ctrl+F</span> — Find &amp; replace<br>
      <span style="color:var(--gold)">Ctrl+E</span> — Export manuscript<br>
      <span style="color:var(--gold)">Ctrl+Enter</span> — Commit draft (collab mode)<br>
      <span style="color:var(--gold)">Ctrl+G</span> — Generate next (collab mode)<br>
      <span style="color:var(--gold)">Space</span> — Play/Pause (when draft area unfocused)<br>
      <span style="color:var(--gold)">Escape</span> — Close menus/modals
    </div>
    <div class="modal-actions">
      <button class="mc-btn primary" data-close-modal="kbModalBackdrop">Got it</button>
    </div>
  </div>
</div>

<!-- AUTOSAVE RESTORE MODAL -->
<div class="modal-backdrop" id="autosaveModalBackdrop">
  <div class="modal">
    <div class="modal-title">Restore Autosave</div>
    <div class="modal-body" id="autosaveList" style="font-family:'IBM Plex Mono',monospace; font-size:11px;">
      Checking for autosaves…
    </div>
    <div class="modal-actions">
      <button class="mc-btn" data-close-modal="autosaveModalBackdrop">Cancel</button>
    </div>
  </div>
</div>

<!-- ADD REFERENCE MODAL -->
<div class="modal-backdrop" id="addRefModalBackdrop">
  <div class="modal">
    <div class="modal-title">Add Reference</div>
    <div class="modal-body">
      <label>Name</label><input id="refNameInput" type="text" placeholder="Character profile, chapter outline…" />
      <label>Type</label>
      <select id="refTypeInput">
        <option value="notes">Notes</option>
        <option value="chapter">Chapter</option>
        <option value="research">Research</option>
        <option value="character">Character</option>
      </select>
      <label>Content</label>
      <textarea id="refContentInput" style="width:100%; min-height:120px; padding:8px; border-radius:5px; border:1px solid var(--glass-border); background:rgba(0,0,0,0.25); color:var(--parchment); font-family:'Cormorant Garamond',serif; font-size:13px; resize:vertical; outline:none;" placeholder="Paste or type reference content…"></textarea>
    </div>
    <div class="modal-actions">
      <button class="mc-btn" data-close-modal="addRefModalBackdrop">Cancel</button>
      <button class="mc-btn primary" id="addRefSaveBtn">Add</button>
    </div>
  </div>
</div>

<script>
/* ═══════════════════════════════════════════════════════════════════
   PUBCAST 2i — WRITER'S ROOM — PRODUCTION BUILD
   ═══════════════════════════════════════════════════════════════════
   Single-file application. Two modes:
     WRITE  — solo word processor for manuscript editing
     COLLAB — co-writing with AI generation + approval flow
   
   Donor mechanics; Reach integration and artwork scripts follow.
   ═══════════════════════════════════════════════════════════════════ */

// ── LLM ENGINE ─────────────────────────────────────────────────────
const LLM_KEY = 'pubcast2i_llm_v2';
function defaultLLM() {
  return {
    provider:'pubpartner',
    claude:  { apiKey:'', model:'claude-sonnet-4-6' },
    openai:  { apiKey:'', endpoint:'https://api.openai.com/v1', model:'gpt-4o-mini' },
    local:   { endpoint:'http://localhost:11434/v1/chat/completions', model:'llama3' },
    pubpartner: { endpoint:location.protocol.startsWith('http') ? location.origin : 'http://localhost:8000', token:'' }
  };
}
function loadLLM() {
  try {
    const raw = sessionStorage.getItem(LLM_KEY) || localStorage.getItem(LLM_KEY);
    if (!raw) return defaultLLM();
    const p = JSON.parse(raw), d = defaultLLM();
    const m = Object.assign({}, d, p);
    for (const k of ['claude','openai','local','pubpartner']) m[k] = Object.assign({}, d[k], p[k] || {});
    return m;
  } catch { return defaultLLM(); }
}
function saveLLM(cfg) {
  // Connection secrets last for this tab's session, not in the document or
  // permanent browser settings. BYOK is the server's encrypted credential store.
  try {
    sessionStorage.setItem(LLM_KEY, JSON.stringify(cfg));
    const safe = JSON.parse(JSON.stringify(cfg));
    safe.claude.apiKey = ''; safe.openai.apiKey = ''; safe.pubpartner.token = '';
    localStorage.setItem(LLM_KEY, JSON.stringify(safe));
  } catch {}
}
let llmCfg = loadLLM();
let abortController = null;

const LLM_ADAPTERS = {
  claude: {
    label: 'Claude',
    configured(c) { return !!(c.claude.apiKey?.trim()); },
    async send(msgs, c, signal) {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method:'POST', signal,
        headers: {
          'Content-Type':'application/json',
          'x-api-key': c.claude.apiKey.trim(),
          'anthropic-version':'2023-06-01',
          'anthropic-dangerous-direct-browser-access':'true'
        },
        body: JSON.stringify({
          model: (c.claude.model || 'claude-sonnet-4-6').trim(),
          max_tokens: 800,
          messages: msgs
        })
      });
      if (!r.ok) throw new Error(`Claude API ${r.status}: ${(await r.text()).slice(0,200)}`);
      const d = await r.json();
      return (d.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n').trim();
    }
  },
  openai: {
    label: 'OpenAI',
    configured(c) { return !!(c.openai.apiKey?.trim()); },
    async send(msgs, c, signal) {
      const base = (c.openai.endpoint || 'https://api.openai.com/v1').replace(/\/+$/, '');
      const r = await fetch(base + '/chat/completions', {
        method:'POST', signal,
        headers: { 'Content-Type':'application/json', 'Authorization':'Bearer ' + c.openai.apiKey.trim() },
        body: JSON.stringify({ model: (c.openai.model || 'gpt-4o-mini').trim(), messages: msgs })
      });
      if (!r.ok) throw new Error(`OpenAI API ${r.status}`);
      const d = await r.json();
      return d.choices?.[0]?.message?.content?.trim() || '';
    }
  },
  local: {
    label: 'Local LLM',
    configured(c) { return !!(c.local.endpoint?.trim()); },
    async send(msgs, c, signal) {
      const r = await fetch(c.local.endpoint.trim(), {
        method:'POST', signal,
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ model: (c.local.model || 'llama3').trim(), messages: msgs, stream: false })
      });
      if (!r.ok) throw new Error(`Local LLM ${r.status}`);
      const d = await r.json();
      return (d.choices?.[0]?.message?.content || d.message?.content || '').trim();
    }
  },
  pubpartner: {
    label: 'PubPartner',
    configured(c) { return !!(c.pubpartner.endpoint?.trim()); },
    async send(msgs, c, signal) {
      const base = c.pubpartner.endpoint.replace(/\/+$/, '');
      const headers = { 'Content-Type':'application/json' };
      if (c.pubpartner.token?.trim()) headers['Authorization'] = 'Bearer ' + c.pubpartner.token.trim();
      const r = await fetch(base + '/api/pubpartner/turns/live', {
        method:'POST', signal, headers,
        body: JSON.stringify({ messages: msgs })
      });
      if (!r.ok) throw new Error(`PubPartner ${r.status}`);
      const d = await r.json();
      return d.reply || d.content || d.message || JSON.stringify(d);
    }
  }
};

function llmOk() { return LLM_ADAPTERS[llmCfg.provider]?.configured(llmCfg) || false; }
async function callLLM(msgs) {
  const a = LLM_ADAPTERS[llmCfg.provider];
  if (!a || !a.configured(llmCfg)) throw new Error('LLM not configured');
  abortController = new AbortController();
  try { return await a.send(msgs, llmCfg, abortController.signal); }
  finally { abortController = null; }
}
function cancelLLM() { if (abortController) { abortController.abort(); abortController = null; } }

// ── CORE STATE ─────────────────────────────────────────────────────
let coWriting = false;  // false = WRITE mode, true = COLLAB mode
let committed = [];     // finalized manuscript lines
let buffer = [];        // draft lines (collab mode)
let pool = [];          // generated lines waiting to be read
let pointer = 0;        // next line in pool
let lockedLines = new Set();
let reading = null;     // current line being read aloud
let playing = false;
let inReaction = false;
let selectedIdx = null; // selected committed line index
let editingIdx = null;  // line being edited
let generating = false;
let speaking = false;
let speechToken = 0;
let documentTitle = 'Untitled manuscript';
let documentDirty = false;
let documentHandle = null;
let chapters = [{ title: 'Chapter One', subtitle: '', startLine: 0 }];
let chatHistory = [];
const MAX_CHAT = 20;
let undoStack = [];
let redoStack = [];
const MAX_UNDO = 60;
let references = []; // { id, name, type, content, date }
let refIdCounter = 1;
let refFilter = 'all';
let reactionTimer = null;

// ── DOM REFS ───────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const pageSheets = $('pageSheets');
const manuscriptLines = $('manuscriptLines');
const manuscriptZone = $('manuscriptZone');
const soloTextarea = $('soloTextarea');
const lineNumbers = $('lineNumbers');
const draftArea = $('draftArea');
const readingIndicator = $('readingIndicator');
const chatLog = $('chatLog');
const chatInput = $('chatInput');
const contextMenu = $('contextMenu');

// ── UNDO / REDO ────────────────────────────────────────────────────
function snapshot() {
  undoStack.push({
    committed: [...committed],
    buffer: [...buffer],
    lockedLines: new Set(lockedLines),
    chapters: JSON.parse(JSON.stringify(chapters))
  });
  if (undoStack.length > MAX_UNDO) undoStack.shift();
  redoStack = [];
}
function undo() {
  if (!undoStack.length) return;
  redoStack.push({ committed: [...committed], buffer: [...buffer], lockedLines: new Set(lockedLines), chapters: JSON.parse(JSON.stringify(chapters)) });
  const s = undoStack.pop();
  committed = s.committed; buffer = s.buffer; lockedLines = s.lockedLines; chapters = s.chapters;
  soloTextarea.value = committed.join('\n');
  markDirty(); render();
}
function redo() {
  if (!redoStack.length) return;
  undoStack.push({ committed: [...committed], buffer: [...buffer], lockedLines: new Set(lockedLines), chapters: JSON.parse(JSON.stringify(chapters)) });
  const s = redoStack.pop();
  committed = s.committed; buffer = s.buffer; lockedLines = s.lockedLines; chapters = s.chapters;
  soloTextarea.value = committed.join('\n');
  markDirty(); render();
}

// ── DIRTY / AUTOSAVE ───────────────────────────────────────────────
let autosaveTimer = null;
function markDirty() {
  documentDirty = true;
  $('saveIndicator').textContent = 'unsaved';
  if (autosaveTimer) clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(writeAutosave, 3000);
}
const AUTOSAVE_DB = 'pubcast2i-autosave-v2';
function openDB() {
  return new Promise(res => {
    const req = indexedDB.open(AUTOSAVE_DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore('snaps');
    req.onsuccess = () => res(req.result);
    req.onerror = () => res(null);
  });
}
async function writeAutosave() {
  try {
    const db = await openDB(); if (!db) return;
    const payload = { title: documentTitle, ts: Date.now(), state: getDocState() };
    const tx = db.transaction('snaps', 'readwrite');
    tx.objectStore('snaps').put(payload, 'autosave_' + (Date.now() % 3));
    tx.oncomplete = () => {};
  } catch {}
}
setInterval(writeAutosave, 5 * 60 * 1000);

async function listAutosaves() {
  try {
    const db = await openDB(); if (!db) return [];
    return new Promise(res => {
      const tx = db.transaction('snaps', 'readonly');
      const store = tx.objectStore('snaps');
      const req = store.getAll();
      req.onsuccess = () => { db.close(); res((req.result || []).filter(Boolean).sort((a, b) => b.ts - a.ts)); };
      req.onerror = () => { db.close(); res([]); };
    });
  } catch { return []; }
}

// ── DOCUMENT STATE ─────────────────────────────────────────────────
function getDocState() {
  return {
    committed, buffer, pool, pointer, chapters,
    lockedLines: [...lockedLines],
    coWriting, references, reading, partnerId, conversations, conversationIds
  };
}
function docPayload() {
  return { format: '2i-document', version: 4, title: documentTitle, state: getDocState() };
}
function loadDocState(state) {
  validateDocumentState(state);
  committed = state.committed || [];
  soloTextarea.value = committed.join('\n');
  buffer = state.buffer || [];
  pool = state.pool || [];
  pointer = state.pointer || 0;
  chapters = state.chapters?.length ? state.chapters : [{ title: 'Chapter One', subtitle: '', startLine: 0 }];
  lockedLines = new Set(state.lockedLines || []);
  coWriting = !!state.coWriting || lockedLines.size > 0; updateModeUI();
  references = (state.references || []).map((r,index)=>({...r,id:index+1}));
  refIdCounter = references.length + 1;
  partnerId = state.partnerId || 'alex';
  conversations = state.conversations || {};
  conversationIds = state.conversationIds || {};
  chatHistory = conversations[partnerId] || [];
  reading = state.reading || null;
  restoreConversation();
  selectedIdx = null; editingIdx = null;
  undoStack = []; redoStack = [];
  render();
}

// ── SAVE / OPEN / EXPORT ───────────────────────────────────────────
function safeName() { return documentTitle.replace(/[\\/:*?"<>|]/g, '-').trim() || 'Untitled'; }
async function saveDocument() {
  if (documentHandle) {
    try {
      const w = await documentHandle.createWritable();
      await w.write(JSON.stringify(docPayload(), null, 2));
      await w.close();
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      return;
    } catch {}
  }
  await saveDocumentAs();
}
async function saveDocumentAs() {
  const payload = docPayload();
  if ('showSaveFilePicker' in window) {
    try {
      const h = await window.showSaveFilePicker({
        suggestedName: safeName() + '.2i',
        types: [{ description: '2i Document', accept: { 'application/json': ['.2i'] } }]
      });
      const w = await h.createWritable(); await w.write(JSON.stringify(payload, null, 2)); await w.close();
      documentHandle = h; documentDirty = false; $('saveIndicator').textContent = 'saved';
      return;
    } catch {}
  }
  // Fallback: download
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = safeName() + '.2i'; a.click(); URL.revokeObjectURL(a.href);
  documentDirty = false; $('saveIndicator').textContent = 'saved';
}
async function openDocument() {
  if ('showOpenFilePicker' in window) {
    try {
      const [h] = await window.showOpenFilePicker({
        types: [{ description: '2i Document', accept: { 'application/json': ['.2i'] } }]
      });
      const file = await h.getFile();
      const text = await file.text();
      const doc = JSON.parse(text);
      if (doc.format !== '2i-document') throw new Error('Not a 2i document');
      documentTitle = doc.title || 'Untitled';
      documentHandle = h;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
      return;
    } catch (e) { if (e.name !== 'AbortError') addChat('pp', '⚠ ' + e.message); return; }
  }
  // Fallback: file input
  const inp = document.createElement('input'); inp.type = 'file'; inp.accept = '.2i,.json';
  inp.onchange = async () => {
    const file = inp.files[0]; if (!file) return;
    try {
      const text = await file.text();
      const doc = JSON.parse(text);
      documentTitle = doc.title || 'Untitled';
      documentHandle = null;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
    } catch (e) { addChat('pp', '⚠ ' + e.message); }
  };
  inp.click();
}
function exportManuscript() {
  let md = '# ' + documentTitle + '\n\n';
  let chIdx = 0;
  committed.forEach((line, i) => {
    const ch = chapters.find(c => c.startLine === i);
    if (ch) { md += '\n## ' + ch.title + (ch.subtitle ? '\n*' + ch.subtitle + '*' : '') + '\n\n'; }
    md += line + '\n';
  });
  if (buffer.length) { md += '\n---\n*Draft:*\n\n' + buffer.join('\n') + '\n'; }
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = safeName() + '.md'; a.click(); URL.revokeObjectURL(a.href);
}
function newDocument() {
  if (documentDirty && !confirm('Discard unsaved changes?')) return;
  committed = []; buffer = []; pool = []; pointer = 0;
  lockedLines = new Set(); chapters = [{ title:'Chapter One', subtitle:'', startLine:0 }];
  selectedIdx = null; editingIdx = null; reading = null;
  documentTitle = 'Untitled Pubcast 2i Document'; documentHandle = null;
  documentDirty = false; $('saveIndicator').textContent = 'unsaved';
  undoStack = []; redoStack = []; chatHistory = [];
  chatLog.innerHTML = ''; references = [];
  render();
}

// ── MODE SWITCHING ─────────────────────────────────────────────────
function updateModeUI() {
  const badge = $('modeBadge');
  if (coWriting) {
    badge.textContent = 'Collab'; badge.className = 'mode-badge collab';
    pageSheets.classList.remove('solo-mode');
    $('collabOnlyControls').classList.remove('hidden');
    $('playbackControls').classList.remove('hidden');
    $('zoneLabel').textContent = 'Manuscript — locked';
  } else {
    badge.textContent = 'Write'; badge.className = 'mode-badge write';
    pageSheets.classList.add('solo-mode');
    $('collabOnlyControls').classList.add('hidden');
    $('playbackControls').classList.add('hidden');
    $('zoneLabel').textContent = 'Manuscript';
  }
}
function toggleMode() {
  if (coWriting && lockedLines.size) {
    addChat('notice', 'Locked lines are protected in Collab mode. Unlock the manuscript before switching to free writing.');
    return;
  }
  if (coWriting && buffer.some(line => line.trim())) {
    addChat('notice', 'Your pencil draft is still uncommitted. Commit it explicitly before switching to Write mode; nothing has moved into the manuscript.');
    draftArea.focus();
    return;
  }
  coWriting = !coWriting;
  if (!coWriting) {
    // switching to solo: merge committed into textarea
    soloTextarea.value = committed.join('\n');
    stopPlaying();
  } else {
    // switching to collab: split textarea back into committed
    const text = soloTextarea.value;
    committed = text.split('\n');
    buffer = [];
  }
  updateModeUI(); markDirty(); render();
}
$('modeBadge').onclick = toggleMode;

// ── APPROVE / LOCK / UNLOCK / CHAPTERS ─────────────────────────────
function showDraftCrossing(lines) {
  if (!document.documentElement.animate && !document.createElement('div').animate) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!lines.some(line => line.trim())) return;
  const from = draftArea.getBoundingClientRect();
  const to = manuscriptZone.getBoundingClientRect();
  if (!from.width || !to.width) return;
  const ghost = document.createElement('div');
  ghost.textContent = lines.join('\n');
  ghost.setAttribute('aria-hidden', 'true');
  ghost.style.cssText = 'position:fixed;pointer-events:none;z-index:9999;white-space:pre-wrap;overflow:hidden;max-height:140px;color:#4a4032;background:#f1e4c8;padding:4px 9px;border-radius:4px;box-shadow:0 4px 14px #0003;';
  ghost.style.left = from.left + 'px';
  ghost.style.top = (from.top + 5) + 'px';
  ghost.style.width = Math.min(from.width, 460) + 'px';
  document.body.append(ghost);
  const dy = Math.min(to.bottom - 38, from.top - 18) - from.top;
  const animation = ghost.animate([
    {transform:'translateY(0)', fontFamily:'Kalam, cursive', fontSize:'16px', opacity:1},
    {transform:`translateY(${dy * .55}px)`, fontFamily:'Kalam, cursive', fontSize:'16px', opacity:.9, offset:.55},
    {transform:`translateY(${dy}px)`, fontFamily:'Cormorant Garamond, serif', fontSize:'15px', opacity:0}
  ], {duration:750, easing:'ease-in-out'});
  animation.addEventListener('finish', () => ghost.remove(), {once:true});
  animation.addEventListener('cancel', () => ghost.remove(), {once:true});
}
function approveBuffer() {
  if (!buffer.some(line => line.trim())) return;
  const approved = [...buffer];
  showDraftCrossing(approved);
  snapshot();
  committed.push(...buffer);
  buffer = []; draftArea.value = '';
  selectedIdx = null; editingIdx = null;
  markDirty(); render();
  closeMenu();
}
function lockScene() {
  if (!coWriting) toggleMode();
  snapshot();
  // Lock lines from the last chapter start to end of committed
  const lastChapter = [...chapters].reverse().find(c => c.startLine <= committed.length - 1);
  const start = lastChapter ? lastChapter.startLine : 0;
  for (let i = start; i < committed.length; i++) lockedLines.add(i);
  markDirty(); render();
}
function lockAll() {
  if (!coWriting) toggleMode();
  snapshot();
  committed.forEach((_, i) => lockedLines.add(i));
  markDirty(); render();
}
function unlockSelected() {
  if (selectedIdx === null) { addChat('pp', 'Select a line first, then unlock it.'); return; }
  snapshot();
  lockedLines.delete(selectedIdx);
  markDirty(); render();
}
function newChapter() {
  snapshot();
  const num = chapters.length + 1;
  const title = prompt('Chapter title:', 'Chapter ' + numberToWord(num));
  if (!title) return;
  const sub = prompt('Subtitle (optional):', '') || '';
  chapters.push({ title, subtitle: sub, startLine: committed.length + buffer.length });
  markDirty(); render();
}
function numberToWord(n) {
  const w = ['One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve'];
  return w[n - 1] || String(n);
}

$('approveBtn').onclick = approveBuffer;
$('lockSceneBtn').onclick = lockScene;
$('lockAllBtn').onclick = lockAll;
$('unlockBtn').onclick = unlockSelected;
$('newChapterBtn').onclick = newChapter;
$('exportBtn').onclick = () => { exportManuscript(); closeMenu(); };

// ── AI GENERATION ──────────────────────────────────────────────────
async function generateMore() {
  if (generating || chatSending || !llmOk()) return false;
  const sourceDocument = documentId, sourcePartner = partnerId;
  generating = true; $('genBtn').disabled = true;
  $('statusText').textContent = 'generating…';
  try {
    const context = committed.slice(-8).join('\n') + (buffer.length ? '\n' + buffer.join('\n') : '');
    const prompt = 'Continue this manuscript with the next 2-4 sentences of prose. Return ONLY the new prose, each sentence on its own line.\n\nContext:\n' + context;
    const reply = await callLLM([{ role: 'user', content: prompt }]);
    if (sourceDocument !== documentId || sourcePartner !== partnerId) return false;
    const lines = reply.split(/\n+/).map(l => l.trim()).filter(Boolean);
    if (lines.length) { pool = pool.concat(lines); return true; }
  } catch (e) {
    if (e.name !== 'AbortError') addChat('pp', '⚠ Generation failed: ' + e.message);
  } finally {
    generating = false; $('genBtn').disabled = false; render();
  }
  return false;
}
$('genBtn').onclick = () => { if (!playing && !generating) { closeMenu(); tick(); } };

// ── PLAYBACK / TICK ────────────────────────────────────────────────
async function tick() {
  if (reading) { buffer.push(reading.text); markDirty(); reading = null; }
  if (pointer >= pool.length && llmOk() && !generating) {
    const got = await generateMore();
    if (!got) { stopPlaying(); render(); return; }
  }
  if (pointer < pool.length) {
    reading = { text: pool[pointer] }; pointer++;
    markDirty(); render();
    if (playing) {
      speechRead(reading.text, () => {
        if (!playing || !reading) return;
        inReaction = true; render();
        reactionTimer = setTimeout(() => { inReaction = false; if (playing) tick(); }, 6000);
      });
    }
  } else { stopPlaying(); }
  render();
}
function startPlaying() {
  if (playing) return;
  playing = true; inReaction = false;
  if (!reading) tick();
  else speechRead(reading.text, () => {
    inReaction = true; render();
    reactionTimer = setTimeout(() => { inReaction = false; tick(); }, 6000);
  });
  render();
}
function stopPlaying() {
  cancelSpeech(); cancelLLM();
  if (reactionTimer) { clearTimeout(reactionTimer); reactionTimer = null; }
  inReaction = false; playing = false; render();
}

$('playBtn').onclick = () => playing ? stopPlaying() : startPlaying();
$('stopBtn').onclick = stopPlaying;
$('skipBtn').onclick = () => {
  if (inReaction) { inReaction = false; if (reactionTimer) clearTimeout(reactionTimer); if (playing) tick(); return; }
  if (playing && reading) { cancelSpeech(); tick(); }
  else if (!playing) tick();
};

// ── SPEECH ─────────────────────────────────────────────────────────
function speechRead(text, done) {
  if (!('speechSynthesis' in window)) { if (done) done(); return; }
  const token = ++speechToken;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = parseFloat($('speedSlider').value) || 1;
  u.onstart = () => { if (token !== speechToken) return; speaking = true; render(); };
  u.onend = () => { if (token !== speechToken) return; speaking = false; render(); if (done) done(); };
  u.onerror = () => { if (token !== speechToken) return; speaking = false; render(); if (done) done(); };
  window.speechSynthesis.speak(u);
}
function cancelSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  speechToken++; speaking = false;
}

// ── CHAT ───────────────────────────────────────────────────────────
function escHtml(s) { return s.replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
function addChat(who, text, thinking) {
  const div = document.createElement('div');
  div.className = 'chat-msg ' + (who === 'you' ? 'you' : 'pp') + (thinking ? ' thinking' : '');
  div.innerHTML = '<span class="who">' + (who === 'you' ? 'You' : 'PubPartner') + '</span>' + escHtml(text);
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}
let chatSending = false;
async function sendChat() {
  if (chatSending) return;
  const v = chatInput.value.trim(); if (!v) return;
  chatSending = true; addChat('you', v); chatInput.value = '';
  chatHistory.push({ role: 'user', content: v });
  if (chatHistory.length > MAX_CHAT * 2) chatHistory = chatHistory.slice(-MAX_CHAT * 2);
  $('chatSendBtn').disabled = true;
  const thinkEl = addChat('pp', '…thinking…', true);
  try {
    const sys = 'You are PubPartner, a creative writing collaborator. Be concise and helpful.\nManuscript context:\n' + committed.slice(-6).join('\n');
    const reply = await callLLM([{ role: 'user', content: sys }, ...chatHistory.slice(-MAX_CHAT)]);
    thinkEl.remove(); addChat('pp', reply || '(empty)');
    chatHistory.push({ role: 'assistant', content: reply || '' });
  } catch (e) {
    thinkEl.remove();
    if (e.name !== 'AbortError') addChat('pp', '⚠ ' + e.message);
  } finally { $('chatSendBtn').disabled = false; chatSending = false; }
}
$('chatSendBtn').onclick = sendChat;
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

// Voice input
const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = $('chatMicBtn');
if (SpeechAPI) {
  const rec = new SpeechAPI(); rec.interimResults = true;
  let listening = false, baseText = '';
  rec.onresult = e => {
    let t = '';
    for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript;
    chatInput.value = (baseText + ' ' + t).trim();
  };
  rec.onend = () => { listening = false; micBtn.classList.remove('listening'); };
  micBtn.onclick = () => {
    if (listening) { rec.stop(); return; }
    baseText = chatInput.value.trim(); rec.start(); listening = true; micBtn.classList.add('listening');
  };
} else {
  micBtn.disabled = true; micBtn.title = 'Speech not supported in this browser';
}

// ── REFERENCE ARCHIVE ──────────────────────────────────────────────
function addReference(name, type, content) {
  references.push({ id: refIdCounter++, name, type: type || 'notes', content, date: new Date().toLocaleDateString() });
  markDirty(); renderRefs();
}
function deleteReference(id) {
  references = references.filter(r => r.id !== id);
  markDirty(); renderRefs();
}
function renderRefs() {
  const container = $('refListContainer');
  const search = $('refSearchInput').value.toLowerCase();
  container.innerHTML = '';
  const filtered = references.filter(r => {
    if (refFilter !== 'all' && r.type !== refFilter) return false;
    if (search && !r.name.toLowerCase().includes(search) && !r.content.toLowerCase().includes(search)) return false;
    return true;
  });
  if (!filtered.length) {
    container.innerHTML = '<div style="font-size:11px; color:var(--parchment-soft); padding:8px; text-align:center;">No references yet</div>';
    return;
  }
  const icons = { chapter:'📖', research:'🔬', notes:'📝', character:'👤' };
  filtered.forEach(r => {
    const el = document.createElement('div'); el.className = 'ref-item';
    const icon=document.createElement('div');icon.className='ref-icon';icon.textContent=icons[r.type] || '📄';
    const meta=document.createElement('div');meta.className='ref-meta';
    for(const [key,value] of [['name',r.name],['type',r.type || 'notes'],['date',r.date || '']]) {
      const row=document.createElement('div');row.className='ref-'+key;row.textContent=String(value);meta.append(row);
    }
    const actions=document.createElement('div');actions.className='ref-actions';
    const view=document.createElement('button');view.className='ref-action-btn';view.title='View';view.textContent='📋';view.onclick=()=>viewRef(r.id);
    const remove=document.createElement('button');remove.className='ref-action-btn';remove.title='Delete';remove.textContent='✕';remove.onclick=()=>confirmReferenceDelete(r.id);
    actions.append(view,remove);el.append(icon,meta,actions);
    container.appendChild(el);
  });
}
function viewRef(id) {
  const r = references.find(x => x.id === id); if (!r) return;
  $('refViewerTitle').textContent = r.name;
  $('refViewerBody').textContent = r.content;
  $('refViewer').classList.add('open');
}
function closeRefViewer() { $('refViewer').classList.remove('open'); }
function setRefFilter(btn, filter) {
  refFilter = filter;
  document.querySelectorAll('.ref-tab').forEach(t => {const active=t.dataset.filter===filter;t.classList.toggle('active',active);t.setAttribute('aria-pressed',String(active));});
  renderRefs();
}
function filterRefs() { renderRefs(); }
$('refSearchInput').addEventListener('input', renderRefs);

$('addRefBtn').onclick = () => {
  $('refNameInput').value = '';
  $('refTypeInput').value = 'notes';
  $('refContentInput').value = '';
  openModal('addRefModalBackdrop');
  setTimeout(() => $('refNameInput').focus(), 100);
};
$('addRefSaveBtn').onclick = () => {
  const name = $('refNameInput').value.trim();
  if (!name) { $('refNameInput').focus(); return; }
  addReference(name, $('refTypeInput').value, $('refContentInput').value);
  closeModal('addRefModalBackdrop');
};

// ── FIND & REPLACE ─────────────────────────────────────────────────
$('frReplaceAllBtn').onclick = () => {
  const find = $('frFind').value;
  const replace = $('frReplace').value;
  if (!find || find.length === 0) {
    $('frResult').textContent = 'Enter text to find.';
    $('frResult').className = 'test-result err';
    return;
  }
  snapshot();
  let count = 0;
  // Replace in committed
  committed = committed.map((l, i) => {
    if (lockedLines.has(i)) return l;
    if (l.includes(find)) { count += l.split(find).length - 1; return l.split(find).join(replace); }
    return l;
  });
  // Replace in buffer
  buffer = buffer.map(l => {
    if (l.includes(find)) { count += l.split(find).length - 1; return l.split(find).join(replace); }
    return l;
  });
  // Replace in reading
  if (reading?.text?.includes(find)) {
    count += reading.text.split(find).length - 1;
    reading.text = reading.text.split(find).join(replace);
  }
  // Sync the editor from the same replacement pass (do not count it twice).
  if (!coWriting) {
    soloTextarea.value = committed.join('\n');
  }
  $('frResult').textContent = count + ' replacement' + (count !== 1 ? 's' : '') + ' made';
  $('frResult').className = 'test-result ok';
  markDirty(); render();
};

// ── CONTEXT MENU ───────────────────────────────────────────────────
function showContextMenu(e, idx) {
  e.preventDefault();
  selectedIdx = idx;
  const locked = lockedLines.has(idx);
  $('ctxLock').style.display = locked ? 'none' : '';
  $('ctxUnlock').style.display = locked ? '' : 'none';
  contextMenu.classList.add('open');
  const cmW = contextMenu.offsetWidth || 170;
  const cmH = contextMenu.offsetHeight || 200;
  const cx = Math.min(e.clientX, window.innerWidth - cmW - 8);
  const cy = Math.min(e.clientY, window.innerHeight - cmH - 8);
  contextMenu.style.left = Math.max(0, cx) + 'px';
  contextMenu.style.top = Math.max(0, cy) + 'px';
  render();
}
document.addEventListener('click', () => contextMenu.classList.remove('open'));

$('ctxEdit').onclick = () => {
  if (selectedIdx === null) return;
  if (lockedLines.has(selectedIdx)) { addChat('pp', 'Unlock the line first.'); return; }
  editingIdx = selectedIdx; render();
};
$('ctxInsertAbove').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); committed.splice(selectedIdx, 0, '');
  // Shift locked lines
  const newLocked = new Set();
  lockedLines.forEach(i => newLocked.add(i >= selectedIdx ? i + 1 : i));
  lockedLines = newLocked;
  // Shift chapter startLines
  chapters.forEach(c => { if (c.startLine >= selectedIdx) c.startLine++; });
  editingIdx = selectedIdx;
  markDirty(); render();
};
$('ctxInsertBelow').onclick = () => {
  if (selectedIdx === null) return;
  const insertAt = selectedIdx + 1;
  snapshot(); committed.splice(insertAt, 0, '');
  const newLocked = new Set();
  lockedLines.forEach(i => newLocked.add(i >= insertAt ? i + 1 : i));
  lockedLines = newLocked;
  chapters.forEach(c => { if (c.startLine >= insertAt) c.startLine++; });
  editingIdx = insertAt; selectedIdx = insertAt;
  markDirty(); render();
};
$('ctxLock').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); lockedLines.add(selectedIdx); markDirty(); render();
};
$('ctxUnlock').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); lockedLines.delete(selectedIdx); markDirty(); render();
};
$('ctxDelete').onclick = () => {
  if (selectedIdx === null) return;
  if (lockedLines.has(selectedIdx)) { addChat('pp', 'Unlock the line before deleting.'); return; }
  snapshot(); committed.splice(selectedIdx, 1);
  const newLocked = new Set();
  lockedLines.forEach(i => { if (i < selectedIdx) newLocked.add(i); else if (i > selectedIdx) newLocked.add(i - 1); });
  lockedLines = newLocked;
  chapters.forEach(c => { if (c.startLine > selectedIdx) c.startLine--; });
  selectedIdx = null; markDirty(); render();
};

// ── RENDER ──────────────────────────────────────────────────────────
function render() {
  // Status
  $('statusDot').className = 'status-dot ' + (playing ? 'playing' : 'paused');
  $('statusText').textContent = playing ? (speaking ? 'reading aloud…' : 'reading…') : (generating ? 'generating…' : 'idle');
  $('playBtn').textContent = playing ? '⏸' : '▶';
  $('playBtn').classList.toggle('active', playing);
  $('docTitleDisplay').textContent = documentTitle;
  $('paperTitle').textContent = documentTitle;

  // Word count
  let allText;
  if (coWriting) {
    allText = committed.join(' ') + ' ' + buffer.join(' ');
  } else {
    allText = soloTextarea.value;
  }
  const wc = allText.trim().split(/\s+/).filter(Boolean).length;
  $('wordCount').textContent = wc.toLocaleString() + ' words';
  $('mcWordProgress').textContent = wc.toLocaleString() + ' words';

  // Manuscript control status
  const allLocked = committed.length > 0 && committed.every((_, i) => lockedLines.has(i));
  $('mcDraftStatus').textContent = allLocked ? 'Locked' : 'Active';
  const targetWc = 50000; // reasonable novel target
  const pct = Math.min(100, Math.round((wc / targetWc) * 100));
  $('mcPercent').textContent = pct + '%';
  $('mcProgressFill').style.width = pct + '%';

  // LLM pill
  if (llmOk()) {
    $('llmPill').textContent = LLM_ADAPTERS[llmCfg.provider].label + ' settings';
    $('llmPill').className = 'llm-pill';
  } else {
    $('llmPill').textContent = 'Connect model';
    $('llmPill').className = 'llm-pill';
  }

  if (coWriting) {
    renderManuscriptLines();
    renderReading();
    draftArea.value = buffer.join('\n');
  } else {
    updateLineNumbers();
  }

  renderRefs();
}

function renderManuscriptLines() {
  manuscriptLines.innerHTML = '';
  let lineNum = 1;
  committed.forEach((text, i) => {
    // Check for chapter heading
    const ch = chapters.find(c => c.startLine === i);
    if (ch) {
      const heading = document.createElement('div'); heading.className = 'chapter-heading';
      heading.textContent = ch.title; manuscriptLines.appendChild(heading);
      if (ch.subtitle) {
        const sub = document.createElement('div'); sub.className = 'chapter-subtitle';
        sub.textContent = ch.subtitle; manuscriptLines.appendChild(sub);
      }
      const divider = document.createElement('div'); divider.className = 'chapter-divider';
      divider.innerHTML = '✦ ✦ ✦'; manuscriptLines.appendChild(divider);
    }

    if (editingIdx === i) {
      // Editing mode
      const wrap = document.createElement('div'); wrap.className = 'm-line selected';
      wrap.innerHTML = `<span class="line-num">${lineNum}</span>`;
      const editDiv = document.createElement('div'); editDiv.className = 'm-line-edit'; editDiv.style.flex = '1';
      const ta = document.createElement('textarea'); ta.value = text; ta.rows = 2;
      ta.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); snapshot(); committed[i] = ta.value; editingIdx = null; markDirty(); render(); }
        if (e.key === 'Escape') { editingIdx = null; render(); }
      });
      editDiv.appendChild(ta); wrap.appendChild(editDiv);
      manuscriptLines.appendChild(wrap);
      setTimeout(() => ta.focus(), 0);
    } else {
      const div = document.createElement('div');
      div.className = 'm-line' + (selectedIdx === i ? ' selected' : '') + (lockedLines.has(i) ? ' locked' : '');
      div.innerHTML = `<span class="line-num">${lineNum}</span>${escHtml(text)}`;
      div.onclick = () => { selectedIdx = (selectedIdx === i) ? null : i; render(); };
      div.oncontextmenu = e => showContextMenu(e, i);
      div.ondblclick = () => {
        if (lockedLines.has(i)) { addChat('pp', 'Unlock the line to edit it.'); return; }
        editingIdx = i; render();
      };
      manuscriptLines.appendChild(div);
    }
    lineNum++;
  });

  // Preserve the author's reading position when selecting or locking a line.
}

function renderReading() {
  readingIndicator.innerHTML = '';
  if (reading) {
    const div = document.createElement('div');
    div.className = 'reading-line' + (inReaction ? ' reaction' : '');
    div.textContent = reading.text;
    // Accept/reject buttons
    const btns = document.createElement('div');
    btns.style.cssText = 'display:flex; gap:6px; margin:4px 0 0 55px;';
    const acceptBtn = document.createElement('button'); acceptBtn.className = 'mc-btn primary';
    acceptBtn.textContent = '✓ Accept'; acceptBtn.style.cssText = 'padding:3px 10px; font-size:9px;';
    acceptBtn.onclick = () => { buffer.push(reading.text); reading = null; markDirty(); render(); };
    const rejectBtn = document.createElement('button'); rejectBtn.className = 'mc-btn danger';
    rejectBtn.textContent = '✕ Reject'; rejectBtn.style.cssText = 'padding:3px 10px; font-size:9px;';
    rejectBtn.onclick = () => { reading = null; render(); };
    btns.appendChild(acceptBtn); btns.appendChild(rejectBtn);
    readingIndicator.appendChild(div);
    if (!playing) readingIndicator.appendChild(btns);
  }
}

function updateLineNumbers() {
  const lines = soloTextarea.value.split('\n');
  lineNumbers.innerHTML = lines.map((_, i) => (i + 1)).join('<br>');
}

// Sync solo textarea scroll with line numbers
soloTextarea.addEventListener('scroll', () => { lineNumbers.scrollTop = soloTextarea.scrollTop; });
soloTextarea.addEventListener('input', () => {
  updateLineNumbers();
  keepChapterPositions(committed.join('\n'),soloTextarea.value);
  committed = soloTextarea.value.split('\n');
  markDirty();
  render();
});
draftArea.addEventListener('input', () => {
  buffer = draftArea.value.split('\n');
  markDirty();
});

// ── LLM MODAL ──────────────────────────────────────────────────────
function showLLMFields() {
  const p = $('llmProvider').value;
  document.querySelectorAll('.llm-fields').forEach(el => el.classList.remove('active'));
  const map = { claude:'llmFieldsClaude', openai:'llmFieldsOpenai', local:'llmFieldsLocal', pubpartner:'llmFieldsPubpartner' };
  if (map[p]) $(map[p]).classList.add('active');
}
$('llmProvider').onchange = showLLMFields;

function openLLMModal() {
  $('llmProvider').value = llmCfg.provider;
  $('llmClaudeKey').value = llmCfg.claude.apiKey || '';
  $('llmClaudeModel').value = llmCfg.claude.model || '';
  $('llmOpenaiKey').value = llmCfg.openai.apiKey || '';
  $('llmOpenaiEndpoint').value = llmCfg.openai.endpoint || '';
  $('llmOpenaiModel').value = llmCfg.openai.model || '';
  $('llmLocalEndpoint').value = llmCfg.local.endpoint || '';
  $('llmLocalModel').value = llmCfg.local.model || '';
  $('llmPPEndpoint').value = llmCfg.pubpartner.endpoint || '';
  $('llmPPToken').value = llmCfg.pubpartner.token || '';
  $('llmTestResult').textContent = '';
  showLLMFields();
  openModal('llmModalBackdrop');
}
$('llmSaveBtn').onclick = () => {
  llmCfg = {
    provider: $('llmProvider').value,
    claude: { apiKey: $('llmClaudeKey').value, model: $('llmClaudeModel').value },
    openai: { apiKey: $('llmOpenaiKey').value, endpoint: $('llmOpenaiEndpoint').value, model: $('llmOpenaiModel').value },
    local: { endpoint: $('llmLocalEndpoint').value, model: $('llmLocalModel').value },
    pubpartner: { endpoint: $('llmPPEndpoint').value, token: $('llmPPToken').value }
  };
  saveLLM(llmCfg); closeModal('llmModalBackdrop'); render();
};
$('llmCancelBtn').onclick = () => closeModal('llmModalBackdrop');
$('llmTestBtn').onclick = async () => {
  $('llmTestResult').textContent = 'Testing…'; $('llmTestResult').className = 'test-result';
  // Temporarily apply modal values
  const tempCfg = {
    provider: $('llmProvider').value,
    claude: { apiKey: $('llmClaudeKey').value, model: $('llmClaudeModel').value },
    openai: { apiKey: $('llmOpenaiKey').value, endpoint: $('llmOpenaiEndpoint').value, model: $('llmOpenaiModel').value },
    local: { endpoint: $('llmLocalEndpoint').value, model: $('llmLocalModel').value },
    pubpartner: { endpoint: $('llmPPEndpoint').value, token: $('llmPPToken').value }
  };
  const adapter = LLM_ADAPTERS[tempCfg.provider];
  if (!adapter || !adapter.configured(tempCfg)) {
    $('llmTestResult').textContent = 'Not configured — fill in the fields above.';
    $('llmTestResult').className = 'test-result err'; return;
  }
  try {
    const reply = await adapter.send([{ role: 'user', content: 'Say "connected" and nothing else.' }], tempCfg);
    $('llmTestResult').textContent = '✓ Connected: ' + reply.slice(0, 60);
    $('llmTestResult').className = 'test-result ok';
  } catch (e) {
    $('llmTestResult').textContent = '✕ ' + e.message;
    $('llmTestResult').className = 'test-result err';
  }
};
$('llmPill').onclick = openLLMModal;

// ── MENUS & MODALS ─────────────────────────────────────────────────
const modalFocus=new Map();
function openModal(id) {
  for(const other of document.querySelectorAll('.modal-backdrop.open'))if(other.id!==id)closeModal(other.id);
  modalFocus.set(id,document.activeElement);$(id).classList.add('open');
  document.querySelector('.app-shell').inert=true;closeMenu();contextMenu.classList.remove('open');
  setTimeout(()=>{if($(id).classList.contains('open'))$(id).querySelector('input:not([type=hidden]),select,textarea,button')?.focus();},0);
}
function closeModal(id) {
  $(id).classList.remove('open');
  if(!document.querySelector('.modal-backdrop.open'))document.querySelector('.app-shell').inert=false;
  const previous=modalFocus.get(id);modalFocus.delete(id);if(previous?.isConnected)previous.focus();
}
function closeMenu() { $('hamburgerMenu').classList.remove('open'); }

// Click backdrop to close any modal
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) closeModal(backdrop.id);
  });
});
function toggleSection(id) { $(id).classList.toggle('collapsed'); }

$('menuToggle').onclick = e => { e.stopPropagation(); $('hamburgerMenu').classList.toggle('open'); };
document.addEventListener('click', e => {
  if (!$('hamburgerMenu').contains(e.target) && e.target !== $('menuToggle')) closeMenu();
});

$('sidebarToggle').onclick = () => {
  $('mainArea').classList.toggle('sidebar-hidden');
};

$('hmNewDoc').onclick = () => { closeMenu(); newDocument(); };
$('hmOpenDoc').onclick = () => { closeMenu(); openDocument(); };
$('hmSaveAs').onclick = () => { closeMenu(); saveDocumentAs(); };
$('hmFindReplace').onclick = () => { $('frResult').textContent = ''; openModal('frModalBackdrop'); };
$('frCloseBtn').onclick = () => closeModal('frModalBackdrop');
$('hmLLMSettings').onclick = () => { closeMenu(); openLLMModal(); };
$('hmKeyboardHelp').onclick = () => { closeMenu(); openModal('kbModalBackdrop'); };
$('hmRenameDoc').onclick = () => {
  closeMenu(); $('renameInput').value = documentTitle; openModal('renameModalBackdrop');
  setTimeout(() => $('renameInput').focus(), 100);
};
$('renameSaveBtn').onclick = () => {
  documentTitle = $('renameInput').value.trim() || 'Untitled';
  markDirty(); render(); closeModal('renameModalBackdrop');
};
$('docTitleDisplay').onclick = () => {
  $('renameInput').value = documentTitle; openModal('renameModalBackdrop');
  setTimeout(() => $('renameInput').focus(), 100);
};
$('saveBtn').onclick = saveDocument;

// Autosave restore
$('hmRestoreAutosave').onclick = async () => {
  closeMenu();
  const list = await listAutosaves();
  const container = $('autosaveList');
  if (!list.length) {
    container.innerHTML = 'No autosaves found.';
  } else {
    container.innerHTML = '';
    list.forEach((snap, i) => {
      const btn = document.createElement('button');
      btn.className = 'mc-btn';
      btn.style.cssText = 'width:100%; text-align:left; margin:4px 0;';
      btn.textContent = (snap.title || 'Untitled') + ' — ' + new Date(snap.ts).toLocaleString();
      btn.onclick = () => {
        try {
          validateDocumentState(snap.state);
          documentTitle = snap.title || 'Untitled';
          loadDocState(snap.state); markDirty();
          closeModal('autosaveModalBackdrop');render();
        } catch(error) { addChat('notice',error.message); }
      };
      container.appendChild(btn);
    });
  }
  openModal('autosaveModalBackdrop');
};

// ── KEYBOARD SHORTCUTS ─────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // Escape: close modals/menus
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(m => closeModal(m.id));
    contextMenu.classList.remove('open');
    closeMenu();
    if (editingIdx !== null) { editingIdx = null; render(); }
    return;
  }
  if (e.ctrlKey || e.metaKey) {
    if (e.key === 's') { e.preventDefault(); saveDocument(); }
    if (e.key === 'z') { e.preventDefault(); undo(); }
    if (e.key === 'y') { e.preventDefault(); redo(); }
    if (e.key === 'f') { e.preventDefault(); $('frResult').textContent = ''; openModal('frModalBackdrop'); setTimeout(() => $('frFind').focus(), 100); }
    if (e.key === 'e') { e.preventDefault(); exportManuscript(); }
    if (e.key === 'Enter' && coWriting) { e.preventDefault(); approveBuffer(); }
    if (e.key === 'g' && coWriting) { e.preventDefault(); if (!generating) tick(); }
  }
});

// ── CANVAS: LANTERN LIGHT ──────────────────────────────────────────
(function initLantern() {
  if(document.documentElement.dataset.reachArtwork==='original')return;
  const frame = $('notebookFrame'); if (!frame) return;
  const canvas = $('lanternCanvas');
  const ctx = canvas.getContext('2d', { alpha: true });
  let w = 0, h = 0, mx = 300, my = 100, raf = 0;
  function resize() {
    w = frame.clientWidth; h = frame.clientHeight;
    canvas.width = w; canvas.height = h; draw();
  }
  function draw() {
    ctx.clearRect(0, 0, w, h);
    const g = ctx.createRadialGradient(mx, my, 0, mx, my, 380);
    g.addColorStop(0, 'rgba(238,207,131,0.12)');
    g.addColorStop(0.35, 'rgba(238,207,131,0.04)');
    g.addColorStop(0.7, 'rgba(238,207,131,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  }
  frame.addEventListener('pointermove', e => {
    const r = frame.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top;
    if (!raf) raf = requestAnimationFrame(() => { draw(); raf = 0; });
  });
  window.addEventListener('resize', resize); resize();
})();

// ── CANVAS: SPIRAL SPINE ───────────────────────────────────────────
function drawSpine() {
  if(document.documentElement.dataset.reachArtwork==='original')return;
  const canvas = $('spineCanvas'); if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height, cx = W * 0.55, rx = Math.min(18, W * 0.34);
  const pitch = 22;

  // Background shadow
  ctx.fillStyle = 'rgba(0,0,0,0.4)';
  ctx.fillRect(cx - rx - 6, 0, rx * 2 + 12, H);

  for (let i = 0; i < H / pitch + 1; i++) {
    const y = i * pitch + 6;
    // Coil shadow
    ctx.beginPath(); ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 5;
    ctx.moveTo(cx - rx, y + 2); ctx.lineTo(cx + rx, y + 7);
    ctx.stroke();
    // Coil body
    ctx.beginPath();
    ctx.strokeStyle = '#bca36f'; ctx.lineWidth = 3.5;
    ctx.moveTo(cx - rx, y); ctx.lineTo(cx + rx, y + 5);
    ctx.stroke();
    // Highlight
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255,240,200,0.35)'; ctx.lineWidth = 1;
    ctx.moveTo(cx - rx + 1, y - 1); ctx.lineTo(cx + rx - 1, y + 4);
    ctx.stroke();
  }
}
window.addEventListener('load', drawSpine);
window.addEventListener('resize', drawSpine);

// ── INIT ───────────────────────────────────────────────────────────
function init() {
  updateModeUI();
  render();
  drawSpine();

  // Load any existing autosave notification
  listAutosaves().then(list => {
    if (list.length && !committed.length && !soloTextarea.value.trim()) {
      addChat('pp', 'I found autosaved work. Use Menu → Restore autosave to recover it.');
    }
  });
}
// ── DRAG & DROP ────────────────────────────────────────────────────
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', async e => {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  if (file.name.endsWith('.2i') || file.name.endsWith('.json')) {
    try {
      const text = await file.text();
      const doc = JSON.parse(text);
      if (doc.format !== '2i-document') { addChat('pp', '⚠ Not a 2i document.'); return; }
      if (documentDirty && !confirm('Discard unsaved changes?')) return;
      documentTitle = doc.title || 'Untitled';
      documentHandle = null;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
      addChat('pp', 'Loaded: ' + documentTitle);
    } catch (err) { addChat('pp', '⚠ ' + err.message); }
  } else if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
    // Import as reference
    try {
      const text = await file.text();
      addReference(file.name, 'research', text);
      addChat('pp', 'Added "' + file.name + '" to Reference Archive.');
    } catch (err) { addChat('pp', '⚠ ' + err.message); }
  }
});

// Reach's storage and partner adapter are installed below before initialization.
</script>
<style>.world-room-section{flex:0 0 auto;max-height:45%;min-height:0;overflow:auto}.world-room-section summary{cursor:pointer;list-style:none}.world-room-section .world-chat-widget{height:270px;padding:6px 9px}#worldRoomSection:not([open]) > .world-chat-widget{display:none}.world-room-section .world-chat-widget [data-world-messages]{min-height:60px}</style>
<script src="/static/world_chat_widget.js"></script>
<script src="./2i-assets/button-bindings.js"></script>
<script src="./2i-assets/reach.js"></script>
<script src="./2i-assets/artwork.js"></script>
<script src="./2i-assets/phone.js"></script>
<script src="./2i-assets/reader.js"></script>
<script src="./2i-assets/desk-controls.js"></script>
</body>
</html>
````

## modules/hub.py

SHA-256: `092506475f186689c2df675af0d2118e2a5e915d08a26fe2fa7c1d36837459af`

````text
# PubCast AI — hub.py
# Copyright © 2024–2026 Josie Curtsey Cobbley (Joshua Cobbley)
# Rearview Foresight LLC — All Rights Reserved
# Feic Mo Chroí — See My Heart

from __future__ import annotations
import asyncio
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Set
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from .persistence import read_json, write_json
from .models import ProductionState
from .route_security import auth_enforced
from .chat_commit_store import ChatCommitStore

logger = logging.getLogger(__name__)

class Hub:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.user_display_name: Dict[str, str] = {}  # uid -> display name (optional; for presence)
        self._ws_meta: Dict[int, Dict[str, Any]] = {}  # id(ws) -> {uid, username, role, room}
        # production state on disk
        self.prod_file = self.data_dir / "global" / "production.json"
        if not self.prod_file.parent.exists():
            self.prod_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.prod_file.exists():
            write_json(self.prod_file, ProductionState().model_dump())
        self.on_chat_callback = None
        self.blackbox_witness = None  # Wired after BlackBox runtime starts.
        self.eq_monitoring_recorder = None  # Optional development evidence recorder.
        self.dm_authorizer = None  # Bound to persistent consent by chat route install.
        self._chat_commit_store = None  # Lazy, installation-local SQLite receipts.

    def get_production_state(self) -> Dict[str, Any]:
        return read_json(self.prod_file)

    def update_production_state(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_production_state()
        # merge shallowly
        current.update(patch or {})
        # validate through model
        model = ProductionState(**current)
        write_json(self.prod_file, model.model_dump())
        return model.model_dump()

    async def connect(
        self,
        ws: WebSocket,
        room: str,
        *,
        uid: str = "anon",
        username: str = "anon",
        role: str = "guest",
        authenticated: bool = False,
        _already_accepted: bool = False,
        dm_peer: str | None = None,
    ) -> None:
        # Recheck even when the caller already resolved consent: another worker
        # may have revoked it while the WebSocket handshake was in progress.
        if room.startswith(("dm____", "dmv2_")):
            if not self._dm_recipient_authorized({
                "uid": uid, "dm_peer": dm_peer, "authenticated": authenticated
            }):
                raise PermissionError("No current permission to join private room")
        if not _already_accepted:
            await ws.accept()
        self.rooms.setdefault(room, set()).add(ws)
        self._ws_meta[id(ws)] = {"uid": uid, "username": username, "role": role,
                                  "room": room, "authenticated": authenticated,
                                  "dm_peer": dm_peer}
        if uid != "anon":
            self.user_display_name[uid] = username
        # Do not load the entire lifetime of a busy room into memory or block
        # the event loop while reading its history. The bounded tail reader is
        # also used by the REST history endpoint.
        history_path = self._log_path(room)
        recent = (await asyncio.to_thread(self._read_history_sync, history_path, 50)
                  if history_path.exists() else [])
        if recent:
            if dm_peer and not self._dm_recipient_authorized({
                "uid": uid, "dm_peer": dm_peer, "authenticated": authenticated
            }):
                await self.disconnect(ws, room)
                return
            await ws.send_text(json.dumps({"type": "history", "payload": recent}))
        # announce presence with names
        await self._broadcast(room, {"type": "presence", "payload": self._presence_payload(room)})

    async def disconnect(self, ws: WebSocket, room: str) -> None:
        try:
            self.rooms.get(room, set()).discard(ws)
            self._ws_meta.pop(id(ws), None)
        finally:
            await self._broadcast(room, {"type": "presence", "payload": self._presence_payload(room)})
            if ws.application_state == WebSocketState.CONNECTED:
                try:
                    await ws.close()
                except Exception:
                    pass

    async def close_room_connections(self, room: str) -> int:
        """Evict a revoked private-room membership from all current sockets."""
        peers = list(self.rooms.get(room, set()))
        for ws in peers:
            await self.disconnect(ws, room)
        return len(peers)

    def participants(self, room: str) -> List[Dict[str, Any]]:
        """Return list of participant metadata dicts for a room."""
        result = []
        for ws in self.rooms.get(room, set()):
            meta = self._ws_meta.get(id(ws))
            if meta:
                result.append({"uid": meta["uid"], "username": meta["username"], "role": meta["role"]})
        return result

    def _presence_payload(self, room: str) -> Dict[str, Any]:
        return {
            "room": room,
            "count": len(self.rooms.get(room, set())),
            "participants": self.participants(room),
        }

    async def broadcast_system_event(self, event: Dict[str, Any]):
        for room, conns in self.rooms.items():
            await self._broadcast(room, event)

    async def send_private_event(self, user_ids: Set[str], event: Dict[str, Any]) -> int:
        """Deliver a private notification only to verified sockets of its addressees.

        Presence in a public room, an unverified client_id or a legacy Hub
        connection is *not* sufficient proof of identity. A user connected in
        multiple rooms receives the notification once per physical socket.
        Offline recipients can retrieve pending DM requests via the HTTP API.
        """
        recipients = {uid.casefold() for uid in user_ids if isinstance(uid, str) and uid}
        if not recipients:
            return 0
        wire = json.dumps(event)
        delivered = 0
        visited: Set[int] = set()
        for connections in list(self.rooms.values()):
            for ws in list(connections):
                key = id(ws)
                if key in visited:
                    continue
                visited.add(key)
                meta = self._ws_meta.get(key)
                if (not meta or not meta.get("authenticated") or
                        str(meta.get("uid") or "").casefold() not in recipients):
                    continue
                if ws.application_state != WebSocketState.CONNECTED:
                    continue
                try:
                    await ws.send_text(wire)
                    delivered += 1
                except Exception:
                    logger.warning("Private notification delivery failed for authenticated socket")
        return delivered

    async def broadcast_presence_update(self, user_id: str, display_name: str):
        # Could be extended to map sockets to user ids to show names; minimal for now
        self.user_display_name[user_id] = display_name
        await self.broadcast_system_event({"type": "user_update", "payload": {"user_id": user_id, "display_name": display_name}})

    async def handle_message(self, ws: WebSocket, room: str, raw: str):
        # Expect raw to be JSON string
        try:
            data = json.loads(raw)
        except Exception as exc:
            logger.debug("hub: malformed WS frame in room=%s: %s", room, exc)
            return
        if not isinstance(data, dict):
            await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "JSON object required"}}))
            return
        typ = data.get("type")
        if typ == "chat":
            meta = self._ws_meta.get(id(ws))
            text = data.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 10000:
                await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "Invalid chat text"}}))
                return
            if auth_enforced() and (not meta or not meta.get("authenticated")):
                await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "Authentication required"}}))
                return
            client_id = data.get("client_message_id")
            if client_id is not None:
                try:
                    client_id = ChatCommitStore.validate_client_id(client_id)
                except ValueError as exc:
                    await ws.send_text(json.dumps({"type": "error", "payload": {"msg": str(exc)}}))
                    return
            # Legacy public clients may still provide a display name in local
            # development. A verified connection must never be impersonated by
            # a sender/user_id field supplied in a WebSocket frame.
            verified = bool(meta and meta.get("authenticated"))
            sender_id = (meta["uid"] if verified else
                         data.get("user_id") or data.get("user") or
                         (meta["uid"] if meta else "anon"))
            sender = (meta["username"] if verified else data.get("user", "anon"))
            if client_id is not None:
                # A keyed legacy WebSocket send follows the same durable
                # receipt path as REST. Never trust the author's identity in
                # the frame; the verified socket determines its receipt key.
                try:
                    receipt = await self.post_chat_message(room, str(sender_id), text,
                                                           client_message_id=client_id)
                except ValueError as exc:
                    await ws.send_text(json.dumps({"type": "error", "payload": {"msg": str(exc)}}))
                    return
                await ws.send_text(json.dumps({"type": "chat_receipt", "payload": {
                    "message_id": receipt["message_id"], "client_message_id": client_id,
                    "duplicate": receipt["duplicate"], "warnings": receipt["warnings"],
                }}))
                return
            payload = {
                "message_id": uuid.uuid4().hex,
                "t": time.time(),
                "room": room,
                "user": sender,
                "user_id": sender_id,
                "text": text,
            }
            await asyncio.to_thread(ChatCommitStore._append_durable, self._log_path(room), payload)
            self._witness_chat(payload)
            await self._broadcast(room, {"type": "chat", "payload": payload})
            if callable(self.on_chat_callback):
                try:
                    await self.on_chat_callback(payload)
                except Exception:
                    # The user's text is already on disk; a failed AI response
                    # must not turn a successful send into an apparent failure.
                    logger.exception("Chat AI callback failed after message %s was persisted", payload["message_id"])
        elif typ == "signal":
            # extension point for invites / cues
            await self._broadcast(room, {"type": "signal", "payload": data.get("payload", {})})
        elif typ == "production_state":
            # allow control room to push updates via ws (UI convenience)
            meta = self._ws_meta.get(id(ws))
            if auth_enforced() and (not meta or not meta.get("authenticated") or
                                    meta.get("role") not in {"mod", "owner"}):
                await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "Production control requires mod or owner"}}))
                return
            patch = data.get("payload", {})
            if not isinstance(patch, dict):
                await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "Invalid production patch"}}))
                return
            updated = self.update_production_state(patch)
            await self.broadcast_system_event({"type": "production_state", "payload": updated})
        else:
            # echo unknown
            await ws.send_text(json.dumps({"type": "error", "payload": {"msg": "unknown type"}}))

    def _dm_recipient_authorized(self, meta: Dict[str, Any] | None) -> bool:
        """Check the live, persistent permission on every private delivery.

        A database outage fails closed. In particular, no private frame may be
        forwarded based only on old in-memory WebSocket membership.
        """
        if (not meta or not meta.get("authenticated") or not meta.get("dm_peer")
                or not callable(self.dm_authorizer)):
            return False
        try:
            return bool(self.dm_authorizer(meta["uid"], meta["dm_peer"]))
        except Exception:
            logger.exception("Private room authorization unavailable; denying outgoing frame")
            return False

    async def _broadcast(self, room: str, msg: Dict[str, Any]):
        dead: List[WebSocket] = []
        revoked: List[WebSocket] = []
        wire = json.dumps(msg)
        private = room.startswith(("dm____", "dmv2_"))
        for ws in list(self.rooms.get(room, set())):
            meta = self._ws_meta.get(id(ws))
            # A revocation on another server worker must not leave this worker
            # broadcasting new private frames to an old authorized socket.
            # Fail closed if the local authorizer was never wired.
            if private and not self._dm_recipient_authorized(meta):
                revoked.append(ws)
                continue
            try:
                if ws.application_state == WebSocketState.CONNECTED:
                    await ws.send_text(wire)
                else:
                    dead.append(ws)
            except Exception as exc:
                logger.debug("hub: broadcast send failed to client in room=%s: %s", room, exc)
                dead.append(ws)
        for ws in dead:
            self.rooms.get(room, set()).discard(ws)
            self._ws_meta.pop(id(ws), None)
        for ws in revoked:
            if ws in self.rooms.get(room, set()):
                await self.disconnect(ws, room)

    def _log_path(self, room: str) -> Path:
        # Room IDs are filesystem components. Never permit separators, parent
        # traversal, Windows drive syntax, or Windows special device names.
        if not isinstance(room, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,159}", room):
            raise ValueError("Invalid room identifier")
        if room.upper().split(".", 1)[0] in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
            raise ValueError("Reserved room identifier")
        logs_dir = self.data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir / f"{room}.jsonl"

    # ── Methods required by BotManager ───────────────────────────────────────

    async def is_user_in_room(self, room: str, user_id: str) -> bool:
        """Return True if any live WebSocket in the room belongs to user_id.

        Now backed by real per-connection identity tracking (_ws_meta) instead
        of the prior conservative approximation. Falls back to the old
        "has a display name registered this session" check only if no live
        connection metadata matches, preserving bot-safe behavior for any
        caller that hasn't been updated to pass real uid/username/role into
        connect() yet.
        """
        for ws in self.rooms.get(room, set()):
            meta = self._ws_meta.get(id(ws))
            if meta and meta.get("uid") == user_id:
                return True
        return user_id in self.user_display_name

    async def get_recent_history(self, room: str, limit: int = 12) -> list:
        """Return the last `limit` chat messages from a room's log.

        File I/O is dispatched to a thread via run_in_executor so the async
        event loop is never blocked - safe to call from Jeremy's watcher loop.
        """
        history_path = self._log_path(room)
        if not history_path.exists():
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._read_history_sync, history_path, limit
        )

    def _read_history_sync(self, path: Path, limit: int) -> list:
        """Read only the tail, not the entire lifetime of a busy shared room.

        JSONL messages are UTF-8 and newline-terminated. The backward read uses
        byte chunks, then decodes only complete trailing lines; malformed lines
        cannot prevent recovery of the remaining messages.
        """
        if limit <= 0:
            return []
        limit = min(int(limit), 500)
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            position = handle.tell()
            chunks = []
            newline_count = 0
            while position and newline_count <= limit:
                size = min(8192, position)
                position -= size
                handle.seek(position)
                block = handle.read(size)
                chunks.append(block)
                newline_count += block.count(b"\n")
        recent = b"".join(reversed(chunks)).splitlines()[-limit:]
        result = []
        for line in recent:
            try:
                result.append(json.loads(line.decode("utf-8")))
            except (ValueError, UnicodeDecodeError):
                continue
        return result

    def _witness_chat(self, payload: Dict[str, Any]) -> bool:
        witness = self.blackbox_witness
        if witness is None:
            return False
        try:
            receipt = witness.record_event(
                "chat.message", source="chat", actor=str(payload.get("user_id") or "anon"),
                data={"room": payload.get("room"), "text": payload.get("text"),
                      "t": payload.get("t"), "message_id": payload.get("message_id")},
            )
            if receipt is None:
                logger.warning("Chat message persisted in room %s but BlackBox witness failed", payload.get("room"))
                return False
            return True
        except Exception:
            # A failed independent witness is important, but it must not
            # change the HTTP send result after the canonical room log
            # committed. Recovery/reconciliation is still an open feature.
            logger.exception("BlackBox witness failed after chat message %s was persisted", payload.get("message_id"))
            return False

    async def post_chat_message(self, room: str, user_id: str, text: str,
                                client_message_id: str | None = None) -> Dict[str, Any]:
        """Commit room text first, then try the independent side effects.

        A UUID-keyed retry reuses the existing persisted message without a
        second broadcast or bot callback. Legacy unkeyed sends retain their
        existing contract and must not be described as idempotent.
        """
        display_name = self.user_display_name.get(user_id, user_id)
        if client_message_id is not None:
            if self._chat_commit_store is None:
                self._chat_commit_store = ChatCommitStore(self.data_dir)
            payload, duplicate = await asyncio.to_thread(
                self._chat_commit_store.commit, room, user_id, text,
                client_message_id, display_name)
            if duplicate:
                return {**payload, "duplicate": True, "warnings": [
                    "Message already saved; the previous BlackBox/AI delivery state is not rechecked"
                ]}
        else:
            payload = {
                "message_id": uuid.uuid4().hex, "t": time.time(),
                "room": room, "user": display_name, "user_id": user_id,
                "text": text,
            }
            await asyncio.to_thread(ChatCommitStore._append_durable, self._log_path(room), payload)
        witnessed = self._witness_chat(payload)
        if self.eq_monitoring_recorder is not None:
            try:
                self.eq_monitoring_recorder.record_message(payload)
            except Exception:
                logger.exception("EQ recorder failed after chat message %s was persisted", payload["message_id"])
        await self._broadcast(room, {"type": "chat", "payload": payload})
        warnings = [] if witnessed else ["BlackBox witness unavailable for this message"]
        if callable(self.on_chat_callback):
            try:
                await self.on_chat_callback(payload)
            except Exception:
                logger.exception("Chat AI callback failed after message %s was persisted", payload["message_id"])
                warnings.append("AI response could not be started for this message")
        payload["warnings"] = warnings
        payload["duplicate"] = False
        return payload

    def invalidate_user_cache(self, user_id: str) -> None:
        """No-op cache invalidation hook (extended in future presence layer)."""
        self.user_display_name.pop(user_id, None)
````

## tests/test_reach_editor.cjs

SHA-256: `ecbdab24ebe469ede8a4d63d1e70c903a0eb1bf72f86a5058f6e64483b00a290`

````text
// Hermetic DOM/state tests, not a browser rendering or live model test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {JSDOM, VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root,'2i/index.html'),'utf8');
// Separate script evaluations preserve real classic-script declaration order.
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).concat(['button-bindings.js','reach.js','artwork.js','phone.js','reader.js','desk-controls.js'].map(file=>fs.readFileSync(path.join(root,'2i/2i-assets',file),'utf8')));
const hotspotMap=JSON.parse(fs.readFileSync(path.join(root,'2i/2i-assets/hotspots.json'),'utf8'));
const documents = new Map();
let requests=[], failProvider=false;
const clickedHotspots=new Set();
const pause=()=>new Promise(resolve=>setTimeout(resolve,30));
function harness(storage={},settings={}) {
  const errors=[];
  const vc=new VirtualConsole(); vc.on('jsdomError',e=>errors.push(e.message));
  const dom=new JSDOM(html,{url:settings.url||'http://reach.test/writers-room',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});
  const w=dom.window, context=dom.getInternalVMContext();
  if(settings.width)Object.defineProperty(w,'innerWidth',{value:settings.width,configurable:true});
  if(settings.height)Object.defineProperty(w,'innerHeight',{value:settings.height,configurable:true});
  for(const file of ['reach.css','artwork.css','phone.css','reader.css']) {const style=w.document.createElement('style');style.textContent=fs.readFileSync(path.join(root,'2i/2i-assets',file),'utf8');w.document.head.append(style);}
  w.document.addEventListener('click',event=>{const target=event.target.closest('[data-hotspot]');if(target)clickedHotspots.add(target.id);},true);
  for(const [key,value] of Object.entries(storage))w.localStorage.setItem(key,value);
  w.requestAnimationFrame=()=>0; w.cancelAnimationFrame=()=>{}; w.confirm=()=>true;w.prompt=()=> '24000';
  w.HTMLCanvasElement.prototype.getContext=()=>new Proxy({}, {get:(_,key)=>key==='createLinearGradient'||key==='createRadialGradient'?()=>({addColorStop(){}}):()=>{}});
  const downloads=[];w.Blob=Blob;
  w.URL.createObjectURL=blob=>{downloads.push(blob);return 'blob:test';}; w.URL.revokeObjectURL=()=>{};
  w.HTMLAnchorElement.prototype.click=function(){};
  w.fetch=async(url,options={})=>{
    const p=new URL(url,'http://reach.test').pathname, body=options.body?JSON.parse(options.body):null;
    let value={},status=200;
    if(p==='/2i-assets/hotspots.json')value=hotspotMap;
    else if(p==='/api/auth/status')value={auth_enforced:false,setup_required:false};
    else if(p==='/api/writers-room/config')value={user_id:'test-author',provider:{provider:'ollama',model:'test-only'}};
    else if(p==='/api/pubpartner/profiles/friend')value={profiles:[{id:'alex',display_name:'Alex'},{id:'craig',display_name:'Craig'}]};
    else if(p==='/api/pubpartner/providers/status')value={available:true,provider:'ollama'};
    else if(p==='/api/pubpartner/turns/live'){
      requests.push(body);
      if(failProvider){status=503;value={ok:false,provider_result:{ok:false,error:'synthetic unavailable provider'}};}
      else value={ok:true,reply:'Synthetic test reply',provider_result:{ok:true,provider:'ollama',model:'test-only'}};
    } else if(p.startsWith('/api/writers-room/documents/')) {
      if(settings.failDocuments)throw Error('Synthetic disconnected document service');
      if(settings.holdNextPut&&options.method==='PUT'){settings.holdNextPut=false;await new Promise(resolve=>settings.releasePut=resolve);}
      const id=p.split('/').pop(), old=documents.get(id);
      if(options.method==='PUT') {
        if((old?.revision||0)!==body.expected_revision){status=409;value={detail:{message:'Revision conflict'}};}
        else {value={...body,id,revision:(old?.revision||0)+1,updated:Date.now()/1000};documents.set(id,value);}
      } else if(old)value=old;else{status=404;value={detail:'document not found'};}
    } else if(p==='/api/writers-room/documents'){
      if(settings.failDocuments)throw Error('Synthetic disconnected document service');
      value={documents:[...documents.values()]};
    }
    else throw Error('Unhandled fake API path: '+p);
    return {ok:status<400,status,json:async()=>value};
  };
  for(const script of scripts)vm.runInContext(script,context);
  // Production bindings must work with inline HTML event handlers disabled.
  return {dom,w,errors,downloads,run:script=>vm.runInContext(script,context),storage:()=>Object.fromEntries(Object.keys(w.localStorage).map(k=>[k,w.localStorage.getItem(k)]))};
}
const deadline=setTimeout(()=>{console.error('FAIL: editor test did not finish');process.exit(1);},30000);
(async()=>{
  let h=harness(); await pause();
  await h.w.reachArtworkReady;
  assert.equal(h.w.document.querySelector('.app-shell').dataset.artworkReady,'true');
  for(const control of hotspotMap.controls){
    const button=h.w.document.getElementById(control.id);
    assert.equal(typeof button.onclick,'function',control.id);
    assert.equal(button.style.left,control.bounds[0]+'px');
    assert(button.getAttribute('aria-label'));
  }
  const {createHash}=require('node:crypto');
  assert.equal(createHash('sha256').update(fs.readFileSync(path.join(root,'2i/2i-assets/writers-room-art.webp'))).digest('hex'),hotspotMap.image.sha256);
  const x=h.w.document.getElementById('saveBtn').style.left;
  Object.defineProperty(h.w,'innerWidth',{value:672,configurable:true});Object.defineProperty(h.w,'innerHeight',{value:448,configurable:true});
  h.w.dispatchEvent(new h.w.Event('resize'));
  assert.equal(h.w.document.querySelector('.app-shell').style.getPropertyValue('--art-scale'),'0.5');
  assert.equal(h.w.document.getElementById('saveBtn').style.left,x);
  console.log('PASS: original image hash, labeled button map and shared scaling');
  h.run(String.raw`soloTextarea.value='A lantern glowed.\n\n  Keep these spaces.  '; soloTextarea.dispatchEvent(new Event('input'));`);
  await h.run('saveDocument()');
  assert.equal(h.run('documentDirty'),false);
  assert.match(h.w.document.getElementById('wordCount').textContent,/6 words/);
  const id=h.run('documentId');
  assert.equal(documents.get(id).state.committed[2],'  Keep these spaces.  ');
  h.run(`documentTitle='The Lantern'; addReference('Harbor map','research','An invented shore.'); markDirty();`);
  await h.run('saveDocument()');
  const saved=h.storage();h.dom.window.close();
  h=harness(saved);await pause();
  assert.equal(h.w.document.getElementById('soloTextarea').value,'A lantern glowed.\n\n  Keep these spaces.  ');
  assert.equal(h.w.document.getElementById('paperTitle').textContent,'The Lantern');
  assert.equal(h.run('references[0].content'),'An invented shore.');
  console.log('PASS: words, title and references survive save and reload');

  h.run(`$('chatInput').value='The harbor is Lumen.';`);await h.run('sendChat()');
  h.run(`$('partnerSelect').value='craig';`);await h.run('switchPartner()');
  assert.equal(h.run('chatHistory.length'),0);
  h.run(`$('chatInput').value='Craig, help me with this scene.';`);await h.run('sendChat()');
  assert.equal(requests.at(-1).friend,'craig');
  assert.equal(requests.at(-1).messages.length,1);
  assert(!JSON.stringify(requests.at(-1).messages).includes('The harbor is Lumen.'));
  assert.equal(requests.at(-1).allow_fallback,false);
  assert(requests.at(-1).task.manuscript_context.includes('Keep these spaces.'));
  h.run(`$('partnerSelect').value='alex';`);await h.run('switchPartner()');
  assert.equal(h.run('chatHistory[0].content'),'The harbor is Lumen.');
  h.run(`$('chatInput').value='Keep that name.';`);await h.run('sendChat()');
  assert.equal(requests.at(-1).messages.length,3);
  console.log('PASS: partner changes isolate conversations; full history reaches the adapter');

  failProvider=true;
  const count=h.run('chatHistory.length');
  h.run(`$('chatInput').value='Try again.';`);await h.run('sendChat()');
  assert.equal(h.run('chatHistory.length'),count+1);
  assert.match(h.w.document.getElementById('chatLog').textContent,/Could not reach the model/);
  assert.equal(h.w.document.getElementById('chatSendBtn').disabled,false);
  console.log('PASS: unavailable model displays an error without inventing an assistant turn');

  h.run('lockAll()');
  assert.equal(h.run('coWriting'),true);
  h.run('toggleMode()');assert.equal(h.run('coWriting'),true);
  h.run(`$('frFind').value='lantern';$('frReplace').value='candle';$('frReplaceAllBtn').click();`);
  assert.equal(h.run('committed[0]'),'A lantern glowed.');
  assert.match(h.w.document.getElementById('frResult').textContent,/0 replacements/);
  console.log('PASS: locked manuscript text resists free editing and replace-all');

  const lockedWords=h.run('JSON.stringify(committed)');
  h.w.document.getElementById('photoInsert').click();
  assert.equal(h.run('JSON.stringify(committed)'),lockedWords);
  assert.equal(h.run('buffer.at(-1)'),'Synthetic test reply');
  assert.equal(h.w.document.getElementById('photoInsert').disabled,true);
  h.w.document.getElementById('photoCommitMenu').click();
  assert.equal(h.run('committed.at(-1)'),'Synthetic test reply');
  h.w.document.getElementById('photoCharacters').click();
  assert(h.w.document.getElementById('photoCollection').classList.contains('open'));
  assert.equal(h.w.document.getElementById('photoCollectionTitle').textContent,'Characters');
  h.run(`addReference('Meet at the dock','idea','A scene premise.');`);
  assert.match(h.w.document.getElementById('photoIdeas').textContent,/Meet at the dock/);
  h.w.document.getElementById('newChapterBtn').click();
  h.w.document.getElementById('photoSceneTitleInput').value='Chapter Two';
  h.w.document.getElementById('photoSceneSave').click();
  assert.equal(h.w.document.getElementById('photoSceneCount').textContent,'SCENE 2 OF 2');
  h.w.document.getElementById('photoPrevious').click();
  assert.equal(h.w.document.getElementById('photoSceneCount').textContent,'SCENE 1 OF 2');
  assert.equal(h.run('committed[0]'),'A lantern glowed.');
  console.log('PASS: image hotspots insert to draft, commit, open collections and navigate scenes');

  const before=h.run('JSON.stringify(getDocState())');
  await assert.rejects(h.run(`importDocument({text:async()=>JSON.stringify({format:'2i-document',version:4,title:'Bad import',state:{committed:'broken'}})})`));
  assert.equal(h.run('JSON.stringify(getDocState())'),before);
  console.log('PASS: malformed import leaves the manuscript intact');

  h.run(`addReference('Literal markup','<img src=x onerror=alert(1)>','<b>A fictional reference</b>');`);
  assert.equal(h.w.document.querySelector('#refListContainer img'),null);
  assert.match(h.w.document.getElementById('refListContainer').textContent,/<img src=x/);
  console.log('PASS: imported reference metadata stays inert text');

  await h.run('saveDocument()');
  const current=documents.get(h.run('documentId'));current.revision++;
  h.run(`documentTitle='A simultaneous edit';markDirty();`);await h.run('saveDocument()');
  assert.equal(h.run('saveConflict'),true);
  assert.notEqual(documents.get(h.run('documentId')).title,'A simultaneous edit');
  assert.match(h.w.document.getElementById('saveIndicator').textContent,/Changed elsewhere/);
  assert.equal(h.errors.filter(e=>!e.includes('indexedDB')).length,0,h.errors.join('\n'));
  h.dom.window.close();
  console.log('PASS: stale revision protects the server copy');

  failProvider=false;h=harness();await h.w.reachStarted;await h.w.reachArtworkReady;
  const click=id=>h.w.document.getElementById(id).click();
  click('photoManuscript');assert.equal(h.w.document.activeElement.id,'soloTextarea');
  click('modeBadge');assert.equal(h.run('coWriting'),true);click('modeBadge');assert.equal(h.run('coWriting'),false);
  click('menuToggle');assert(h.w.document.getElementById('hamburgerMenu').classList.contains('open'));
  click('sidebarToggle');assert(h.w.document.getElementById('deskSettings').classList.contains('open'));click('deskModelSettings');assert(h.w.document.getElementById('llmModalBackdrop').classList.contains('open'));
  assert.equal(h.w.document.querySelector('.app-shell').inert,true);
  assert.equal(h.w.getComputedStyle(h.w.document.getElementById('reachModel')).backgroundColor,'rgb(25, 20, 14)');
  click('llmTestBtn');await pause();assert.match(h.w.document.getElementById('llmTestResult').textContent,/Service configured/);
  click('llmSaveBtn');await pause();assert(!h.w.document.getElementById('llmModalBackdrop').classList.contains('open'));
  assert.equal(h.w.document.querySelector('.app-shell').inert,false);
  click('sidebarToggle');h.w.document.dispatchEvent(new h.w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));assert.equal(h.w.document.querySelector('.app-shell').inert,false);
  h.run(`soloTextarea.value='Scene one.\\n';soloTextarea.dispatchEvent(new Event('input'));addReference('Chapter sketch','chapter','A chapter.');addReference('Harbor map','research','A shore.');addReference('Quill notes','notes','A quill.');addReference('Mara','character','A mariner.');addReference('The islands','worldbuilding','An invented world.');`);
  for(const [id,title] of [['photoCharacters','Characters'],['photoWorldbuilding','Worldbuilding'],['photoNotes','Notes']]) {
    click(id);assert.equal(h.w.document.getElementById('photoCollectionTitle').textContent,title);click('photoCollectionClose');
  }
  for(const [id,name] of [['photoRefChapter','Chapter sketch'],['photoRefResearch','Harbor map'],['photoRefNotes','Quill notes']]) {
    click(id);const rows=h.w.document.querySelectorAll('#refListContainer .ref-item');assert.equal(rows.length,1);assert(rows[0].textContent.includes(name));
  }
  click('photoRefAll');assert.equal(h.w.document.querySelectorAll('#refListContainer .ref-item').length,5);
  h.w.document.getElementById('refSearchInput').value='quill';click('photoSearch');
  assert.equal(h.w.document.querySelectorAll('#refListContainer .ref-item').length,1);
  assert.match(h.w.document.getElementById('refListContainer').textContent,/Quill notes/);
  h.w.document.getElementById('refSearchInput').value='';click('photoSearch');
  click('addRefBtn');h.w.document.getElementById('refNameInput').value='Added through the picture';h.w.document.getElementById('refContentInput').value='Preserved reference';click('addRefSaveBtn');
  assert(h.run(`references.some(r=>r.name==='Added through the picture')`));
  click('photoAddIdea');assert.equal(h.w.document.getElementById('refTypeInput').value,'idea');
  h.w.document.getElementById('refNameInput').value='The return';h.w.document.getElementById('refContentInput').value='Return to the harbor.';click('addRefSaveBtn');
  h.w.document.querySelector('#photoIdeas button').click();assert.equal(h.w.document.getElementById('refViewerTitle').textContent,'The return');
  click('photoManuscript');assert(!h.w.document.getElementById('refViewer').classList.contains('open'));
  click('photoAllIdeas');assert.equal(h.w.document.getElementById('photoCollectionTitle').textContent,'Scene ideas');click('photoCollectionClose');
  click('newChapterBtn');h.w.document.getElementById('photoSceneTitleInput').value='Second scene';click('photoSceneSave');
  h.run(`soloTextarea.value+='Second scene words.';soloTextarea.dispatchEvent(new Event('input'));`);
  click('photoPrevious');assert.equal(h.run('photoScene'),0);
  click('photoNext');assert.equal(h.run('photoScene'),1);
  click('photoOutline');assert.equal(h.w.document.querySelectorAll('#photoCollectionBody button').length,2);
  h.w.document.querySelector('#photoCollectionBody button').click();assert.equal(h.run('photoScene'),0);
  h.run(`soloTextarea.value=soloTextarea.value.replace('Scene one.','First line.\\nExtra line.');soloTextarea.dispatchEvent(new Event('input'));`);
  assert.equal(h.run('chapters[1].startLine'),2);
  click('photoNext');assert.equal(h.w.document.getElementById('soloTextarea').selectionStart,h.run(`soloTextarea.value.indexOf('Second scene words.')`));
  click('lockSceneBtn');assert(h.run('lockedLines.has(2)'));assert(!h.run('lockedLines.has(0)'));
  click('lockSceneBtn');assert.equal(h.run('lockedLines.size'),0);
  click('photoLockMode');assert(h.w.document.getElementById('photoLockOptions').classList.contains('open'));
  h.w.document.querySelector('#photoLockOptionsBody button').click();assert.equal(h.run('coWriting'),false);
  h.w.document.getElementById('chatInput').value='Suggest a line.';click('chatSendBtn');await pause();assert.equal(h.run('chatHistory.length'),2);
  click('photoDismiss');assert.equal(h.w.document.getElementById('photoInsert').disabled,true);
  h.w.document.getElementById('chatInput').value='One more.';click('chatSendBtn');await pause();click('photoInsert');assert.equal(h.run('buffer.at(-1)'),'Synthetic test reply');
  click('saveBtn');await h.run('saveDocument()');assert.equal(h.run('documentDirty'),false);
  click('exportBtn');assert.match(await h.downloads.at(-1).text(),/Second scene words/);
  click('hmSaveAs');const exported=JSON.parse(await h.downloads.at(-1).text());assert.equal(exported.format,'2i-document');assert.equal(exported.state.buffer.at(-1),'Synthetic test reply');
  const priorLeft=h.w.document.getElementById('saveBtn').style.left;
  click('photoHotspotMenu');assert(h.w.document.querySelector('.app-shell').classList.contains('show-hotspots'));
  assert.equal(h.w.document.getElementById('saveBtn').style.left,priorLeft);
  click('photoFullSizeMenu');assert.equal(h.w.getComputedStyle(h.w.document.querySelector('.app-shell')).transform,'none');click('photoFullSizeMenu');
  for(const control of hotspotMap.controls) {
    const computed=h.w.getComputedStyle(h.w.document.getElementById(control.id));
    assert.notEqual(computed.display,'none',control.id);assert.equal(computed.position,'absolute',control.id);
    assert(clickedHotspots.has(control.id),'Control was not clicked: '+control.id);
  }
  assert.equal(h.errors.length,0,h.errors.join('\n'));h.w.close();
  console.log('PASS: all '+hotspotMap.controls.length+' pictured controls clicked, with navigation, settings, search, archive, locks, chat, draft, save and exports checked');
  console.log('PASS: chapter destinations follow edits made before them; clickable-area display preserves coordinates');

  const timing={holdNextPut:true};h=harness({},timing);await h.w.reachStarted;await h.w.reachArtworkReady;
  h.run(`soloTextarea.value='Before edit';soloTextarea.dispatchEvent(new Event('input'));`);
  const originalId=h.run('documentId'),firstSave=h.run('saveDocument()');await pause();assert.equal(typeof timing.releasePut,'function');
  h.run(`soloTextarea.value='Latest edit made during saving';soloTextarea.dispatchEvent(new Event('input'));`);
  const switchDocument=h.run('newDocument()');timing.releasePut();await firstSave;await switchDocument;
  assert.equal(documents.get(originalId).state.committed[0],'Latest edit made during saving');
  assert.notEqual(h.run('documentId'),originalId);
  console.log('PASS: switching manuscripts waits for edits made while a save was in progress');
  timing.failDocuments=true;
  h.run(`soloTextarea.value='Offline manuscript A';soloTextarea.dispatchEvent(new Event('input'));`);await h.run('saveDocument()');
  const offlineA=h.run('documentId');await h.run('newDocument()');
  h.run(`soloTextarea.value='Offline manuscript B';soloTextarea.dispatchEvent(new Event('input'));`);await h.run('saveDocument()');
  const offlineB=h.run('documentId');await h.run('showShelf()');
  const recovery=h.w.document.querySelector('#reachShelfList button[data-document-id="'+offlineA+'"][data-source="browser"]');assert(recovery);recovery.click();await pause();
  assert.equal(h.run('documentId'),offlineA);assert.equal(h.w.document.getElementById('soloTextarea').value,'Offline manuscript A');
  assert.equal(h.run(`stored(RECOVERY_KEY+':'+${JSON.stringify(offlineB)},null).state.committed[0]`),'Offline manuscript B');
  const recoveryStorage=h.storage();h.w.close();h=harness(recoveryStorage,timing);await h.w.reachStarted;await h.w.reachArtworkReady;
  assert.equal(h.w.document.getElementById('soloTextarea').value,'Offline manuscript A');assert.equal(h.errors.length,0,h.errors.join('\n'));h.w.close();
  console.log('PASS: offline manuscript copies remain separately recoverable through switching and reload');

  h=harness({}, {url:'http://reach.test/writers-room?view=phone',width:390,height:844});
  await h.w.reachStarted;await h.w.reachPhoneReady;
  const phone=h.w.reachPhone,phoneClick=id=>h.w.document.getElementById(id).click();
  assert.equal(phone.active,true);assert.equal(phone.panel,'write');
  assert.equal(h.w.document.getElementById('phonePanel_partner').hidden,true);
  const phoneEditor=h.w.document.getElementById('soloTextarea');
  h.run(`soloTextarea.value='Written on a phone.\\n  Keep my spaces.  ';soloTextarea.dispatchEvent(new Event('input'));`);
  const phoneId=h.run('documentId');
  for(const control of hotspotMap.controls){
    const node=h.w.document.getElementById(control.id),style=h.w.getComputedStyle(node);
    assert(h.w.document.getElementById('phoneRoom').contains(node),control.id);
    assert.equal(h.w.document.querySelectorAll('#'+control.id).length,1,control.id);
    assert.equal(typeof node.onclick,'function',control.id);
    assert.equal(style.position,'static',control.id);
    assert(Number.parseFloat(style.minHeight)>=48,control.id+' must be touch-sized');
    assert(node.textContent.trim(),control.id+' needs a visible phone caption');
  }
  assert.equal(h.w.getComputedStyle(phoneEditor).fontSize,'var(--reach-manuscript-size,18px)');
  assert.equal(h.w.document.documentElement.style.getPropertyValue('--reach-manuscript-size'),'18px');
  phoneClick('saveBtn');await h.run('saveDocument()');assert.equal(documents.get(phoneId).state.committed[1],'  Keep my spaces.  ');
  phoneClick('phoneTab_partner');assert.equal(phone.panel,'partner');
  h.w.document.getElementById('chatInput').value='A fictional scene suggestion, please.';phoneClick('chatSendBtn');await pause();
  assert.equal(h.run('chatHistory.at(-1).content'),'Synthetic test reply');
  phoneClick('photoInsert');assert.equal(phone.panel,'write');assert.equal(h.w.document.activeElement.id,'draftArea');
  assert.equal(h.run('buffer.at(-1)'),'Synthetic test reply');phoneClick('phoneCommit');assert.equal(h.run('committed.at(-1)'),'Synthetic test reply');
  console.log('PASS: phone view reuses all 26 controls with readable captions, 48px minimum heights, writing, save and partner-to-draft actions');

  phoneClick('phoneTab_archive');assert.equal(phone.panel,'archive');
  h.run(`addReference('Phone research','research','Saved from my phone.');`);
  h.w.document.getElementById('refSearchInput').value='phone';phoneClick('photoSearch');
  assert.match(h.w.document.getElementById('refListContainer').textContent,/Phone research/);
  h.w.document.querySelector('#refListContainer .ref-action-btn[title="View"]').click();
  assert.equal(phone.panel,'write');assert.equal(h.w.document.getElementById('refViewerBody').textContent,'Saved from my phone.');h.run('closeRefViewer()');
  phoneClick('sidebarToggle');assert(h.w.document.getElementById('deskSettings').classList.contains('open'));phoneClick('deskModelSettings');assert(h.w.document.getElementById('llmModalBackdrop').classList.contains('open'));
  assert.equal(h.w.document.querySelector('.app-shell').inert,true);h.run("closeModal('llmModalBackdrop')");assert.equal(h.w.document.querySelector('.app-shell').inert,false);
  const wordsBeforeSwitch=h.run('JSON.stringify(getDocState())');phoneClick('phoneDesktop');
  assert.equal(phone.active,false);assert.equal(h.w.document.getElementById('soloTextarea'),phoneEditor);
  assert.equal(h.run('JSON.stringify(getDocState())'),wordsBeforeSwitch);assert.equal(h.run('documentId'),phoneId);
  for(const control of hotspotMap.controls){const node=h.w.document.getElementById(control.id);assert.equal(node.style.left,control.bounds[0]+'px');assert.equal(h.w.getComputedStyle(node).position,'absolute');}
  phoneClick('photoPhoneMenu');assert.equal(phone.active,true);assert.equal(h.w.document.getElementById('soloTextarea'),phoneEditor);
  assert.equal(h.run('JSON.stringify(getDocState())'),wordsBeforeSwitch);
  phoneClick('exportBtn');assert.match(await h.downloads.at(-1).text(),/Written on a phone/);
  phoneClick('phoneShelf');await pause();assert(h.w.document.getElementById('reachShelf').classList.contains('open'));h.run("closeModal('reachShelf')");
  console.log('PASS: phone archive, settings, exports and shelf work; desktop/phone switches preserve the exact editor, unsaved state and original coordinates');

  const tab=h.w.document.getElementById('phoneTab_write');tab.dispatchEvent(new h.w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
  assert.equal(phone.panel,'partner');assert.equal(h.w.document.activeElement.id,'phoneTab_partner');
  for(const [width,height] of [[320,568],[360,800],[390,844],[430,932],[844,390],[390,390]]){
    Object.defineProperty(h.w,'innerWidth',{value:width,configurable:true});Object.defineProperty(h.w,'innerHeight',{value:height,configurable:true});
    h.w.dispatchEvent(new h.w.Event('resize'));
    assert.equal(h.w.document.documentElement.style.getPropertyValue('--phone-height'),height+'px');assert.equal(phone.active,true);
    assert.equal(h.w.getComputedStyle(h.w.document.querySelector('.app-shell')).transform,'none');
  }
  assert.equal(h.errors.length,0,h.errors.join('\n'));h.w.close();
  h=harness({}, {width:390,height:844});await h.w.reachStarted;await h.w.reachPhoneReady;assert.equal(h.w.reachPhone.active,true);h.w.close();
  h=harness({}, {url:'http://reach.test/writers-room?view=desktop',width:390,height:844});await h.w.reachStarted;await h.w.reachPhoneReady;assert.equal(h.w.reachPhone.active,false);h.w.close();
  console.log('PASS: phone tabs support keyboard navigation, viewport changes retain the view, small screens select phone mode, and explicit desktop mode is honored');
  clearTimeout(deadline);
})().catch(error=>{console.error(error);process.exit(1);});
````

## tests/test_foresight_airgapped_ui.py

SHA-256: `74f16fabf857731c11e1d1f3b93bb9144cf8019fa299f571a3e975ac54393dec`

````text
"""Exercise the REAL Counter menu/controller scripts without network navigation.

This is an environment-limited browser regression. Navigation to HTTP and file
URLs is prohibited by the runner; graphics is deliberately stubbed. It checks
real DOM menus, click handling, tray lifecycle and in-memory serialization,
NOT GPU quality, authenticated HTTP, embedded iframe execution, or persistence
across an actual browser restart. Those require separate target-device gates.
"""
from pathlib import Path
import os
import re
import shutil

import pytest

playwright = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
COUNTER_HTML = (STATIC / "foresight_counter.html").read_text(encoding="utf-8")
SCRIPTS = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", COUNTER_HTML, flags=re.S)
APP_SCRIPT = next(script for script in reversed(SCRIPTS) if "async function boot()" in script)
DOM = re.sub(r"<script(?:\s+[^>]*)?>.*?</script>", "", COUNTER_HTML, flags=re.S)


@pytest.fixture
def counter_page():
    with playwright.sync_playwright() as p:
        executable = (os.environ.get("FORESIGHT_TEST_CHROMIUM")
                      or shutil.which("chromium") or shutil.which("chromium-browser")
                      or shutil.which("google-chrome"))
        try:
            browser = p.chromium.launch(
                **({"executable_path": executable} if executable else {}),
                args=["--disable-dev-shm-usage", "--use-angle=swiftshader"],
            )
        except playwright.Error as error:
            pytest.skip(f"Optional development browser unavailable: {error}")
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(DOM)
        page.evaluate("""() => {
          const storage = new Map();
          Object.defineProperty(window, 'localStorage', {configurable:true, value: {
            getItem: k=>storage.has(k)?storage.get(k):null,
            setItem: (k,v)=>storage.set(k,String(v)),
            removeItem: k=>storage.delete(k), clear:()=>storage.clear()
          }});
          window.ReachAuth={requireSession:async()=>({role:'owner'})};
        }""")
        for name in ["foresight.config.js", "foresight_shapes.js", "foresight_gl.js", "foresight_chain.js"]:
            page.add_script_tag(path=str(STATIC / name))
        # Replace only the renderer; the real Counter, physics, menus and provider
        # remain unmodified and interact with actual browser DOM.
        page.evaluate("""() => {
          const mat=ForesightGL.MAT;
          window.ForesightGL=class {
            static MAT=mat;
            constructor(){this.gl={finish(){}};this.quality='full';}
            loadStone(){}setTheme(){}setLight2(){}draw(){}
          };
        }""")
        for name in ["foresight_counter.js", "foresight_files.js", "foresight_programs.js"]:
            page.add_script_tag(path=str(STATIC / name))
        page.add_script_tag(content=APP_SCRIPT)
        page.wait_for_function("window.__counter && window.__programs")
        yield page
        assert not errors, errors
        browser.close()


def open_menu(page, name):
    page.get_by_role("button", name=name, exact=True).click()


def test_default_counter_menu_can_open_lock_close_and_reopen(counter_page):
    page = counter_page
    assert page.evaluate("__counter.trays.length") == 0
    open_menu(page, "File")
    page.get_by_role("menuitem", name="New blank tray").click()
    page.wait_for_function("__counter.trays.length===1 && !__counter.trays[0].hidden")
    assert page.evaluate("__counter.trays[0].stack[0].type") == "blank"
    open_menu(page, "View")
    page.get_by_role("menuitem", name="Lock this tray").click()
    assert page.evaluate("__counter.trays[0].locked")
    open_menu(page, "View")
    page.get_by_role("menuitem", name="Unlock this tray").click()
    assert not page.evaluate("__counter.trays[0].locked")
    open_menu(page, "File")
    page.get_by_role("menuitem", name="Close this tray into the fan").click()
    page.wait_for_function("__counter.trays[0].closed", timeout=5000)
    assert page.evaluate("__counter.trays[0].stack[0].type") == "blank"
    open_menu(page, "Window")
    item = page.get_by_role("menuitem", name=re.compile("in the fan"))
    assert item.count() == 1
    item.click()
    page.wait_for_function("!__counter.trays[0].closed && !__counter.trays[0].hidden", timeout=5000)


def test_real_counter_integrates_2i_hosting_and_restorable_layout(counter_page):
    page = counter_page
    # The actual program provider creates the iframe and retains content identity.
    page.evaluate("__programs.open('twoi')")
    page.wait_for_function("__counter.trays.some(t=>t.stack[0].type==='twoi') && !__counter.trays[0].hidden", timeout=5000)
    assert page.locator('iframe[src="/writers-room"]').count() == 1
    page.evaluate("__counter.saveNow()")
    saved = page.evaluate("__counter.serialize()")
    assert len(saved["trays"]) == 1
    assert saved["trays"][0]["contents"][0]["type"] == "twoi"
    assert page.evaluate("localStorage.getItem('foresight.counter.v3')")
    # Reconstruct a fresh counter, not a merge into an already populated one.
    restored = page.evaluate("""snap => {
      __counter.destroy();
      const gl=new ForesightGL(document.getElementById('gl'));
      const fresh=ForesightCounter.create({canvas:document.getElementById('gl'),gl,
        provider:__programs.provider,storageKey:null,top:70});
      window.__restoredCounter=fresh;
      return fresh.restore(snap) && fresh.trays.length===1 &&
        fresh.trays[0].stack[0].type==='twoi';
    }""", saved)
    assert restored
    # We cannot navigate to /writers-room under this runner policy; iframe
    # creation and route correctness are verified separately by HTTP tests.


@pytest.fixture
def compatibility_page():
    """Actual application and its built-in Canvas 2D fallback, no GL test double."""
    with playwright.sync_playwright() as p:
        executable = (os.environ.get("FORESIGHT_TEST_CHROMIUM")
                      or shutil.which("chromium") or shutil.which("chromium-browser")
                      or shutil.which("google-chrome"))
        try:
            browser = p.chromium.launch(
                **({"executable_path": executable} if executable else {}),
                args=["--disable-dev-shm-usage", "--use-angle=swiftshader"],
            )
        except playwright.Error as error:
            pytest.skip(f"Optional development browser unavailable: {error}")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(DOM)
        page.evaluate("""() => {
          const storage=new Map();
          Object.defineProperty(window,'localStorage',{configurable:true,value:{
            getItem:k=>storage.has(k)?storage.get(k):null,
            setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)
          }});
          window.ReachAuth={requireSession:async()=>({role:'owner'})};
          // Force missing WebGL to test the product's real Canvas 2D failover,
          // not just whatever graphics drivers the CI machine happens to have.
          const real=HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext=function(mode,...args){
            if(mode==='webgl2'||mode==='webgl')return null;
            return real.call(this,mode,...args);
          };
        }""")
        for name in ["foresight.config.js", "foresight_shapes.js", "foresight_gl.js",
                     "foresight_canvas2d.js", "foresight_chain.js", "foresight_counter.js",
                     "foresight_files.js", "foresight_programs.js"]:
            page.add_script_tag(path=str(STATIC / name))
        page.add_script_tag(content=APP_SCRIPT)
        page.wait_for_function("window.__counter && !!window.ForesightCanvas2D")
        yield page
        assert not errors, errors
        browser.close()


def test_real_canvas2d_fallback_keeps_counter_usable(compatibility_page):
    page=compatibility_page
    assert page.get_by_role("status",name="Graphics compatibility mode").is_visible()
    open_menu(page,"File")
    page.get_by_role("menuitem",name="New blank tray").click()
    page.wait_for_function("__counter.trays.length===1 && !__counter.trays[0].hidden")
    assert page.evaluate("document.getElementById('gl').width > 0")
    assert page.evaluate("__counter.trays[0].stack[0].type") == "blank"
    # Changing lighting continues working under the alternate renderer.
    open_menu(page,"View")
    page.get_by_role("menuitem",name="Lantern light").click()
    assert page.evaluate("typeof __counter.debug.draw === 'function'")


def test_real_canvas2d_can_render_five_mixed_tray_shapes(compatibility_page):
    page=compatibility_page
    page.evaluate("""() => {
      for(const id of ['twoi','pubpartner_status','world_chat','recordings','doctor'])
        __programs.open(id);
    }""")
    # Crowded admission is a queued physics operation, not a synchronous call.
    # This is a generous CI bound; target-device animation performance is a
    # separate measured acceptance gate, never silently relaxed in physics tests.
    page.wait_for_function("__counter.trays.length===5",timeout=30000)
    page.evaluate("__counter.settle(120)")
    assert page.evaluate("__counter.trays.length") == 5
    assert page.evaluate("__counter.trays.every(t=>t.stack.length===1)")
    assert page.evaluate("document.querySelectorAll('.fc-plaque').length") == 5
````

## 2i/writers-room-v22.html

SHA-256: `68140d9958d1e803215ecc20f39b9011cc7b6637e920bbc20f020920c8ff3fcb`

````text
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pubcast 2i — Writer's Room</title>
<script src="/static/reach_auth.js"></script>
<link rel="stylesheet" href="/2i-assets/reach.css">
<style>

/* ═══════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════ */
:root {
  --ivory:#f9f4e6; --ivory-deep:#efe4cc; --ivory-glow:#fffbf0;
  --gold:#cda349; --gold-bright:#eecf83; --gold-deep:#93701f;
  --gold-glow:rgba(238,207,131,0.45); --gold-dim:rgba(205,163,73,0.18);
  --ink:#231f18; --pencil:#4a4032; --pencil-soft:#7c7160;
  --mahogany:#3a2013; --mahogany-deep:#1b0f09;
  --leather:#2c1608; --leather-seam:rgba(0,0,0,0.28);
  --velvet:#2e6b52; --velvet-glow:rgba(46,107,82,0.38);
  --parchment:#ecdfc3; --parchment-soft:#c3b391;
  --danger:#a24a3a; --danger-glow:rgba(162,74,58,0.3);
  --paper:#f6ecd5; --paper-aged:#f1e4c8; --paper-line:rgba(160,140,110,0.22);
  --margin-red:rgba(180,60,50,0.28);
  --glass-border:rgba(205,163,73,0.32);
  --frame-shadow:0 22px 46px -20px rgba(0,0,0,.85),
    inset 0 2px 0 rgba(255,225,150,.18),
    inset 0 -4px 8px rgba(0,0,0,.72);
  /* Per-pane text zoom. Set at runtime by loadZoom()/adjustZoom() in JS.
     Font-size only — nothing that reads these variables may also be a
     button, icon, or layout dimension. */
  --zoom-manuscript:1; --zoom-chat:1; --zoom-ref:1;
}
*, *::before, *::after { box-sizing:border-box; }
html, body {
  height:100%; margin:0; overflow:hidden;
  font-family:'Cormorant Garamond',serif;
  color:var(--parchment);
  background:
    radial-gradient(ellipse 55% 32% at 50% 0%, rgba(238,207,131,0.10), transparent 62%),
    radial-gradient(ellipse 45% 30% at 12% 105%, rgba(46,107,82,0.07), transparent 60%),
    linear-gradient(165deg, #2c190f 0%, #1d1009 55%, #130a05 100%);
}

/* ═══════════════════════════════════════════════════════════════
   LAYOUT SHELL
   ═══════════════════════════════════════════════════════════════ */
.app-shell {
  display:grid;
  grid-template-rows: 42px 1fr 32px;
  height:100vh;
}

/* --- TOP BAR --- */
.top-bar {
  display:flex; align-items:center; gap:12px;
  padding:0 16px;
  background:linear-gradient(180deg, rgba(44,22,8,0.95), rgba(27,15,9,0.98));
  border-bottom:1px solid rgba(205,163,73,0.25);
  box-shadow:0 2px 12px rgba(0,0,0,0.5);
  z-index:20;
}
.top-logo {
  font-family:'Cinzel Decorative',serif;
  font-size:14px; font-weight:700;
  color:var(--gold-bright);
  text-shadow:0 1px 3px rgba(0,0,0,0.6), 0 0 12px rgba(238,207,131,0.15);
  white-space:nowrap;
  letter-spacing:0.04em;
}
.top-logo small {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; font-weight:400;
  color:var(--parchment-soft);
  display:block; margin-top:-2px;
  letter-spacing:0.08em;
}
.top-tabs {
  display:flex; gap:2px;
  margin:0 auto;
  background:rgba(0,0,0,0.25);
  border-radius:6px; padding:3px;
}
.top-tab {
  font-family:'IBM Plex Mono',monospace;
  font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
  padding:5px 14px; border-radius:4px;
  border:none; cursor:pointer;
  color:var(--parchment-soft);
  background:transparent;
  transition:all 0.15s ease;
  box-shadow:none;
}
.top-tab:hover { color:var(--parchment); background:rgba(205,163,73,0.12); }
.top-tab.active {
  color:var(--gold-bright);
  background:rgba(205,163,73,0.22);
  box-shadow:inset 0 0 0 1px rgba(205,163,73,0.3);
}
.top-right {
  display:flex; align-items:center; gap:10px;
  margin-left:auto;
}
.mode-badge {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; letter-spacing:0.1em; text-transform:uppercase;
  padding:4px 10px; border-radius:4px;
  border:1px solid var(--glass-border);
  cursor:pointer;
  transition:all 0.15s ease;
}
.mode-badge.write {
  color:#bff2c8; border-color:rgba(46,107,82,0.5);
  background:rgba(46,107,82,0.15);
}
.mode-badge.collab {
  color:var(--gold-bright); border-color:var(--glass-border);
  background:rgba(205,163,73,0.12);
}
.top-icon-btn {
  width:28px; height:28px; border-radius:50%;
  border:1px solid rgba(205,163,73,0.25);
  background:rgba(0,0,0,0.2);
  color:var(--parchment-soft);
  font-size:13px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.15s ease;
  padding:0;
  box-shadow:none;
}
.top-icon-btn:hover { border-color:var(--gold); color:var(--gold-bright); background:rgba(205,163,73,0.12); }

/* --- MAIN AREA --- */
.main-area {
  display:grid;
  grid-template-columns: 280px 1fr;
  min-height:0; overflow:hidden;
  gap:0;
}
.main-area.sidebar-hidden { grid-template-columns: 0px 1fr; }
.main-area.sidebar-hidden .sidebar { display:none; }

/* --- LEFT SIDEBAR --- */
.sidebar {
  display:flex; flex-direction:column;
  background:linear-gradient(180deg, rgba(44,22,8,0.92), rgba(20,11,6,0.96));
  border-right:1px solid rgba(205,163,73,0.18);
  overflow:hidden; min-height:0;
}
.sidebar-section {
  display:flex; flex-direction:column;
  border-bottom:1px solid rgba(205,163,73,0.12);
  min-height:0;
}
.sidebar-section.collapsed > :not(.section-header) { display:none; }
.section-header {
  font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.1em; text-transform:uppercase;
  color:var(--gold);
  padding:10px 14px 8px;
  display:flex; align-items:center; gap:8px;
  cursor:pointer;
  user-select:none;
  border:none; background:none; width:100%; text-align:left;
  box-shadow:none;
}
.section-header::before {
  content:''; width:5px; height:5px; border-radius:50%;
  background:var(--gold);
  box-shadow:0 0 6px rgba(238,207,131,0.6);
  flex-shrink:0;
}
.section-header .collapse-arrow {
  margin-left:auto; font-size:8px; color:var(--parchment-soft);
  transition:transform 0.2s ease;
}
.sidebar-section.collapsed .collapse-arrow { transform:rotate(-90deg); }
.section-body { padding:0 14px 12px; display:flex; flex-direction:column; gap:8px; }

/* Manuscript control */
.mc-row {
  display:flex; justify-content:space-between; align-items:center;
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft);
}
.mc-progress {
  width:100%; height:6px; border-radius:3px;
  background:rgba(0,0,0,0.3);
  border:1px solid rgba(205,163,73,0.15);
  overflow:hidden;
}
.mc-progress-fill {
  height:100%; border-radius:2px;
  background:linear-gradient(90deg, var(--gold-deep), var(--gold-bright));
  transition:width 0.3s ease;
}
.mc-btn-row { display:flex; gap:6px; }
.mc-btn {
  flex:1; font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.04em;
  padding:7px 8px; border-radius:5px;
  cursor:pointer;
  border:1px solid rgba(205,163,73,0.25);
  background:linear-gradient(160deg, rgba(255,255,255,0.04), rgba(0,0,0,0.15));
  color:var(--parchment);
  box-shadow:0 2px 4px rgba(0,0,0,0.3);
  transition:all 0.12s ease;
  text-transform:uppercase;
}
.mc-btn:hover:not(:disabled) {
  border-color:var(--gold);
  background:rgba(205,163,73,0.12);
  box-shadow:0 2px 8px rgba(0,0,0,0.4), 0 0 8px rgba(238,207,131,0.12);
}
.mc-btn:disabled { opacity:0.35; cursor:default; }
.mc-btn.primary {
  background:linear-gradient(155deg, rgba(255,255,255,0.5), transparent 28%),
    linear-gradient(160deg, #fffdf3, #eee1c8 48%, #cdbb98);
  color:#684b18;
  border-color:rgba(100,70,35,0.7);
  box-shadow:0 3px 6px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.9);
}
.mc-btn.primary:hover:not(:disabled) {
  filter:brightness(1.08);
  box-shadow:0 4px 10px rgba(0,0,0,0.5), 0 0 12px rgba(238,207,131,0.2);
}
.mc-btn.danger { border-color:var(--danger); color:#f2c0bf; }

/* Reference archive */
.ref-search {
  display:flex; gap:4px;
}
.ref-search input {
  flex:1; padding:6px 8px; border-radius:5px;
  border:1px solid rgba(205,163,73,0.18);
  background:rgba(0,0,0,0.2);
  color:var(--parchment);
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  outline:none;
}
.ref-search input:focus { border-color:var(--gold); }
.ref-search button {
  width:30px; flex:0 0 30px; padding:0; font-size:12px;
  border-radius:5px;
}
.ref-tabs {
  display:flex; gap:2px;
}
.ref-tab {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; letter-spacing:0.06em; text-transform:uppercase;
  padding:4px 8px; border-radius:3px;
  border:none; cursor:pointer;
  color:var(--parchment-soft); background:transparent;
  box-shadow:none;
}
.ref-tab:hover { color:var(--parchment); }
.ref-tab.active { color:var(--gold-bright); background:rgba(205,163,73,0.18); }
.ref-list-container {
  flex:1; overflow-y:auto; min-height:0;
  display:flex; flex-direction:column; gap:4px;
}
.ref-item {
  display:flex; align-items:flex-start; gap:8px;
  padding:8px; border-radius:5px;
  background:rgba(0,0,0,0.12);
  border:1px solid transparent;
  cursor:pointer;
  transition:all 0.12s ease;
}
.ref-item:hover {
  border-color:rgba(205,163,73,0.3);
  background:rgba(205,163,73,0.06);
}
.ref-icon {
  width:24px; height:24px; border-radius:4px;
  background:rgba(205,163,73,0.12);
  display:flex; align-items:center; justify-content:center;
  font-size:11px; flex-shrink:0;
  color:var(--gold);
  margin-top:2px;
}
.ref-meta {
  flex:1; min-width:0;
}
.ref-meta .ref-name {
  font-family:'Cormorant Garamond',serif;
  font-size:13px; color:var(--parchment);
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.ref-meta .ref-type {
  font-family:'IBM Plex Mono',monospace;
  font-size:9px; color:var(--parchment-soft);
}
.ref-meta .ref-date {
  font-family:'IBM Plex Mono',monospace;
  font-size:8.5px; color:var(--parchment-soft);
  opacity:0.7;
}
.ref-actions { display:flex; gap:4px; flex-shrink:0; margin-top:2px; }
.ref-action-btn {
  width:22px; height:22px; border-radius:3px;
  border:1px solid rgba(205,163,73,0.15);
  background:transparent; color:var(--parchment-soft);
  font-size:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  padding:0; box-shadow:none;
}
.ref-action-btn:hover { border-color:var(--gold); color:var(--gold-bright); }

/* Chat pane */
.chat-section { flex:1; min-height:0; }
.chat-section .section-body { flex:1; min-height:0; display:flex; flex-direction:column; }
.chat-log {
  flex:1; overflow-y:auto; min-height:0;
  display:flex; flex-direction:column; gap:6px;
  padding-right:4px;
}
.chat-msg {
  font-size:calc(13px * var(--zoom-chat, 1)); line-height:1.45;
  padding:7px 10px; border-radius:8px;
  max-width:92%;
}
.chat-msg.pp {
  background:rgba(0,0,0,0.22); border:1px solid rgba(0,0,0,0.15);
  align-self:flex-start; color:var(--parchment);
}
.chat-msg.you {
  background:rgba(46,107,82,0.2); border:1px solid var(--velvet-glow);
  align-self:flex-end; color:var(--parchment);
}
.chat-msg .who {
  font-family:'IBM Plex Mono',monospace;
  font-size:0.65em; text-transform:uppercase; letter-spacing:0.06em;
  color:var(--parchment-soft); display:block; margin-bottom:2px;
}
.chat-msg.thinking { opacity:0.5; font-style:italic; }
.chat-input-row {
  display:flex; gap:4px; margin-top:6px; flex-shrink:0;
}
.chat-input-row input {
  flex:1; font-family:'Cormorant Garamond',serif;
  font-size:calc(13px * var(--zoom-chat, 1)); padding:7px 9px;
  color:var(--parchment);
  border:1px solid rgba(205,163,73,0.18);
  border-radius:6px; background:rgba(0,0,0,0.2);
  outline:none;
}
.chat-input-row input:focus { border-color:var(--gold); }
.chat-mic-btn {
  width:28px; flex:0 0 28px; padding:0; font-size:12px;
  border-radius:6px;
}
.chat-mic-btn.listening {
  background:linear-gradient(160deg,#c94747,#8a2c2c) !important;
  color:#fff !important;
  animation:micPulse 1s ease-in-out infinite;
}
@keyframes micPulse { 0%,100%{box-shadow:0 0 0 0 rgba(201,71,71,.5)} 50%{box-shadow:0 0 0 5px rgba(201,71,71,0)} }

/* ═══════════════════════════════════════════════════════════════
   NOTEBOOK
   ═══════════════════════════════════════════════════════════════ */
.notebook-frame {
  position:relative;
  display:flex;
  min-height:0; overflow:hidden;
  background:
    radial-gradient(ellipse at 50% 4%, rgba(255,220,145,0.10), transparent 34%),
    radial-gradient(ellipse at 50% 100%, rgba(0,0,0,0.3), transparent 48%),
    linear-gradient(180deg, #2a160d, #160b06 82%);
  border-left:3px solid transparent;
  border-image:linear-gradient(180deg, #e4bd68, #6d4a16 18%, #261609 52%, #c49a48 82%, #5b3d12) 1;
  box-shadow:inset 0 18px 35px rgba(255,215,135,.03), inset 0 -30px 45px rgba(0,0,0,.4);
}
#lanternCanvas {
  position:absolute; inset:0; width:100%; height:100%;
  pointer-events:none; z-index:0;
}

.notebook-inner {
  position:relative; z-index:1;
  display:flex; flex:1; min-height:0; min-width:0;
  margin:8px 8px 8px 0;
}

/* Spiral spine */
.spiral-spine {
  flex:0 0 52px;
  position:relative;
  background:linear-gradient(90deg, #090604, #21150d 12%, #0d0805 27%, #24170e 52%, #090604 76%, #1b1009);
  box-shadow:inset -8px 0 10px -8px rgba(0,0,0,.9), inset 6px 0 8px -8px rgba(238,207,131,.15);
  overflow:hidden;
}
.spiral-spine canvas { width:100%; height:100%; display:block; }

/* Page sheets */
.page-sheets {
  flex:1; min-width:0; min-height:0;
  display:flex; flex-direction:column;
  overflow:hidden;
  border-radius:0 6px 6px 0;
  box-shadow:inset -10px 0 16px -14px rgba(0,0,0,.6), inset 0 2px 0 rgba(255,255,255,.6);
  position:relative;
}

/* Manuscript zone (locked/committed text) */
.manuscript-zone {
  background:var(--paper);
  flex:0 0 auto; max-height:45vh;
  overflow-y:auto;
  position:relative;
  padding:0;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9),
    inset -6px 0 12px rgba(120,84,30,.10),
    inset 0 -6px 12px rgba(90,60,20,.07);
}
.manuscript-zone .zone-label-row {
  position:sticky; top:0; z-index:5;
  display:flex; align-items:center; justify-content:flex-end; gap:10px;
  padding:4px 14px;
  background:linear-gradient(180deg, var(--paper), rgba(246,236,213,0.9));
}
.manuscript-zone .zone-label {
  font-family:'IBM Plex Mono',monospace; font-size:8px;
  letter-spacing:0.12em; color:var(--gold-deep); text-transform:uppercase;
}

/* Solo mode */
.page-sheets.solo-mode .manuscript-zone { flex:1; max-height:none; }
.page-sheets.solo-mode .tortoise-seam { display:none; }
.page-sheets.solo-mode .draft-zone { display:none; }
.page-sheets.solo-mode .solo-editor { display:flex; }
.page-sheets.solo-mode .manuscript-lines { display:none; }

.solo-editor {
  display:none; flex:1; flex-direction:row;
  min-height:0;
}
.line-numbers {
  flex:0 0 44px;
  padding:6px 0;
  text-align:right;
  font-family:'IBM Plex Mono',monospace;
  font-size:12px;
  /* Line pitch must match .solo-textarea's actual line-box height
     (font-size × line-height), not this gutter's own smaller glyph
     size, or the numbers drift off their lines — worse at every zoom
     step away from 100%. Pre-existing at 1x (18.6px vs 24px); fixed
     here rather than carried forward. 2.00208 = (15.5 * 1.55) / 12 —
     precomputed because calc() division must be by a plain <number>,
     never by another length (verified: dividing by 12px directly
     left the expression unresolved and the declaration invalid). */
  line-height:calc(2.00208 * var(--zoom-manuscript, 1));
  color:rgba(147,112,31,0.4);
  user-select:none;
  overflow-y:auto; overflow-x:hidden;
  scrollbar-width:none;
  border-right:1px solid var(--margin-red);
  padding-right:8px;
}
.line-numbers::-webkit-scrollbar { display:none; }
.solo-textarea {
  flex:1; resize:none; border:none; outline:none;
  font-family:'Cormorant Garamond',serif;
  font-size:calc(15.5px * var(--zoom-manuscript, 1)); line-height:1.55;
  color:var(--ink);
  background:transparent;
  padding:6px 24px 40px 14px;
  overflow-y:auto;
}

/* Manuscript lines (co-writing committed) */
.manuscript-lines {
  padding:4px 0;
}
.m-line {
  font-family:'Cormorant Garamond',serif;
  font-size:calc(15px * var(--zoom-manuscript, 1)); line-height:1.5;
  color:var(--ink);
  padding:1px 24px 1px 58px;
  cursor:pointer;
  position:relative;
  transition:background 0.1s ease;
  display:flex; align-items:baseline;
}
.m-line:hover { background:rgba(147,112,31,0.06); }
.m-line.selected { background:rgba(205,163,73,0.18); box-shadow:inset 3px 0 0 var(--gold); }
.m-line.locked::after {
  content:'🔒'; position:absolute; right:8px; top:50%; transform:translateY(-50%);
  font-size:10px; opacity:0.4;
}
.m-line .line-num {
  position:absolute; left:8px;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  color:rgba(147,112,31,0.35);
  width:36px; text-align:right;
  user-select:none;
}
.m-line-edit textarea {
  width:100%; font-family:'Cormorant Garamond',serif;
  font-size:calc(15px * var(--zoom-manuscript, 1)); line-height:1.5; color:var(--ink);
  background:rgba(255,255,255,0.5);
  border:1px solid var(--gold-deep); border-radius:4px;
  padding:3px 6px; resize:vertical; outline:none;
}
.chapter-heading {
  font-family:'Cinzel Decorative',serif;
  font-size:20px; text-align:center;
  color:var(--ink); padding:18px 24px 6px;
  letter-spacing:0.04em;
}
.chapter-subtitle {
  font-family:'Cormorant Garamond',serif;
  font-style:italic; font-size:16px;
  text-align:center; color:var(--pencil);
  padding:0 24px 12px;
}
.chapter-divider {
  text-align:center; padding:2px 0 10px;
  color:var(--gold-deep); font-size:14px;
  letter-spacing:0.3em;
  opacity:0.5;
}

/* Tortoise seam divider */
.tortoise-seam {
  height:8px; flex-shrink:0;
  background:linear-gradient(90deg, #8a5a22, #c49a48, #8a5a22);
  box-shadow:
    inset 0 2px 2px rgba(255,255,255,0.4),
    inset 0 -2px 3px rgba(0,0,0,0.5),
    0 1px 2px rgba(0,0,0,0.5);
}

/* Draft zone (co-writing buffer) */
.draft-zone {
  background:var(--paper-aged);
  flex:1; min-height:0; overflow-y:auto;
  position:relative;
  padding:0;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.8),
    inset -6px 0 12px rgba(120,84,30,.10);
  scroll-behavior:smooth;
}
.reading-line {
  font-family:'Kalam',cursive;
  font-size:16px; line-height:1.45;
  color:var(--pencil);
  padding:6px 24px 6px 58px;
  background:rgba(205,163,73,0.12);
  border-left:3px solid var(--gold);
  margin:0 0 4px;
  position:relative;
}
.reading-line.reaction { border-left-color:var(--velvet); background:rgba(46,107,82,0.08); }
.draft-area {
  display:block; width:100%; min-height:100px;
  resize:none; border:none; outline:none; overflow-y:auto;
  font-family:'Kalam',cursive;
  font-size:calc(16px * var(--zoom-manuscript, 1)); line-height:1.5;
  color:var(--pencil);
  background:transparent;
  padding:4px 24px 30px 58px;
  text-shadow:0 .25px 0 rgba(0,0,0,.18);
}

/* ═══════════════════════════════════════════════════════════════
   BOTTOM STATUS BAR
   ═══════════════════════════════════════════════════════════════ */
.status-bar {
  display:flex; align-items:center; gap:12px;
  padding:0 16px;
  background:linear-gradient(180deg, rgba(27,15,9,0.96), rgba(20,11,6,0.98));
  border-top:1px solid rgba(205,163,73,0.18);
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft);
  z-index:20;
}
.status-dot {
  width:6px; height:6px; border-radius:50%;
  background:var(--parchment-soft);
}
.status-dot.playing { background:var(--velvet); box-shadow:0 0 6px rgba(46,107,82,0.8); }
.status-dot.paused { background:var(--gold); box-shadow:0 0 6px rgba(238,207,131,0.6); }
.status-sep { color:rgba(205,163,73,0.25); }
.llm-pill {
  padding:2px 8px; border-radius:999px;
  border:1px solid var(--glass-border);
  cursor:pointer; font-size:9px;
  transition:all 0.12s ease;
}
.llm-pill.ok { color:#bff2c8; border-color:#4c9a63; }
.llm-pill.err { color:#f2c0bf; border-color:#9a4c4c; }
.status-right {
  margin-left:auto;
  display:flex; align-items:center; gap:10px;
}
.playback-controls {
  display:flex; align-items:center; gap:4px;
}
.pb-btn {
  width:24px; height:24px; border-radius:4px;
  border:1px solid rgba(205,163,73,0.2);
  background:transparent; color:var(--parchment-soft);
  font-size:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  padding:0; box-shadow:none;
  transition:all 0.12s ease;
}
.pb-btn:hover { border-color:var(--gold); color:var(--gold-bright); }
.pb-btn.active { background:rgba(46,107,82,0.2); border-color:var(--velvet); color:#bff2c8; }
.speed-slider {
  width:50px; height:3px;
  accent-color:var(--gold);
}
.save-btn {
  font-family:'IBM Plex Mono',monospace;
  font-size:9.5px; letter-spacing:0.06em; text-transform:uppercase;
  padding:4px 12px; border-radius:4px;
  border:1px solid rgba(205,163,73,0.3);
  background:rgba(205,163,73,0.1);
  color:var(--gold-bright);
  cursor:pointer;
  box-shadow:none;
  transition:all 0.12s ease;
}
.save-btn:hover { background:rgba(205,163,73,0.2); border-color:var(--gold); }

/* ═══════════════════════════════════════════════════════════════
   MODALS
   ═══════════════════════════════════════════════════════════════ */
.modal-backdrop {
  position:fixed; inset:0;
  background:rgba(10,6,3,0.65);
  z-index:100;
  display:none; align-items:center; justify-content:center;
}
.modal-backdrop.open { display:flex; }
.modal {
  width:min(460px, 92vw); max-height:86vh; overflow:auto;
  padding:18px; border-radius:10px;
  background:linear-gradient(160deg, #432516, #1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  box-shadow:0 24px 48px -18px rgba(0,0,0,.9);
  color:var(--parchment);
}
.modal-title {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  letter-spacing:0.1em; text-transform:uppercase;
  color:var(--gold); margin-bottom:12px;
  display:flex; align-items:center; gap:6px;
}
.modal-title::before {
  content:''; width:5px; height:5px; border-radius:50%;
  background:var(--gold); box-shadow:0 0 6px rgba(238,207,131,0.6);
}
.modal-body { display:flex; flex-direction:column; gap:6px; }
.modal-body label {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--parchment-soft); margin-top:6px;
}
.modal-body select, .modal-body input[type=text], .modal-body input[type=password], .modal-body input[type=number] {
  width:100%; padding:7px 9px; border-radius:5px;
  border:1px solid var(--glass-border);
  background:rgba(0,0,0,0.25); color:var(--parchment);
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  outline:none;
}
.modal-body select:focus, .modal-body input:focus { border-color:var(--gold); }
.modal-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:14px; }
.modal-actions button { font-size:11px; padding:6px 14px; }
.test-result {
  margin-top:8px; font-family:'IBM Plex Mono',monospace;
  font-size:11px; min-height:14px;
}
.test-result.ok { color:#bff2c8; }
.test-result.err { color:#f2c0bf; }
.llm-fields { display:none; flex-direction:column; gap:4px; }
.llm-fields.active { display:flex; }

/* Context menu */
.context-menu {
  position:fixed; z-index:200;
  padding:5px; border-radius:8px;
  background:linear-gradient(160deg,#432516,#1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  box-shadow:0 10px 24px -6px rgba(0,0,0,0.7);
  display:none;
  min-width:160px;
}
.context-menu.open { display:block; }
.ctx-btn {
  display:block; width:100%; text-align:left;
  font-family:'IBM Plex Mono',monospace;
  font-size:11px; padding:7px 12px;
  background:transparent; border:none; color:var(--parchment);
  cursor:pointer; border-radius:4px;
  box-shadow:none;
}
.ctx-btn:hover { background:rgba(205,163,73,0.15); }
.ctx-sep { height:1px; background:rgba(205,163,73,0.12); margin:3px 8px; }

/* Ref viewer overlay */
.ref-viewer {
  position:absolute; inset:0; z-index:10;
  background:var(--paper);
  display:none; flex-direction:column;
}
.ref-viewer.open { display:flex; }
.ref-viewer-header {
  display:flex; align-items:center; gap:8px;
  padding:8px 14px;
  border-bottom:1px solid rgba(147,112,31,0.15);
  background:linear-gradient(180deg, var(--paper), var(--paper-aged));
}
.ref-viewer-header .ref-back-btn {
  font-size:11px; padding:4px 10px; border-radius:4px;
  border:1px solid rgba(147,112,31,0.3);
  background:transparent; color:var(--pencil);
  cursor:pointer; box-shadow:none;
}
.ref-viewer-header .ref-title {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--pencil-soft);
}
.ref-viewer-body {
  flex:1; overflow-y:auto; padding:12px 24px;
  font-family:'Cormorant Garamond',serif;
  font-size:calc(15px * var(--zoom-ref, 1)); line-height:1.6;
  color:var(--ink);
  white-space:pre-wrap;
}

/* Hamburger menu */
.hamburger-menu {
  position:fixed; top:46px; right:12px; z-index:90;
  min-width:220px; padding:6px;
  background:linear-gradient(160deg,#432516,#1c0e08 88%);
  border:1px solid rgba(205,163,73,0.35);
  border-radius:8px;
  box-shadow:0 16px 32px -12px rgba(0,0,0,.9);
  display:none;
}
.hamburger-menu.open { display:block; }
.hm-btn {
  display:flex; align-items:center; gap:8px; width:100%;
  text-align:left; padding:7px 12px; border-radius:5px;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  background:transparent; border:none; color:var(--parchment);
  cursor:pointer; box-shadow:none;
}
.hm-btn:hover { background:rgba(205,163,73,0.12); }
.hm-btn .hm-icon { width:18px; text-align:center; font-size:12px; }
.hm-sep { height:1px; background:rgba(205,163,73,0.12); margin:4px 12px; }
.hm-toggle::after {
  content:'Off'; margin-left:auto;
  font-size:8.5px; padding:2px 6px; border-radius:999px;
  background:rgba(255,255,255,0.06); color:var(--parchment-soft);
}
.hm-toggle.on::after {
  content:'On'; background:rgba(205,163,73,0.25); color:var(--gold-bright);
}

/* Scrollbar */
::-webkit-scrollbar { width:7px; height:7px; }
::-webkit-scrollbar-track { background:rgba(0,0,0,.12); }
::-webkit-scrollbar-thumb {
  background:linear-gradient(180deg,#5a3d15,#cda349,#6b4a18);
  border-radius:8px; border:1.5px solid transparent; background-clip:padding-box;
}

/* Utilities */
.hidden { display:none !important; }

/* ── PUBPARTNER INTELLIGENCE ─────────────────────────────────────── */
.pp-status { font-size:10px; letter-spacing:.04em; padding:3px 6px;
             border-radius:3px; margin-bottom:6px; }
.pp-status.ok  { color:var(--gold); background:rgba(205,163,73,.10); }
.pp-status.off { color:var(--parchment-soft); background:rgba(0,0,0,.18); }
.pp-flag { display:flex; align-items:flex-start; gap:6px; font-size:11px;
           line-height:1.35; padding:5px 6px; margin-bottom:4px;
           border-left:2px solid var(--parchment-soft);
           background:rgba(0,0,0,.16); border-radius:0 3px 3px 0; }
.pp-flag.pp-attention { border-left-color:var(--gold); }
.pp-flag.pp-concern   { border-left-color:var(--danger); }
.pp-flag-msg { flex:1; }
.pp-flag-x { background:none; border:none; color:var(--parchment-soft);
             cursor:pointer; font-size:10px; padding:0 2px; line-height:1; }
.pp-flag-x:hover { color:var(--parchment); }
.pp-cast-head { font-size:9px; letter-spacing:.12em; text-transform:uppercase;
                color:var(--parchment-soft); margin:8px 0 3px; }
.pp-cast-row { font-size:11px; padding:2px 0; display:flex;
               align-items:center; gap:5px; }
.pp-dot { width:4px; height:4px; border-radius:50%;
          background:var(--parchment-soft); flex:0 0 auto; }
.pp-dot.pp-user { background:var(--gold); }
.pp-aka { color:var(--parchment-soft); font-size:10px; }

/* ── per-pane text zoom control ───────────────────────────────────────
   Fixed dimensions always — these buttons never grow. They change one
   of --zoom-manuscript / --zoom-chat / --zoom-ref, nothing else. */
.zoom-ctrl { display:flex; align-items:center; gap:3px; flex-shrink:0; }
.zoom-btn {
  width:19px; height:19px; flex:0 0 19px; padding:0;
  font-family:'IBM Plex Mono',monospace; font-size:11px; line-height:1;
  display:flex; align-items:center; justify-content:center;
  border-radius:4px; cursor:pointer; user-select:none;
  border:1px solid rgba(205,163,73,0.25);
  background:linear-gradient(160deg, rgba(255,255,255,0.04), rgba(0,0,0,0.15));
  color:var(--parchment-soft);
  transition:border-color 0.12s ease, color 0.12s ease;
}
.zoom-btn:hover { border-color:var(--gold); color:var(--gold-bright); }
.zoom-btn:active { transform:translateY(1px); }
.zoom-pct {
  font-family:'IBM Plex Mono',monospace; font-size:9px; letter-spacing:.02em;
  color:var(--parchment-soft); min-width:29px; text-align:center; user-select:none;
}
/* On the paper-colored notebook surfaces (zone label, reference viewer)
   the dark-glass palette above reads muddy — swap to ink/pencil tones. */
.zoom-ctrl.on-paper .zoom-btn {
  border-color:rgba(147,112,31,0.3);
  background:rgba(255,255,255,0.35);
  color:var(--pencil);
}
.zoom-ctrl.on-paper .zoom-btn:hover { border-color:var(--gold-deep); color:var(--ink); }
.zoom-ctrl.on-paper .zoom-pct { color:var(--pencil-soft); }
</style>
<script src="/static/program_audio_runtime.js"></script>
</head>
<body>
<!-- ═══════════════════════════════════════════════════════════════
     APP SHELL
     ═══════════════════════════════════════════════════════════════ -->
<div class="app-shell">
  <!-- TOP BAR -->
  <div class="top-bar">
    <div class="top-logo">Writer's Room<small>Pubcast 2i</small></div>
    <div class="top-tabs">
      <span class="top-tab active" data-tab="manuscript" aria-current="page">Manuscript</span>
    </div>
    <div class="top-right">
      <button class="mode-badge write" id="modeBadge" title="Toggle between Write (solo) and Collab (co-writing) mode">Write</button>
      <button class="top-icon-btn" id="shelfBtn" title="My manuscripts">My manuscripts</button>
      <button class="top-icon-btn" id="sidebarToggle" title="Toggle sidebar">☰</button>
      <button class="top-icon-btn" id="menuToggle" title="Menu">⚙</button>
    </div>
  </div>

  <!-- MAIN AREA -->
  <div class="main-area" id="mainArea">
    <!-- SIDEBAR -->
    <div class="sidebar" id="sidebar">
      <!-- Manuscript Control -->
      <div class="sidebar-section" id="mcSection">
        <button class="section-header" onclick="toggleSection('mcSection')">
          Manuscript Control <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body">
          <div class="mc-row"><span>Draft Status</span><span id="mcDraftStatus">Active</span></div>
          <div class="mc-row"><span id="mcWordProgress">0 / — words</span><span id="mcPercent"></span></div>
          <div class="mc-progress"><div class="mc-progress-fill" id="mcProgressFill" style="width:0"></div></div>
          <div class="mc-btn-row">
            <button class="mc-btn primary" id="lockSceneBtn">🔒 Lock scene</button>
          </div>
          <div class="mc-btn-row">
            <button class="mc-btn" id="unlockBtn">🔓 Unlock</button>
            <button class="mc-btn" id="lockAllBtn">Lock all</button>
          </div>
          <div class="mc-btn-row">
            <button class="mc-btn" id="newChapterBtn">New chapter</button>
            <button class="mc-btn" id="exportBtn">Export</button>
          </div>
          <div class="mc-btn-row" id="collabOnlyControls">
            <button class="mc-btn primary" id="approveBtn">✓ Commit draft</button>
            <button class="mc-btn" id="genBtn">⚡ Generate</button>
          </div>
        </div>
      </div>

      <!-- Reference Archive -->
      <div class="sidebar-section" id="refSection">
        <button class="section-header" onclick="toggleSection('refSection')">
          Reference Archive <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body" style="flex:1; min-height:0;">
          <div class="ref-search">
            <input type="text" id="refSearchInput" placeholder="Search documents…" />
            <button class="mc-btn" style="flex:0 0 28px; padding:0; font-size:11px;" onclick="filterRefs()">🔍</button>
          </div>
          <div class="ref-tabs">
            <button class="ref-tab active" data-filter="all" onclick="setRefFilter(this,'all')">All</button>
            <button class="ref-tab" data-filter="chapter" onclick="setRefFilter(this,'chapter')">Chapters</button>
            <button class="ref-tab" data-filter="research" onclick="setRefFilter(this,'research')">Research</button>
            <button class="ref-tab" data-filter="notes" onclick="setRefFilter(this,'notes')">Notes</button>
          </div>
          <div class="ref-list-container" id="refListContainer"></div>
          <button class="mc-btn" id="addRefBtn" style="flex-shrink:0;">+ Add reference</button>
        </div>
      </div>

      <!-- Chat -->
      <div class="sidebar-section chat-section" id="chatSection">
        <button class="section-header" onclick="toggleSection('chatSection')">
          PubPartner — Chat <span class="collapse-arrow">▼</span>
        </button>
        <div class="section-body">
          <label class="partner-label" for="partnerSelect">Conversation partner</label>
          <select id="partnerSelect" aria-label="Conversation partner"><option value="alex">Alex</option></select>
          <p id="partnerNote" class="partner-note">Your manuscript and conversation stay together.</p>
          <div id="ppStatus" class="pp-status off">PubPartner: offline</div>
          <div id="ppFlags"></div>
          <div id="ppCast"></div>
          <div class="zoom-ctrl" style="justify-content:flex-end; margin-bottom:4px;" title="Chat text size">
            <button class="zoom-btn" onclick="adjustZoom('chat',-1)" title="Smaller text">A−</button>
            <span class="zoom-pct" id="zoomPctChat">100%</span>
            <button class="zoom-btn" onclick="adjustZoom('chat',1)" title="Larger text">A+</button>
          </div>
          <div class="chat-log" id="chatLog"></div>
          <div class="chat-input-row">
            <input id="chatInput" type="text" placeholder="Talk with PubPartner…" />
            <button class="mc-btn chat-mic-btn" id="chatMicBtn" title="Dictate">🎤</button>
            <button class="mc-btn primary" id="chatSendBtn" style="flex:0 0 auto; padding:5px 10px;">Send</button>
          </div>
        </div>
      </div>
    </div>

    <!-- NOTEBOOK -->
    <div class="notebook-frame" id="notebookFrame">
      <canvas id="lanternCanvas"></canvas>
      <div class="notebook-inner">
        <div class="spiral-spine"><canvas id="spineCanvas"></canvas></div>
        <div class="page-sheets" id="pageSheets">
          <!-- Reference viewer overlay -->
          <div class="ref-viewer" id="refViewer">
            <div class="ref-viewer-header">
              <button class="ref-back-btn" onclick="closeRefViewer()">← Back</button>
              <span class="ref-title" id="refViewerTitle"></span>
              <div class="zoom-ctrl on-paper" style="margin-left:auto;" title="Reference text size">
                <button class="zoom-btn" onclick="adjustZoom('ref',-1)" title="Smaller text">A−</button>
                <span class="zoom-pct" id="zoomPctRef">100%</span>
                <button class="zoom-btn" onclick="adjustZoom('ref',1)" title="Larger text">A+</button>
              </div>
            </div>
            <div class="ref-viewer-body" id="refViewerBody"></div>
          </div>

          <!-- Manuscript zone (committed text / solo editor) -->
          <div class="manuscript-zone" id="manuscriptZone">
            <div class="zone-label-row">
              <div class="zoom-ctrl on-paper" title="Manuscript text size">
                <button class="zoom-btn" onclick="adjustZoom('manuscript',-1)" title="Smaller text">A−</button>
                <span class="zoom-pct" id="zoomPctManuscript">100%</span>
                <button class="zoom-btn" onclick="adjustZoom('manuscript',1)" title="Larger text">A+</button>
              </div>
              <div class="zone-label" id="zoneLabel">Manuscript</div>
            </div>
            <div class="manuscript-lines" id="manuscriptLines"></div>
            <div class="solo-editor" id="soloEditor">
              <div class="line-numbers" id="lineNumbers"></div>
              <textarea class="solo-textarea" id="soloTextarea" placeholder="Begin writing your manuscript…" spellcheck="true"></textarea>
            </div>
          </div>

          <!-- Seam -->
          <div class="tortoise-seam" id="tortoiseSeam"></div>

          <!-- Draft zone (buffer in co-writing) -->
          <div class="draft-zone" id="draftZone">
            <div id="readingIndicator"></div>
            <textarea class="draft-area" id="draftArea" placeholder="Keep writing…" spellcheck="true"></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- STATUS BAR -->
  <div class="status-bar">
    <span class="status-dot" id="statusDot"></span>
    <span id="statusText">idle</span>
    <span class="status-sep">|</span>
    <span id="docTitleDisplay" style="cursor:pointer;" title="Click to rename"></span>
    <span class="status-sep">|</span>
    <span id="wordCount">0 words</span>
    <span class="status-sep">|</span>
    <span id="llmPill" class="llm-pill" title="Click to configure LLM">no LLM</span>
    <div class="status-right">
      <div class="playback-controls" id="playbackControls">
        <button class="pb-btn" id="stopBtn" title="Stop">■</button>
        <button class="pb-btn" id="playBtn" title="Play/Pause">▶</button>
        <button class="pb-btn" id="skipBtn" title="Skip">⏭</button>
        <input type="range" class="speed-slider" id="speedSlider" min="0.5" max="2.5" step="0.25" value="1" title="Read speed" />
      </div>
      <span id="saveIndicator" style="font-size:9px; opacity:0.6;">unsaved</span>
      <button class="save-btn" id="saveBtn">Save</button>
    </div>
  </div>
</div>

<!-- HAMBURGER MENU -->
<div class="hamburger-menu" id="hamburgerMenu">
  <button class="hm-btn" id="hmNewDoc"><span class="hm-icon">📄</span>New document</button>
  <button class="hm-btn" id="hmOpenDoc"><span class="hm-icon">📂</span>Open document…</button>
  <button class="hm-btn" id="hmSaveAs"><span class="hm-icon">💾</span>Save as…</button>
  <button class="hm-btn" id="hmRestoreAutosave"><span class="hm-icon">🔄</span>Restore autosave…</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmFindReplace"><span class="hm-icon">🔍</span>Find &amp; replace</button>
  <button class="hm-btn" id="hmRenameDoc"><span class="hm-icon">✏️</span>Rename document</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmLLMSettings"><span class="hm-icon">⚙</span>LLM provider…</button>
  <div class="hm-sep"></div>
  <button class="hm-btn" id="hmKeyboardHelp"><span class="hm-icon">⌨</span>Keyboard shortcuts</button>
</div>

<!-- CONTEXT MENU -->
<div class="context-menu" id="contextMenu">
  <button class="ctx-btn" id="ctxEdit">Edit line</button>
  <button class="ctx-btn" id="ctxInsertAbove">Insert line above</button>
  <button class="ctx-btn" id="ctxInsertBelow">Insert line below</button>
  <div class="ctx-sep"></div>
  <button class="ctx-btn" id="ctxLock">Lock line</button>
  <button class="ctx-btn" id="ctxUnlock">Unlock line</button>
  <button class="ctx-btn" id="ctxDelete">Delete line</button>
</div>

<!-- LLM MODAL -->
<div class="modal-backdrop" id="llmModalBackdrop">
  <div class="modal">
    <div class="modal-title">LLM Provider</div>
    <div class="modal-body">
      <label>Provider</label>
      <select id="llmProvider">
        <option value="claude">Claude (Anthropic API)</option>
        <option value="openai">OpenAI / OpenAI-compatible</option>
        <option value="local">Local (Ollama, LM Studio)</option>
        <option value="pubpartner">PubPartner (local server)</option>
      </select>
      <div id="llmFieldsClaude" class="llm-fields">
        <label>API key</label><input id="llmClaudeKey" type="password" placeholder="sk-ant-…" autocomplete="off" />
        <label>Model</label><input id="llmClaudeModel" type="text" value="claude-sonnet-4-6" />
      </div>
      <div id="llmFieldsOpenai" class="llm-fields">
        <label>API key</label><input id="llmOpenaiKey" type="password" placeholder="sk-…" autocomplete="off" />
        <label>Base URL</label><input id="llmOpenaiEndpoint" type="text" value="https://api.openai.com/v1" />
        <label>Model</label><input id="llmOpenaiModel" type="text" value="gpt-4o-mini" />
      </div>
      <div id="llmFieldsLocal" class="llm-fields">
        <label>Endpoint URL</label><input id="llmLocalEndpoint" type="text" value="http://localhost:11434/v1/chat/completions" />
        <label>Model</label><input id="llmLocalModel" type="text" value="llama3" />
      </div>
      <div class="llm-fields" id="reachModelFields">
        <label for="reachProvider">AI provider</label><select id="reachProvider"><option value="ollama">Ollama (local)</option><option value="openai_compatible">Local runtime</option><option value="openai">OpenAI (paid)</option><option value="anthropic">Anthropic (paid)</option></select>
        <label for="reachModel">Model</label><input id="reachModel" type="text" autocomplete="off" />
        <label for="reachCredential">Credential ID</label><input id="reachCredential" type="text" autocomplete="off" />
        <label for="reachBaseURL">Provider base URL</label><input id="reachBaseURL" type="text" autocomplete="off" />
      </div>
      <div id="llmFieldsPubpartner" class="llm-fields">
        <label>PubPartner URL</label><input id="llmPPEndpoint" type="text" value="" placeholder="Current Foresight host" />
        <label>Auth token (if set)</label><input id="llmPPToken" type="password" autocomplete="off" />
      </div>
    </div>
    <div class="modal-actions">
      <button class="mc-btn" id="llmTestBtn">Test</button>
      <button class="mc-btn" id="llmCancelBtn">Cancel</button>
      <button class="mc-btn primary" id="llmSaveBtn">Save</button>
    </div>
    <div id="llmTestResult" class="test-result"></div>
  </div>
</div>

<!-- FIND & REPLACE MODAL -->
<div class="modal-backdrop" id="frModalBackdrop">
  <div class="modal">
    <div class="modal-title">Find &amp; Replace</div>
    <div class="modal-body">
      <label>Find</label><input id="frFind" type="text" placeholder="text to find…" autocomplete="off" />
      <label>Replace with</label><input id="frReplace" type="text" placeholder="replacement…" autocomplete="off" />
    </div>
    <div class="modal-actions">
      <button class="mc-btn" id="frCloseBtn">Close</button>
      <button class="mc-btn primary" id="frReplaceAllBtn">Replace all</button>
    </div>
    <div id="frResult" class="test-result"></div>
  </div>
</div>

<!-- RENAME MODAL -->
<div class="modal-backdrop" id="renameModalBackdrop">
  <div class="modal">
    <div class="modal-title">Rename Document</div>
    <div class="modal-body">
      <label>Title</label><input id="renameInput" type="text" />
    </div>
    <div class="modal-actions">
      <button class="mc-btn" onclick="closeModal('renameModalBackdrop')">Cancel</button>
      <button class="mc-btn primary" id="renameSaveBtn">Save</button>
    </div>
  </div>
</div>

<!-- KEYBOARD SHORTCUTS MODAL -->
<div class="modal-backdrop" id="kbModalBackdrop">
  <div class="modal">
    <div class="modal-title">Keyboard Shortcuts</div>
    <div class="modal-body" style="font-family:'IBM Plex Mono',monospace; font-size:11px; line-height:2;">
      <span style="color:var(--gold)">Ctrl+S</span> — Save document<br>
      <span style="color:var(--gold)">Ctrl+Z</span> — Undo<br>
      <span style="color:var(--gold)">Ctrl+Y</span> — Redo<br>
      <span style="color:var(--gold)">Ctrl+F</span> — Find &amp; replace<br>
      <span style="color:var(--gold)">Ctrl+E</span> — Export manuscript<br>
      <span style="color:var(--gold)">Ctrl+Enter</span> — Commit draft (collab mode)<br>
      <span style="color:var(--gold)">Ctrl+G</span> — Generate next (collab mode)<br>
      <span style="color:var(--gold)">Space</span> — Play/Pause (when draft area unfocused)<br>
      <span style="color:var(--gold)">Escape</span> — Close menus/modals
    </div>
    <div class="modal-actions">
      <button class="mc-btn primary" onclick="closeModal('kbModalBackdrop')">Got it</button>
    </div>
  </div>
</div>

<!-- AUTOSAVE RESTORE MODAL -->
<div class="modal-backdrop" id="autosaveModalBackdrop">
  <div class="modal">
    <div class="modal-title">Restore Autosave</div>
    <div class="modal-body" id="autosaveList" style="font-family:'IBM Plex Mono',monospace; font-size:11px;">
      Checking for autosaves…
    </div>
    <div class="modal-actions">
      <button class="mc-btn" onclick="closeModal('autosaveModalBackdrop')">Cancel</button>
    </div>
  </div>
</div>

<!-- ADD REFERENCE MODAL -->
<div class="modal-backdrop" id="addRefModalBackdrop">
  <div class="modal">
    <div class="modal-title">Add Reference</div>
    <div class="modal-body">
      <label>Name</label><input id="refNameInput" type="text" placeholder="Character profile, chapter outline…" />
      <label>Type</label>
      <select id="refTypeInput">
        <option value="notes">Notes</option>
        <option value="chapter">Chapter</option>
        <option value="research">Research</option>
        <option value="character">Character</option>
      </select>
      <label>Content</label>
      <textarea id="refContentInput" style="width:100%; min-height:120px; padding:8px; border-radius:5px; border:1px solid var(--glass-border); background:rgba(0,0,0,0.25); color:var(--parchment); font-family:'Cormorant Garamond',serif; font-size:13px; resize:vertical; outline:none;" placeholder="Paste or type reference content…"></textarea>
    </div>
    <div class="modal-actions">
      <button class="mc-btn" onclick="closeModal('addRefModalBackdrop')">Cancel</button>
      <button class="mc-btn primary" id="addRefSaveBtn">Add</button>
    </div>
  </div>
</div>

<script>
/* ═══════════════════════════════════════════════════════════════════
   PUBCAST 2i — WRITER'S ROOM — PRODUCTION BUILD
   ═══════════════════════════════════════════════════════════════════
   Single-file application. Two modes:
     WRITE  — solo word processor for manuscript editing
     COLLAB — co-writing with AI generation + approval flow
   
   All buttons wired. All features functional. No stubs.
   ═══════════════════════════════════════════════════════════════════ */

// ── LLM ENGINE ─────────────────────────────────────────────────────
let LLM_KEY = 'pubcast2i_llm_v2';
function defaultLLM() {
  return {
    provider:'pubpartner',
    claude:  { apiKey:'', model:'claude-sonnet-4-6' },
    openai:  { apiKey:'', endpoint:'https://api.openai.com/v1', model:'gpt-4o-mini' },
    local:   { endpoint:'http://localhost:11434/v1/chat/completions', model:'llama3' },
    pubpartner: { endpoint:location.origin, token:'' }
  };
}
function loadLLM() {
  try {
    const raw = localStorage.getItem(LLM_KEY);
    if (!raw) return defaultLLM();
    const p = JSON.parse(raw), d = defaultLLM();
    const m = Object.assign({}, d, p);
    for (const k of ['claude','openai','local','pubpartner']) m[k] = Object.assign({}, d[k], p[k] || {});
    // Migrate the stale original-host setting; keep intentionally selected remote hosts.
    if (/^http:\/\/localhost:8000\/?$/.test(m.pubpartner.endpoint||'')) m.pubpartner.endpoint=location.origin;
    return m;
  } catch { return defaultLLM(); }
}
function saveLLM(cfg) { try { localStorage.setItem(LLM_KEY, JSON.stringify(cfg)); } catch {} }
let llmCfg = defaultLLM(); // Load saved settings only after Reach verifies their owner.
let abortController = null;

const LLM_ADAPTERS = {
  claude: {
    label: 'Claude',
    configured(c) { return !!(c.claude.apiKey?.trim()); },
    async send(msgs, c, signal) {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method:'POST', signal,
        headers: {
          'Content-Type':'application/json',
          'x-api-key': c.claude.apiKey.trim(),
          'anthropic-version':'2023-06-01',
          'anthropic-dangerous-direct-browser-access':'true'
        },
        body: JSON.stringify({
          model: (c.claude.model || 'claude-sonnet-4-6').trim(),
          max_tokens: 800,
          messages: msgs
        })
      });
      if (!r.ok) throw new Error(`Claude API ${r.status}: ${(await r.text()).slice(0,200)}`);
      const d = await r.json();
      return (d.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n').trim();
    }
  },
  openai: {
    label: 'OpenAI',
    configured(c) { return !!(c.openai.apiKey?.trim()); },
    async send(msgs, c, signal) {
      const base = (c.openai.endpoint || 'https://api.openai.com/v1').replace(/\/+$/, '');
      const r = await fetch(base + '/chat/completions', {
        method:'POST', signal,
        headers: { 'Content-Type':'application/json', 'Authorization':'Bearer ' + c.openai.apiKey.trim() },
        body: JSON.stringify({ model: (c.openai.model || 'gpt-4o-mini').trim(), messages: msgs })
      });
      if (!r.ok) throw new Error(`OpenAI API ${r.status}`);
      const d = await r.json();
      return d.choices?.[0]?.message?.content?.trim() || '';
    }
  },
  local: {
    label: 'Local LLM',
    configured(c) { return !!(c.local.endpoint?.trim()); },
    async send(msgs, c, signal) {
      const r = await fetch(c.local.endpoint.trim(), {
        method:'POST', signal,
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ model: (c.local.model || 'llama3').trim(), messages: msgs, stream: false })
      });
      if (!r.ok) throw new Error(`Local LLM ${r.status}`);
      const d = await r.json();
      return (d.choices?.[0]?.message?.content || d.message?.content || '').trim();
    }
  },
  pubpartner: {
    label: 'PubPartner',
    configured(c) { return !!(c.pubpartner.endpoint?.trim()); },
    async send(msgs, c, signal) {
      const base = c.pubpartner.endpoint.replace(/\/+$/, '');
      const headers = { 'Content-Type':'application/json' };
      if (c.pubpartner.token?.trim()) headers['Authorization'] = 'Bearer ' + c.pubpartner.token.trim();
      const r = await fetch(base + '/api/pubpartner/turns/live', {
        method:'POST', signal, headers,
        body: JSON.stringify({ messages: msgs })
      });
      if (!r.ok) throw new Error(`PubPartner ${r.status}`);
      const d = await r.json();
      return d.reply || d.content || d.message || JSON.stringify(d);
    }
  }
};

function llmOk() { return LLM_ADAPTERS[llmCfg.provider]?.configured(llmCfg) || false; }
async function callLLM(msgs) {
  const a = LLM_ADAPTERS[llmCfg.provider];
  if (!a || !a.configured(llmCfg)) throw new Error('LLM not configured');
  abortController = new AbortController();
  try { return await a.send(msgs, llmCfg, abortController.signal); }
  finally { abortController = null; }
}
function cancelLLM() { if (abortController) { abortController.abort(); abortController = null; } }

// ── CORE STATE ─────────────────────────────────────────────────────
let coWriting = false;  // false = WRITE mode, true = COLLAB mode
let committed = [];     // finalized manuscript lines
let buffer = [];        // draft lines (collab mode)
let pool = [];          // generated lines waiting to be read
let pointer = 0;        // next line in pool
let lockedLines = new Set();
let reading = null;     // current line being read aloud
let playing = false;
let inReaction = false;
let selectedIdx = null; // selected committed line index
let editingIdx = null;  // line being edited
let generating = false;
let speaking = false;
let speechToken = 0;
let documentTitle = 'Untitled Pubcast 2i Document';
let documentDirty = false;
let documentHandle = null;
let chapters = [{ title: 'Chapter One', subtitle: '', startLine: 0 }];
let chatHistory = [];
const MAX_CHAT = 20;
let undoStack = [];
let redoStack = [];
const MAX_UNDO = 60;
let references = []; // { id, name, type, content, date }
let refIdCounter = 1;
let refFilter = 'all';
let reactionTimer = null;

// ── DOM REFS ───────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const pageSheets = $('pageSheets');
const manuscriptLines = $('manuscriptLines');
const manuscriptZone = $('manuscriptZone');
const soloTextarea = $('soloTextarea');
const lineNumbers = $('lineNumbers');
const draftArea = $('draftArea');
const readingIndicator = $('readingIndicator');
const chatLog = $('chatLog');
const chatInput = $('chatInput');
const contextMenu = $('contextMenu');

// ── UNDO / REDO ────────────────────────────────────────────────────
function snapshot() {
  undoStack.push({
    committed: [...committed],
    buffer: [...buffer],
    lockedLines: new Set(lockedLines),
    chapters: JSON.parse(JSON.stringify(chapters))
  });
  if (undoStack.length > MAX_UNDO) undoStack.shift();
  redoStack = [];
}
function undo() {
  if (!undoStack.length) return;
  redoStack.push({ committed: [...committed], buffer: [...buffer], lockedLines: new Set(lockedLines), chapters: JSON.parse(JSON.stringify(chapters)) });
  const s = undoStack.pop();
  committed = s.committed; buffer = s.buffer; lockedLines = s.lockedLines; chapters = s.chapters;
  markDirty(); render();
}
function redo() {
  if (!redoStack.length) return;
  undoStack.push({ committed: [...committed], buffer: [...buffer], lockedLines: new Set(lockedLines), chapters: JSON.parse(JSON.stringify(chapters)) });
  const s = redoStack.pop();
  committed = s.committed; buffer = s.buffer; lockedLines = s.lockedLines; chapters = s.chapters;
  markDirty(); render();
}

// ── DIRTY / AUTOSAVE ───────────────────────────────────────────────
let autosaveTimer = null;
function markDirty() {
  documentDirty = true;
  $('saveIndicator').textContent = 'unsaved';
  if (autosaveTimer) clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(writeAutosave, 3000);
}
const AUTOSAVE_DB = 'pubcast2i-autosave-v2' + (new URLSearchParams(location.search).get('file') ? '-file-'+new URLSearchParams(location.search).get('file') : '');
function openDB() {
  return new Promise(res => {
    const req = indexedDB.open(AUTOSAVE_DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore('snaps');
    req.onsuccess = () => res(req.result);
    req.onerror = () => res(null);
  });
}
async function writeAutosave() {
  try {
    const db = await openDB(); if (!db) return;
    const payload = { title: documentTitle, ts: Date.now(), state: getDocState() };
    const tx = db.transaction('snaps', 'readwrite');
    tx.objectStore('snaps').put(payload, 'autosave_' + (Date.now() % 3));
    tx.oncomplete = () => {};
  } catch {}
}
setInterval(writeAutosave, 5 * 60 * 1000);

async function listAutosaves() {
  try {
    const db = await openDB(); if (!db) return [];
    return new Promise(res => {
      const tx = db.transaction('snaps', 'readonly');
      const store = tx.objectStore('snaps');
      const req = store.getAll();
      req.onsuccess = () => res((req.result || []).filter(Boolean).sort((a, b) => b.ts - a.ts));
      req.onerror = () => res([]);
    });
  } catch { return []; }
}

// ── DOCUMENT STATE ─────────────────────────────────────────────────
function getDocState() {
  return {
    committed, buffer, pool, pointer, chapters,
    lockedLines: [...lockedLines],
    coWriting, references,
    ...(typeof partnerId !== 'undefined' ? {
      partnerId,
      conversations: {...conversations, [partnerId]: [...chatHistory]},
      conversationIds: {...conversationIds}
    } : {})
  };
}
function docPayload() {
  return { format: '2i-document', version: 4, title: documentTitle, state: getDocState() };
}
function loadDocState(state) {
  committed = state.committed || [];
  buffer = state.buffer || [];
  pool = state.pool || [];
  pointer = state.pointer || 0;
  chapters = state.chapters || [{ title: 'Chapter One', subtitle: '', startLine: 0 }];
  lockedLines = new Set(state.lockedLines || []);
  if (state.coWriting !== undefined) { coWriting = state.coWriting; updateModeUI(); }
  if (state.references) { references = state.references; refIdCounter = Math.max(1, ...references.map(r => r.id || 0)) + 1; }
  if (typeof partnerId !== 'undefined') {
    if (state.partnerId) partnerId = state.partnerId;
    conversations = state.conversations && typeof state.conversations === 'object' ? state.conversations : {};
    conversationIds = state.conversationIds && typeof state.conversationIds === 'object' ? state.conversationIds : {};
    chatHistory = conversations[partnerId] || [];
    if (typeof restoreConversation === 'function') restoreConversation();
  }
  selectedIdx = null; editingIdx = null;
  undoStack = []; redoStack = [];
  // Solo mode shows the manuscript in this textarea, and its input handler rebuilds
  // `committed` from it. If a restored document is not written back into it, the
  // writer sees a blank page and the first keystroke replaces the whole manuscript
  // (and its recovery copy) with that keystroke.
  if (!coWriting && typeof soloTextarea !== 'undefined' && soloTextarea) {
    soloTextarea.value = committed.join('\n');
  }
  render();
}

// ── SAVE / OPEN / EXPORT ───────────────────────────────────────────
function safeName() { return documentTitle.replace(/[\\/:*?"<>|]/g, '-').trim() || 'Untitled'; }
async function saveDocument() {
  if (documentHandle) {
    try {
      const w = await documentHandle.createWritable();
      await w.write(JSON.stringify(docPayload(), null, 2));
      await w.close();
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      return;
    } catch {}
  }
  await saveDocumentAs();
}
async function saveDocumentAs() {
  const payload = docPayload();
  if ('showSaveFilePicker' in window) {
    try {
      const h = await window.showSaveFilePicker({
        suggestedName: safeName() + '.2i',
        types: [{ description: '2i Document', accept: { 'application/json': ['.2i'] } }]
      });
      const w = await h.createWritable(); await w.write(JSON.stringify(payload, null, 2)); await w.close();
      documentHandle = h; documentDirty = false; $('saveIndicator').textContent = 'saved';
      return;
    } catch {}
  }
  // Fallback: download
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = safeName() + '.2i'; a.click(); URL.revokeObjectURL(a.href);
  documentDirty = false; $('saveIndicator').textContent = 'saved';
}
async function openDocument() {
  if ('showOpenFilePicker' in window) {
    try {
      const [h] = await window.showOpenFilePicker({
        types: [{ description: '2i Document', accept: { 'application/json': ['.2i'] } }]
      });
      const file = await h.getFile();
      const text = await file.text();
      const doc = JSON.parse(text);
      if (doc.format !== '2i-document') throw new Error('Not a 2i document');
      documentTitle = doc.title || 'Untitled';
      documentHandle = h;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
      return;
    } catch (e) { if (e.name !== 'AbortError') addChat('pp', '⚠ ' + e.message); return; }
  }
  // Fallback: file input
  const inp = document.createElement('input'); inp.type = 'file'; inp.accept = '.2i,.json';
  inp.onchange = async () => {
    const file = inp.files[0]; if (!file) return;
    try {
      const text = await file.text();
      const doc = JSON.parse(text);
      documentTitle = doc.title || 'Untitled';
      documentHandle = null;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
    } catch (e) { addChat('pp', '⚠ ' + e.message); }
  };
  inp.click();
}
function exportManuscript() {
  let md = '# ' + documentTitle + '\n\n';
  let chIdx = 0;
  committed.forEach((line, i) => {
    const ch = chapters.find(c => c.startLine === i);
    if (ch) { md += '\n## ' + ch.title + (ch.subtitle ? '\n*' + ch.subtitle + '*' : '') + '\n\n'; }
    md += line + '\n';
  });
  if (buffer.length) { md += '\n---\n*Draft:*\n\n' + buffer.join('\n') + '\n'; }
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = safeName() + '.md'; a.click(); URL.revokeObjectURL(a.href);
}
function newDocument() {
  if (documentDirty && !confirm('Discard unsaved changes?')) return;
  committed = []; buffer = []; pool = []; pointer = 0;
  lockedLines = new Set(); chapters = [{ title:'Chapter One', subtitle:'', startLine:0 }];
  selectedIdx = null; editingIdx = null; reading = null;
  documentTitle = 'Untitled Pubcast 2i Document'; documentHandle = null;
  documentDirty = false; $('saveIndicator').textContent = 'unsaved';
  undoStack = []; redoStack = []; chatHistory = [];
  chatLog.innerHTML = ''; references = [];
  render();
}

// ── MODE SWITCHING ─────────────────────────────────────────────────
function updateModeUI() {
  const badge = $('modeBadge');
  if (coWriting) {
    badge.textContent = 'Collab'; badge.className = 'mode-badge collab';
    pageSheets.classList.remove('solo-mode');
    $('collabOnlyControls').classList.remove('hidden');
    $('playbackControls').classList.remove('hidden');
    $('zoneLabel').textContent = 'Manuscript — locked';
  } else {
    badge.textContent = 'Write'; badge.className = 'mode-badge write';
    pageSheets.classList.add('solo-mode');
    $('collabOnlyControls').classList.add('hidden');
    $('playbackControls').classList.add('hidden');
    $('zoneLabel').textContent = 'Manuscript';
  }
}
function toggleMode() {
  if (coWriting && buffer.length) approveBuffer();
  coWriting = !coWriting;
  if (!coWriting) {
    // switching to solo: merge committed into textarea
    soloTextarea.value = committed.join('\n');
    stopPlaying();
  } else {
    // switching to collab: split textarea back into committed
    const text = soloTextarea.value;
    committed = text.split('\n');
    buffer = [];
  }
  updateModeUI(); markDirty(); render();
}
$('modeBadge').onclick = toggleMode;

// ── APPROVE / LOCK / UNLOCK / CHAPTERS ─────────────────────────────
function approveBuffer() {
  if (!buffer.length) return;
  snapshot();
  const approved = buffer.slice();
  committed.push(...buffer);
  buffer = []; draftArea.value = '';
  selectedIdx = null; editingIdx = null;
  markDirty(); render();
  closeMenu();
  approved.forEach(t => { if (ppWasGenerated(t)) ppVoiceSignal('accepted', t); });
  ppCommit();
}
function lockScene() {
  snapshot();
  // Lock lines from the last chapter start to end of committed
  const lastChapter = [...chapters].reverse().find(c => c.startLine <= committed.length - 1);
  const start = lastChapter ? lastChapter.startLine : 0;
  for (let i = start; i < committed.length; i++) lockedLines.add(i);
  markDirty(); render();
}
function lockAll() {
  snapshot();
  committed.forEach((_, i) => lockedLines.add(i));
  markDirty(); render();
}
function unlockSelected() {
  if (selectedIdx === null) { addChat('pp', 'Select a line first, then unlock it.'); return; }
  snapshot();
  lockedLines.delete(selectedIdx);
  markDirty(); render();
}
function newChapter() {
  snapshot();
  const num = chapters.length + 1;
  const title = prompt('Chapter title:', 'Chapter ' + numberToWord(num));
  if (!title) return;
  const sub = prompt('Subtitle (optional):', '') || '';
  chapters.push({ title, subtitle: sub, startLine: committed.length + buffer.length });
  markDirty(); render();
}
function numberToWord(n) {
  const w = ['One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve'];
  return w[n - 1] || String(n);
}

$('approveBtn').onclick = approveBuffer;
$('lockSceneBtn').onclick = lockScene;
$('lockAllBtn').onclick = lockAll;
$('unlockBtn').onclick = unlockSelected;
$('newChapterBtn').onclick = newChapter;
$('exportBtn').onclick = () => { exportManuscript(); closeMenu(); };

// ── AI GENERATION ──────────────────────────────────────────────────
async function generateMore() {
  if (generating || !llmOk()) return false;
  generating = true; $('genBtn').disabled = true;
  $('statusText').textContent = 'generating…';
  try {
    if (PP.online) {
      try {
        const lines = await ppGenerate();
        if (lines.length) {
          lines.forEach(l => ppMarkGenerated(l));
          pool = pool.concat(lines);
          return true;
        }
      } catch (e) { console.debug('[2i] falling back to direct LLM:', e.message); }
    }
    const context = committed.slice(-8).join('\n') + (buffer.length ? '\n' + buffer.join('\n') : '');
    const prompt = 'Continue this manuscript with the next 2-4 sentences of prose. Return ONLY the new prose, each sentence on its own line.\n\nContext:\n' + context;
    const reply = await callLLM([{ role: 'user', content: prompt }]);
    const lines = reply.split(/\n+/).map(l => l.trim()).filter(Boolean);
    if (lines.length) { lines.forEach(l => ppMarkGenerated(l)); pool = pool.concat(lines); return true; }
  } catch (e) {
    if (e.name !== 'AbortError') addChat('pp', '⚠ Generation failed: ' + e.message);
  } finally {
    generating = false; $('genBtn').disabled = false; render();
  }
  return false;
}
$('genBtn').onclick = () => { if (!playing && !generating) { closeMenu(); tick(); } };

// ── PLAYBACK / TICK ────────────────────────────────────────────────
async function tick() {
  if (reading) { buffer.push(reading.text); markDirty(); reading = null; }
  if (pointer >= pool.length && llmOk() && !generating) {
    const got = await generateMore();
    if (!got) { stopPlaying(); render(); return; }
  }
  if (pointer < pool.length) {
    reading = { text: pool[pointer] }; pointer++;
    markDirty(); render();
    if (playing) {
      speechRead(reading.text, () => {
        if (!playing || !reading) return;
        inReaction = true; render();
        reactionTimer = setTimeout(() => { inReaction = false; if (playing) tick(); }, 6000);
      });
    }
  } else { stopPlaying(); }
  render();
}
function startPlaying() {
  if (playing) return;
  playing = true; inReaction = false;
  if (!reading) tick();
  else speechRead(reading.text, () => {
    inReaction = true; render();
    reactionTimer = setTimeout(() => { inReaction = false; tick(); }, 6000);
  });
  render();
}
function stopPlaying() {
  cancelSpeech(); cancelLLM();
  if (reactionTimer) { clearTimeout(reactionTimer); reactionTimer = null; }
  inReaction = false; playing = false; render();
}

$('playBtn').onclick = () => playing ? stopPlaying() : startPlaying();
$('stopBtn').onclick = stopPlaying;
$('skipBtn').onclick = () => {
  if (inReaction) { inReaction = false; if (reactionTimer) clearTimeout(reactionTimer); if (playing) tick(); return; }
  if (playing && reading) { cancelSpeech(); tick(); }
  else if (!playing) tick();
};

// ── SPEECH ─────────────────────────────────────────────────────────
function speechRead(text, done) {
  if (!('speechSynthesis' in window)) { if (done) done(); return; }
  const token = ++speechToken;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = parseFloat($('speedSlider').value) || 1;
  u.onstart = () => { if (token !== speechToken) return; speaking = true; render(); };
  u.onend = () => { if (token !== speechToken) return; speaking = false; render(); if (done) done(); };
  u.onerror = () => { if (token !== speechToken) return; speaking = false; render(); if (done) done(); };
  window.speechSynthesis.speak(u);
}
function cancelSpeech() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  speechToken++; speaking = false;
}

// ── CHAT ───────────────────────────────────────────────────────────
function escHtml(s) { return s.replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
function addChat(who, text, thinking) {
  const div = document.createElement('div');
  div.className = 'chat-msg ' + (who === 'you' ? 'you' : 'pp') + (thinking ? ' thinking' : '');
  div.innerHTML = '<span class="who">' + (who === 'you' ? 'You' : 'PubPartner') + '</span>' + escHtml(text);
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}
let chatSending = false;
async function sendChat() {
  if (chatSending) return;
  const v = chatInput.value.trim(); if (!v) return;
  chatSending = true; addChat('you', v); chatInput.value = '';
  chatHistory.push({ role: 'user', content: v });
  if (chatHistory.length > MAX_CHAT * 2) chatHistory = chatHistory.slice(-MAX_CHAT * 2);
  $('chatSendBtn').disabled = true;
  const thinkEl = addChat('pp', '…thinking…', true);
  try {
    const sys = 'You are PubPartner, a creative writing collaborator. Be concise and helpful.\nManuscript context:\n' + committed.slice(-6).join('\n');
    const reply = await callLLM([{ role: 'user', content: sys }, ...chatHistory.slice(-MAX_CHAT)]);
    thinkEl.remove(); addChat('pp', reply || '(empty)');
    chatHistory.push({ role: 'assistant', content: reply || '' });
  } catch (e) {
    thinkEl.remove();
    if (e.name !== 'AbortError') addChat('pp', '⚠ ' + e.message);
  } finally { $('chatSendBtn').disabled = false; chatSending = false; }
}
$('chatSendBtn').onclick = sendChat;
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

// Voice input
const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = $('chatMicBtn');
if (SpeechAPI) {
  const rec = new SpeechAPI(); rec.interimResults = true;
  let listening = false, baseText = '';
  rec.onresult = e => {
    let t = '';
    for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript;
    chatInput.value = (baseText + ' ' + t).trim();
  };
  rec.onend = () => { listening = false; micBtn.classList.remove('listening'); };
  micBtn.onclick = () => {
    if (listening) { rec.stop(); return; }
    baseText = chatInput.value.trim(); rec.start(); listening = true; micBtn.classList.add('listening');
  };
} else {
  micBtn.disabled = true; micBtn.title = 'Speech not supported in this browser';
}

// ── REFERENCE ARCHIVE ──────────────────────────────────────────────
function addReference(name, type, content) {
  references.push({ id: refIdCounter++, name, type: type || 'notes', content, date: new Date().toLocaleDateString() });
  markDirty(); renderRefs();
}
function deleteReference(id) {
  references = references.filter(r => r.id !== id);
  markDirty(); renderRefs();
}
function renderRefs() {
  const container = $('refListContainer');
  const search = $('refSearchInput').value.toLowerCase();
  container.innerHTML = '';
  const filtered = references.filter(r => {
    if (refFilter !== 'all' && r.type !== refFilter) return false;
    if (search && !r.name.toLowerCase().includes(search) && !r.content.toLowerCase().includes(search)) return false;
    return true;
  });
  if (!filtered.length) {
    container.innerHTML = '<div style="font-size:11px; color:var(--parchment-soft); padding:8px; text-align:center;">No references yet</div>';
    return;
  }
  const icons = { chapter:'📖', research:'🔬', notes:'📝', character:'👤' };
  filtered.forEach(r => {
    const el = document.createElement('div'); el.className = 'ref-item';
    el.innerHTML = `<div class="ref-icon">${icons[r.type] || '📄'}</div>
      <div class="ref-meta">
        <div class="ref-name">${escHtml(r.name)}</div>
        <div class="ref-type">${r.type}</div>
        <div class="ref-date">${r.date}</div>
      </div>
      <div class="ref-actions">
        <button class="ref-action-btn" title="View" onclick="viewRef(${r.id})">📋</button>
        <button class="ref-action-btn" title="Delete" onclick="if(confirm('Delete this reference?'))deleteReference(${r.id})">✕</button>
      </div>`;
    container.appendChild(el);
  });
}
function viewRef(id) {
  const r = references.find(x => x.id === id); if (!r) return;
  $('refViewerTitle').textContent = r.name;
  $('refViewerBody').textContent = r.content;
  $('refViewer').classList.add('open');
}
function closeRefViewer() { $('refViewer').classList.remove('open'); }
function setRefFilter(btn, filter) {
  refFilter = filter;
  document.querySelectorAll('.ref-tab').forEach(t => t.classList.toggle('active', t.dataset.filter === filter));
  renderRefs();
}
function filterRefs() { renderRefs(); }
$('refSearchInput').addEventListener('input', renderRefs);

$('addRefBtn').onclick = () => {
  $('refNameInput').value = '';
  $('refTypeInput').value = 'notes';
  $('refContentInput').value = '';
  openModal('addRefModalBackdrop');
  setTimeout(() => $('refNameInput').focus(), 100);
};
$('addRefSaveBtn').onclick = () => {
  const name = $('refNameInput').value.trim();
  if (!name) { $('refNameInput').focus(); return; }
  addReference(name, $('refTypeInput').value, $('refContentInput').value);
  closeModal('addRefModalBackdrop');
};

// ── FIND & REPLACE ─────────────────────────────────────────────────
$('frReplaceAllBtn').onclick = () => {
  const find = $('frFind').value;
  const replace = $('frReplace').value;
  if (!find || find.length === 0) {
    $('frResult').textContent = 'Enter text to find.';
    $('frResult').className = 'test-result err';
    return;
  }
  snapshot();
  let count = 0;
  // Replace in committed
  committed = committed.map(l => {
    if (l.includes(find)) { count += l.split(find).length - 1; return l.split(find).join(replace); }
    return l;
  });
  // Replace in buffer
  buffer = buffer.map(l => {
    if (l.includes(find)) { count += l.split(find).length - 1; return l.split(find).join(replace); }
    return l;
  });
  // Replace in reading
  if (reading?.text?.includes(find)) {
    count += reading.text.split(find).length - 1;
    reading.text = reading.text.split(find).join(replace);
  }
  // Replace in solo textarea
  if (!coWriting) {
    const val = soloTextarea.value;
    if (val.includes(find)) {
      count += val.split(find).length - 1;
      soloTextarea.value = val.split(find).join(replace);
      committed = soloTextarea.value.split('\n');
    }
  }
  $('frResult').textContent = count + ' replacement' + (count !== 1 ? 's' : '') + ' made';
  $('frResult').className = 'test-result ok';
  markDirty(); render();
};

// ── CONTEXT MENU ───────────────────────────────────────────────────
function showContextMenu(e, idx) {
  e.preventDefault();
  selectedIdx = idx;
  const locked = lockedLines.has(idx);
  $('ctxLock').style.display = locked ? 'none' : '';
  $('ctxUnlock').style.display = locked ? '' : 'none';
  contextMenu.classList.add('open');
  const cmW = contextMenu.offsetWidth || 170;
  const cmH = contextMenu.offsetHeight || 200;
  const cx = Math.min(e.clientX, window.innerWidth - cmW - 8);
  const cy = Math.min(e.clientY, window.innerHeight - cmH - 8);
  contextMenu.style.left = Math.max(0, cx) + 'px';
  contextMenu.style.top = Math.max(0, cy) + 'px';
  render();
}
document.addEventListener('click', () => contextMenu.classList.remove('open'));

$('ctxEdit').onclick = () => {
  if (selectedIdx === null) return;
  if (lockedLines.has(selectedIdx)) { addChat('pp', 'Unlock the line first.'); return; }
  editingIdx = selectedIdx; render();
};
$('ctxInsertAbove').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); committed.splice(selectedIdx, 0, '');
  // Shift locked lines
  const newLocked = new Set();
  lockedLines.forEach(i => newLocked.add(i >= selectedIdx ? i + 1 : i));
  lockedLines = newLocked;
  // Shift chapter startLines
  chapters.forEach(c => { if (c.startLine >= selectedIdx) c.startLine++; });
  editingIdx = selectedIdx;
  markDirty(); render();
};
$('ctxInsertBelow').onclick = () => {
  if (selectedIdx === null) return;
  const insertAt = selectedIdx + 1;
  snapshot(); committed.splice(insertAt, 0, '');
  const newLocked = new Set();
  lockedLines.forEach(i => newLocked.add(i >= insertAt ? i + 1 : i));
  lockedLines = newLocked;
  chapters.forEach(c => { if (c.startLine >= insertAt) c.startLine++; });
  editingIdx = insertAt; selectedIdx = insertAt;
  markDirty(); render();
};
$('ctxLock').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); lockedLines.add(selectedIdx); markDirty(); render();
};
$('ctxUnlock').onclick = () => {
  if (selectedIdx === null) return;
  snapshot(); lockedLines.delete(selectedIdx); markDirty(); render();
};
$('ctxDelete').onclick = () => {
  if (selectedIdx === null) return;
  if (lockedLines.has(selectedIdx)) { addChat('pp', 'Unlock the line before deleting.'); return; }
  snapshot(); committed.splice(selectedIdx, 1);
  const newLocked = new Set();
  lockedLines.forEach(i => { if (i < selectedIdx) newLocked.add(i); else if (i > selectedIdx) newLocked.add(i - 1); });
  lockedLines = newLocked;
  chapters.forEach(c => { if (c.startLine > selectedIdx) c.startLine--; });
  selectedIdx = null; markDirty(); render();
};

// ── RENDER ──────────────────────────────────────────────────────────
function render() {
  // Status
  $('statusDot').className = 'status-dot ' + (playing ? 'playing' : 'paused');
  $('statusText').textContent = playing ? (speaking ? 'reading aloud…' : 'reading…') : (generating ? 'generating…' : 'idle');
  $('playBtn').textContent = playing ? '⏸' : '▶';
  $('playBtn').classList.toggle('active', playing);
  $('docTitleDisplay').textContent = documentTitle;

  // Word count
  let allText;
  if (coWriting) {
    allText = committed.join(' ') + ' ' + buffer.join(' ');
  } else {
    allText = soloTextarea.value;
  }
  const wc = allText.trim().split(/\s+/).filter(Boolean).length;
  $('wordCount').textContent = wc.toLocaleString() + ' words';
  $('mcWordProgress').textContent = wc.toLocaleString() + ' words';

  // Manuscript control status
  const allLocked = committed.length > 0 && committed.every((_, i) => lockedLines.has(i));
  $('mcDraftStatus').textContent = allLocked ? 'Locked' : 'Active';
  const targetWc = 50000; // reasonable novel target
  const pct = Math.min(100, Math.round((wc / targetWc) * 100));
  $('mcPercent').textContent = pct + '%';
  $('mcProgressFill').style.width = pct + '%';

  // LLM pill
  if (llmOk()) {
    $('llmPill').textContent = LLM_ADAPTERS[llmCfg.provider].label;
    $('llmPill').className = 'llm-pill ok';
  } else {
    $('llmPill').textContent = 'no LLM';
    $('llmPill').className = 'llm-pill';
  }

  if (coWriting) {
    renderManuscriptLines();
    renderReading();
    draftArea.value = buffer.join('\n');
  } else {
    updateLineNumbers();
  }

  renderRefs();
}

function renderManuscriptLines() {
  manuscriptLines.innerHTML = '';
  let lineNum = 1;
  committed.forEach((text, i) => {
    // Check for chapter heading
    const ch = chapters.find(c => c.startLine === i);
    if (ch) {
      const heading = document.createElement('div'); heading.className = 'chapter-heading';
      heading.textContent = ch.title; manuscriptLines.appendChild(heading);
      if (ch.subtitle) {
        const sub = document.createElement('div'); sub.className = 'chapter-subtitle';
        sub.textContent = ch.subtitle; manuscriptLines.appendChild(sub);
      }
      const divider = document.createElement('div'); divider.className = 'chapter-divider';
      divider.innerHTML = '✦ ✦ ✦'; manuscriptLines.appendChild(divider);
    }

    if (editingIdx === i) {
      // Editing mode
      const wrap = document.createElement('div'); wrap.className = 'm-line selected';
      wrap.innerHTML = `<span class="line-num">${lineNum}</span>`;
      const editDiv = document.createElement('div'); editDiv.className = 'm-line-edit'; editDiv.style.flex = '1';
      const ta = document.createElement('textarea'); ta.value = text; ta.rows = 2;
      ta.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault(); snapshot();
          const before = committed[i];
          committed[i] = ta.value;
          editingIdx = null; markDirty(); render();
          if (before !== ta.value && ppWasGenerated(before)) {
            ppVoiceSignal('rewritten', before, ta.value);
            ppForgetGenerated(before);
          }
          ppCommit();
        }
        if (e.key === 'Escape') { editingIdx = null; render(); }
      });
      editDiv.appendChild(ta); wrap.appendChild(editDiv);
      manuscriptLines.appendChild(wrap);
      setTimeout(() => ta.focus(), 0);
    } else {
      const div = document.createElement('div');
      div.className = 'm-line' + (selectedIdx === i ? ' selected' : '') + (lockedLines.has(i) ? ' locked' : '');
      div.innerHTML = `<span class="line-num">${lineNum}</span>${escHtml(text)}`;
      div.onclick = () => { selectedIdx = (selectedIdx === i) ? null : i; render(); };
      div.oncontextmenu = e => showContextMenu(e, i);
      div.ondblclick = () => {
        if (lockedLines.has(i)) { addChat('pp', 'Unlock the line to edit it.'); return; }
        editingIdx = i; render();
      };
      manuscriptLines.appendChild(div);
    }
    lineNum++;
  });

  // Scroll to bottom
  manuscriptZone.scrollTop = manuscriptZone.scrollHeight;
}

function renderReading() {
  readingIndicator.innerHTML = '';
  if (reading) {
    const div = document.createElement('div');
    div.className = 'reading-line' + (inReaction ? ' reaction' : '');
    div.textContent = reading.text;
    // Accept/reject buttons
    const btns = document.createElement('div');
    btns.style.cssText = 'display:flex; gap:6px; margin:4px 0 0 55px;';
    const acceptBtn = document.createElement('button'); acceptBtn.className = 'mc-btn primary';
    acceptBtn.textContent = '✓ Accept'; acceptBtn.style.cssText = 'padding:3px 10px; font-size:9px;';
    acceptBtn.onclick = () => { buffer.push(reading.text); reading = null; markDirty(); render(); };
    const rejectBtn = document.createElement('button'); rejectBtn.className = 'mc-btn danger';
    rejectBtn.textContent = '✕ Reject'; rejectBtn.style.cssText = 'padding:3px 10px; font-size:9px;';
    rejectBtn.onclick = () => { ppVoiceSignal('rejected', reading.text); ppForgetGenerated(reading.text); reading = null; render(); };
    btns.appendChild(acceptBtn); btns.appendChild(rejectBtn);
    readingIndicator.appendChild(div);
    if (!playing) readingIndicator.appendChild(btns);
  }
}

function updateLineNumbers() {
  const lines = soloTextarea.value.split('\n');
  lineNumbers.innerHTML = lines.map((_, i) => (i + 1)).join('<br>');
}

// Sync solo textarea scroll with line numbers
soloTextarea.addEventListener('scroll', () => { lineNumbers.scrollTop = soloTextarea.scrollTop; });
soloTextarea.addEventListener('input', () => {
  updateLineNumbers();
  committed = soloTextarea.value.split('\n');
  markDirty();
});
draftArea.addEventListener('input', () => {
  buffer = draftArea.value.split('\n');
  markDirty();
});

// ── LLM MODAL ──────────────────────────────────────────────────────
function showLLMFields() {
  const p = $('llmProvider').value;
  document.querySelectorAll('.llm-fields').forEach(el => el.classList.remove('active'));
  const map = { claude:'llmFieldsClaude', openai:'llmFieldsOpenai', local:'llmFieldsLocal', pubpartner:'llmFieldsPubpartner' };
  if (map[p]) $(map[p]).classList.add('active');
}
$('llmProvider').onchange = showLLMFields;

function openLLMModal() {
  $('llmProvider').value = llmCfg.provider;
  $('llmClaudeKey').value = llmCfg.claude.apiKey || '';
  $('llmClaudeModel').value = llmCfg.claude.model || '';
  $('llmOpenaiKey').value = llmCfg.openai.apiKey || '';
  $('llmOpenaiEndpoint').value = llmCfg.openai.endpoint || '';
  $('llmOpenaiModel').value = llmCfg.openai.model || '';
  $('llmLocalEndpoint').value = llmCfg.local.endpoint || '';
  $('llmLocalModel').value = llmCfg.local.model || '';
  $('llmPPEndpoint').value = llmCfg.pubpartner.endpoint || '';
  $('llmPPToken').value = llmCfg.pubpartner.token || '';
  $('llmTestResult').textContent = '';
  showLLMFields();
  openModal('llmModalBackdrop');
}
$('llmSaveBtn').onclick = () => {
  llmCfg = {
    provider: $('llmProvider').value,
    claude: { apiKey: $('llmClaudeKey').value, model: $('llmClaudeModel').value },
    openai: { apiKey: $('llmOpenaiKey').value, endpoint: $('llmOpenaiEndpoint').value, model: $('llmOpenaiModel').value },
    local: { endpoint: $('llmLocalEndpoint').value, model: $('llmLocalModel').value },
    pubpartner: { endpoint: $('llmPPEndpoint').value, token: $('llmPPToken').value }
  };
  saveLLM(llmCfg); closeModal('llmModalBackdrop'); render();
};
$('llmCancelBtn').onclick = () => closeModal('llmModalBackdrop');
$('llmTestBtn').onclick = async () => {
  $('llmTestResult').textContent = 'Testing…'; $('llmTestResult').className = 'test-result';
  // Temporarily apply modal values
  const tempCfg = {
    provider: $('llmProvider').value,
    claude: { apiKey: $('llmClaudeKey').value, model: $('llmClaudeModel').value },
    openai: { apiKey: $('llmOpenaiKey').value, endpoint: $('llmOpenaiEndpoint').value, model: $('llmOpenaiModel').value },
    local: { endpoint: $('llmLocalEndpoint').value, model: $('llmLocalModel').value },
    pubpartner: { endpoint: $('llmPPEndpoint').value, token: $('llmPPToken').value }
  };
  const adapter = LLM_ADAPTERS[tempCfg.provider];
  if (!adapter || !adapter.configured(tempCfg)) {
    $('llmTestResult').textContent = 'Not configured — fill in the fields above.';
    $('llmTestResult').className = 'test-result err'; return;
  }
  try {
    const reply = await adapter.send([{ role: 'user', content: 'Say "connected" and nothing else.' }], tempCfg);
    $('llmTestResult').textContent = '✓ Connected: ' + reply.slice(0, 60);
    $('llmTestResult').className = 'test-result ok';
  } catch (e) {
    $('llmTestResult').textContent = '✕ ' + e.message;
    $('llmTestResult').className = 'test-result err';
  }
};
$('llmPill').onclick = openLLMModal;

// ── MENUS & MODALS ─────────────────────────────────────────────────
function openModal(id) { $(id).classList.add('open'); closeMenu(); }
function closeModal(id) { $(id).classList.remove('open'); }
function closeMenu() { $('hamburgerMenu').classList.remove('open'); }

// Click backdrop to close any modal
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) backdrop.classList.remove('open');
  });
});
function toggleSection(id) { $(id).classList.toggle('collapsed'); }

$('menuToggle').onclick = e => { e.stopPropagation(); $('hamburgerMenu').classList.toggle('open'); };
document.addEventListener('click', e => {
  if (!$('hamburgerMenu').contains(e.target) && e.target !== $('menuToggle')) closeMenu();
});

$('sidebarToggle').onclick = () => {
  $('mainArea').classList.toggle('sidebar-hidden');
};

$('hmNewDoc').onclick = () => { closeMenu(); newDocument(); };
$('hmOpenDoc').onclick = () => { closeMenu(); openDocument(); };
$('hmSaveAs').onclick = () => { closeMenu(); saveDocumentAs(); };
$('hmFindReplace').onclick = () => { $('frResult').textContent = ''; openModal('frModalBackdrop'); };
$('frCloseBtn').onclick = () => closeModal('frModalBackdrop');
$('hmLLMSettings').onclick = () => { closeMenu(); openLLMModal(); };
$('hmKeyboardHelp').onclick = () => { closeMenu(); openModal('kbModalBackdrop'); };
$('hmRenameDoc').onclick = () => {
  closeMenu(); $('renameInput').value = documentTitle; openModal('renameModalBackdrop');
  setTimeout(() => $('renameInput').focus(), 100);
};
$('renameSaveBtn').onclick = () => {
  documentTitle = $('renameInput').value.trim() || 'Untitled';
  markDirty(); render(); closeModal('renameModalBackdrop');
};
$('docTitleDisplay').onclick = () => {
  $('renameInput').value = documentTitle; openModal('renameModalBackdrop');
  setTimeout(() => $('renameInput').focus(), 100);
};
$('saveBtn').onclick = saveDocument;

// Autosave restore
$('hmRestoreAutosave').onclick = async () => {
  closeMenu();
  const list = await listAutosaves();
  const container = $('autosaveList');
  if (!list.length) {
    container.innerHTML = 'No autosaves found.';
  } else {
    container.innerHTML = '';
    list.forEach((snap, i) => {
      const btn = document.createElement('button');
      btn.className = 'mc-btn';
      btn.style.cssText = 'width:100%; text-align:left; margin:4px 0;';
      btn.textContent = (snap.title || 'Untitled') + ' — ' + new Date(snap.ts).toLocaleString();
      btn.onclick = () => {
        documentTitle = snap.title || 'Untitled';
        loadDocState(snap.state);
        closeModal('autosaveModalBackdrop');
        render();
      };
      container.appendChild(btn);
    });
  }
  openModal('autosaveModalBackdrop');
};

// ── KEYBOARD SHORTCUTS ─────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // Escape: close modals/menus
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(m => m.classList.remove('open'));
    contextMenu.classList.remove('open');
    closeMenu();
    if (editingIdx !== null) { editingIdx = null; render(); }
    return;
  }
  if (e.ctrlKey || e.metaKey) {
    if (e.key === 's') { e.preventDefault(); saveDocument(); }
    if (e.key === 'z') { e.preventDefault(); undo(); }
    if (e.key === 'y') { e.preventDefault(); redo(); }
    if (e.key === 'f') { e.preventDefault(); $('frResult').textContent = ''; openModal('frModalBackdrop'); setTimeout(() => $('frFind').focus(), 100); }
    if (e.key === 'e') { e.preventDefault(); exportManuscript(); }
    if (e.key === 'Enter' && coWriting) { e.preventDefault(); approveBuffer(); }
    if (e.key === 'g' && coWriting) { e.preventDefault(); if (!generating) tick(); }
  }
});

// ── CANVAS: LANTERN LIGHT ──────────────────────────────────────────
(function initLantern() {
  const frame = $('notebookFrame'); if (!frame) return;
  const canvas = $('lanternCanvas');
  const ctx = canvas.getContext('2d', { alpha: true });
  let w = 0, h = 0, mx = 300, my = 100, raf = 0;
  function resize() {
    w = frame.clientWidth; h = frame.clientHeight;
    canvas.width = w; canvas.height = h; draw();
  }
  function draw() {
    ctx.clearRect(0, 0, w, h);
    const g = ctx.createRadialGradient(mx, my, 0, mx, my, 380);
    g.addColorStop(0, 'rgba(238,207,131,0.12)');
    g.addColorStop(0.35, 'rgba(238,207,131,0.04)');
    g.addColorStop(0.7, 'rgba(238,207,131,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  }
  frame.addEventListener('pointermove', e => {
    if(document.documentElement.dataset.foresightActivity && document.documentElement.dataset.foresightActivity!=='full')return;
    const r = frame.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top;
    if (!raf) raf = requestAnimationFrame(() => { draw(); raf = 0; });
  });
  window.addEventListener('resize', resize); resize();
})();

// ── CANVAS: SPIRAL SPINE ───────────────────────────────────────────
function drawSpine() {
  const canvas = $('spineCanvas'); if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height, cx = W * 0.55, rx = Math.min(18, W * 0.34);
  const pitch = 22;

  // Background shadow
  ctx.fillStyle = 'rgba(0,0,0,0.4)';
  ctx.fillRect(cx - rx - 6, 0, rx * 2 + 12, H);

  for (let i = 0; i < H / pitch + 1; i++) {
    const y = i * pitch + 6;
    // Coil shadow
    ctx.beginPath(); ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 5;
    ctx.moveTo(cx - rx, y + 2); ctx.lineTo(cx + rx, y + 7);
    ctx.stroke();
    // Coil body
    ctx.beginPath();
    ctx.strokeStyle = '#bca36f'; ctx.lineWidth = 3.5;
    ctx.moveTo(cx - rx, y); ctx.lineTo(cx + rx, y + 5);
    ctx.stroke();
    // Highlight
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255,240,200,0.35)'; ctx.lineWidth = 1;
    ctx.moveTo(cx - rx + 1, y - 1); ctx.lineTo(cx + rx - 1, y + 4);
    ctx.stroke();
  }
}
window.addEventListener('load', drawSpine);
window.addEventListener('resize', drawSpine);

// ── INIT ───────────────────────────────────────────────────────────
function init() {
  updateModeUI();
  render();
  drawSpine();

  // Load any existing autosave notification
  listAutosaves().then(list => {
    if (list.length && !committed.length && !soloTextarea.value.trim()) {
      addChat('pp', 'I found autosaved work. Use Menu → Restore autosave to recover it.');
    }
  });
}
// ── DRAG & DROP ────────────────────────────────────────────────────
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', async e => {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  if (file.name.endsWith('.2i') || file.name.endsWith('.json')) {
    try {
      const text = await file.text();
      const doc = JSON.parse(text);
      if (doc.format !== '2i-document') { addChat('pp', '⚠ Not a 2i document.'); return; }
      if (documentDirty && !confirm('Discard unsaved changes?')) return;
      documentTitle = doc.title || 'Untitled';
      documentHandle = null;
      loadDocState(doc.state);
      documentDirty = false; $('saveIndicator').textContent = 'saved';
      render();
      addChat('pp', 'Loaded: ' + documentTitle);
    } catch (err) { addChat('pp', '⚠ ' + err.message); }
  } else if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
    // Import as reference
    try {
      const text = await file.text();
      addReference(file.name, 'research', text);
      addChat('pp', 'Added "' + file.name + '" to Reference Archive.');
    } catch (err) { addChat('pp', '⚠ ' + err.message); }
  }
});

init();
</script>

<script>
/* ══ PUBPARTNER MANUSCRIPT INTELLIGENCE ══════════════════════════
   v21. Additive layer. Every call is fire-and-forget: if
   PubPartner is unreachable, writing continues exactly as in v20.
   ═══════════════════════════════════════════════════════════════ */
const PP = {
  base: null,              // set from the PubPartner URL field
  projectId: null,
  userId: null,
  online: false,
  lastCommit: 0,
  intelligence: null,      // local cache of server-side intelligence
  inflight: false,
  pending: false,
};

/* ── identity ──────────────────────────────────────────────────────── */

function ppIdentity() {
  let uid = localStorage.getItem('2i_user_id');
  if (!uid) {
    uid = 'user_' + Math.random().toString(36).slice(2, 14);
    localStorage.setItem('2i_user_id', uid);
  }
  PP.userId = uid;

  // Project identity follows the document, not the browser session, so
  // intelligence stays attached to the manuscript across machines.
  let pid = (typeof docMeta === 'object' && docMeta && docMeta.projectId) || null;
  if (!pid) {
    pid = localStorage.getItem('2i_project_' + (docTitle || 'untitled'));
    if (!pid) {
      pid = 'proj_' + Math.random().toString(36).slice(2, 14);
      localStorage.setItem('2i_project_' + (docTitle || 'untitled'), pid);
    }
  }
  PP.projectId = pid;
  return pid;
}

function ppBase() {
  const el = document.getElementById('llmPPEndpoint');
  const raw = window.location.origin; // 2i manuscript endpoints are served by this PubCast instance
  if (/localhost:8000/.test(raw) && !/localhost|127\.0\.0\.1/.test(window.location.hostname)) return window.location.origin;
  return raw.replace(/\/+$/, '');
}

/* ── chapter segmentation ──────────────────────────────────────────── */

function ppChapters() {
  // Mirrors 2i's own chapter model: chapters[] hold startLine offsets into
  // committed[]. A manuscript with no chapter breaks is one chapter.
  const out = [];
  if (!chapters.length) {
    out.push({ index: 0, title: docTitle || 'Untitled', lines: committed.slice() });
    return out;
  }
  const sorted = chapters
    .map((c, i) => ({ ...c, _i: i }))
    .sort((a, b) => a.startLine - b.startLine);

  if (sorted[0].startLine > 0) {
    out.push({ index: 0, title: 'Opening', lines: committed.slice(0, sorted[0].startLine) });
  }
  sorted.forEach((ch, i) => {
    const start = ch.startLine;
    const end = i + 1 < sorted.length ? sorted[i + 1].startLine : committed.length;
    out.push({
      index: out.length,
      title: ch.title || ('Chapter ' + (i + 1)),
      lines: committed.slice(start, end),
    });
  });
  return out;
}

function ppCurrentChapterIndex() {
  const chs = ppChapters();
  const pos = committed.length;
  let acc = 0;
  for (let i = 0; i < chs.length; i++) {
    acc += chs[i].lines.length;
    if (pos <= acc) return i;
  }
  return Math.max(0, chs.length - 1);
}

function ppWordCount() {
  // v20 computes word count inline in render(); there is no shared helper.
  // Defining our own avoids reaching into render internals and avoids a
  // ReferenceError that the commit try/catch would silently swallow,
  // which would leave PubPartner permanently "offline" for no visible reason.
  const text = (typeof coWriting !== 'undefined' && coWriting)
    ? committed.join(' ') + ' ' + buffer.join(' ')
    : (typeof soloTextarea !== 'undefined' && soloTextarea ? soloTextarea.value : committed.join(' '));
  return text.trim().split(/\s+/).filter(Boolean).length;
}

/* ── transport ─────────────────────────────────────────────────────── */

async function ppFetch(path, options = {}, timeoutMs = 15000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(ppBase() + path, {
      ...options,
      signal: ctrl.signal,
      headers: { 'Content-Type': 'application/json', 'X-Client-Id': PP.userId || ppIdentity() && PP.userId, ...(options.headers || {}) },
    });
    if (!r.ok) throw new Error('PubPartner ' + r.status);
    return await r.json();
  } finally {
    clearTimeout(timer);
  }
}

/* ── commit ────────────────────────────────────────────────────────── */

async function ppCommit({ force = false } = {}) {
  if (!committed.length) return;

  // Coalesce: one commit in flight at a time. A second request while one
  // is running sets a flag and re-fires once, instead of queueing a burst
  // of indexing work behind a fast typist.
  if (PP.inflight) { PP.pending = true; return; }
  PP.inflight = true;

  try {
    ppIdentity();
    const res = await ppFetch('/api/pubpartner/manuscript/commit', {
      method: 'POST',
      body: JSON.stringify({
        protocol_version: 1,
        user_id: PP.userId,
        project_id: PP.projectId,
        chapters: ppChapters(),
        force_reindex: force,
        metadata: { title: docTitle || 'Untitled', words: ppWordCount() },
      }),
    }, 30000);

    PP.online = true;
    PP.lastCommit = Date.now();
    ppSetStatus(
      res.chapters_indexed.length
        ? 'indexed ch ' + res.chapters_indexed.join(', ')
        : 'up to date'
    );
    if (res.chapters_indexed.length) ppLoadIntelligence();
    if (res.errors && res.errors.length) {
      console.warn('[2i] commit reported issues:', res.errors);
    }
  } catch (e) {
    PP.online = false;
    ppSetStatus('offline');
    console.debug('[2i] commit skipped:', e.message);
  } finally {
    PP.inflight = false;
    if (PP.pending) { PP.pending = false; setTimeout(() => ppCommit(), 400); }
  }
}

/* ── intelligence ──────────────────────────────────────────────────── */

let intelligenceLastLoaded=0, intelligenceRefreshDeferred=false;
document.addEventListener('foresight:activity-change',()=>{
  if(document.documentElement.dataset.foresightActivity==='full' && intelligenceRefreshDeferred)ppLoadIntelligence();
});
async function ppLoadIntelligence() {
  const mode=document.documentElement.dataset.foresightActivity||'full';
  if(mode==='pause-optional'||(mode==='reduced'&&Date.now()-intelligenceLastLoaded<120000)) {
    intelligenceRefreshDeferred=true;
    return;
  }
  intelligenceRefreshDeferred=false;
  intelligenceLastLoaded=Date.now();
  try {
    ppIdentity();
    const res = await ppFetch(
      '/api/pubpartner/manuscript/' + encodeURIComponent(PP.projectId) + '/intelligence'
    );
    PP.intelligence = res;
    PP.online = true;
    ppRenderFlags();
    ppRenderCast();
  } catch (e) {
    PP.online = false;
    console.debug('[2i] intelligence unavailable:', e.message);
  }
}

function ppRenderFlags() {
  const host = document.getElementById('ppFlags');
  if (!host) return;
  const flags = (PP.intelligence && PP.intelligence.flags) || [];
  if (!flags.length) { host.innerHTML = ''; host.style.display = 'none'; return; }
  host.style.display = '';
  host.innerHTML = flags.slice(0, 6).map(f =>
    '<div class="pp-flag pp-' + f.severity + '">' +
      '<span class="pp-flag-msg">' + escHtml(f.message) + '</span>' +
      '<button class="pp-flag-x" title="Dismiss" ' +
              'onclick="ppResolveFlag(\'' + f.flag_id + '\')">✕</button>' +
    '</div>'
  ).join('');
}

function ppRenderCast() {
  const host = document.getElementById('ppCast');
  if (!host) return;
  const ents = (PP.intelligence && PP.intelligence.entities) || {};
  const chars = ents.character || [];
  const locs = ents.location || [];
  if (!chars.length && !locs.length) { host.innerHTML = ''; return; }

  let html = '';
  if (chars.length) {
    html += '<div class="pp-cast-head">Characters</div>';
    html += chars.slice(0, 12).map(c => {
      const aka = c.aliases && c.aliases.length
        ? ' <span class="pp-aka">(' + escHtml(c.aliases.slice(0, 2).join(', ')) + ')</span>'
        : '';
      const conf = Math.round((c.provenance.confidence || 0) * 100);
      const userSet = c.provenance.authority === 'user';
      return '<div class="pp-cast-row" title="' +
             (userSet ? 'you set this' : 'inferred, ' + conf + '% confidence') + '">' +
             '<span class="pp-dot' + (userSet ? ' pp-user' : '') + '"></span>' +
             escHtml(c.name) + aka + '</div>';
    }).join('');
  }
  if (locs.length) {
    html += '<div class="pp-cast-head">Places</div>';
    html += locs.slice(0, 8).map(l =>
      '<div class="pp-cast-row"><span class="pp-dot"></span>' + escHtml(l.name) + '</div>'
    ).join('');
  }
  host.innerHTML = html;
}

async function ppResolveFlag(flagId) {
  try {
    await ppFetch('/api/pubpartner/manuscript/' +
      encodeURIComponent(PP.projectId) + '/flags/' + encodeURIComponent(flagId) +
      '/resolve', { method: 'POST' });
    if (PP.intelligence) {
      PP.intelligence.flags = PP.intelligence.flags.filter(f => f.flag_id !== flagId);
      ppRenderFlags();
    }
  } catch (e) {
    addChat('pp', 'Could not dismiss that note: ' + e.message);
  }
}

/* ── generation ────────────────────────────────────────────────────── */

async function ppGenerate(instruction) {
  ppIdentity();
  const res = await ppFetch('/api/pubpartner/manuscript/generate', {
    method: 'POST',
    body: JSON.stringify({
      user_id: PP.userId,
      project_id: PP.projectId,
      context_lines: committed.slice(-8).concat(buffer),
      current_chapter: ppCurrentChapterIndex(),
      instruction: instruction || null,
      max_tokens: 400,
    }),
  }, 60000);
  if (!res.ok) throw new Error(res.error || 'generation returned nothing');
  return res.lines || [];
}

/* ── voice signals ─────────────────────────────────────────────────── */

function ppVoiceSignal(type, aiText, humanText) {
  if (!aiText || !aiText.trim()) return;
  ppIdentity();
  // Fire-and-forget by design. A failed signal costs one training sample;
  // a blocked UI costs the writer their momentum.
  ppFetch('/api/pubpartner/manuscript/voice-signal', {
    method: 'POST',
    body: JSON.stringify({
      user_id: PP.userId,
      project_id: PP.projectId,
      type: type,
      ai_text: aiText,
      human_text: humanText || null,
      chapter_index: ppCurrentChapterIndex(),
    }),
  }, 8000).catch(e => console.debug('[2i] voice signal dropped:', e.message));
}

/* ── status ────────────────────────────────────────────────────────── */

function ppSetStatus(text) {
  const el = document.getElementById('ppStatus');
  if (!el) return;
  el.textContent = 'PubPartner: ' + text;
  el.className = 'pp-status ' + (PP.online ? 'ok' : 'off');
}

async function ppHealthCheck() {
  try {
    ppIdentity();
    const res = await ppFetch('/api/pubpartner/manuscript/' +
      encodeURIComponent(PP.projectId) + '/health', {}, 5000);
    PP.online = true;
    ppSetStatus(res.stats.entities + ' known');
    ppLoadIntelligence();
  } catch (e) {
    PP.online = false;
    ppSetStatus('offline');
  }
}

/* ── text zoom (independent per pane) ─────────────────────────────────
   Three panes — manuscript, chat, reference — each carry their own
   zoom level. This changes font-size only, via the CSS custom
   properties declared in :root. Buttons, icons, and layout chrome
   never read these variables and never resize. Persisted across
   reloads the same way project/user identity is (localStorage).
   ────────────────────────────────────────────────────────────────── */
const ZOOM_MIN = 0.7, ZOOM_MAX = 2.0, ZOOM_STEP = 0.1;
const ZOOM_VAR = { manuscript: '--zoom-manuscript', chat: '--zoom-chat', ref: '--zoom-ref' };
const ZOOM_LABEL_ID = { manuscript: 'zoomPctManuscript', chat: 'zoomPctChat', ref: 'zoomPctRef' };
let zoomState = { manuscript: 1, chat: 1, ref: 1 };

function applyZoom(which) {
  document.documentElement.style.setProperty(ZOOM_VAR[which], zoomState[which].toFixed(2));
  const label = $(ZOOM_LABEL_ID[which]);
  if (label) label.textContent = Math.round(zoomState[which] * 100) + '%';
}

function adjustZoom(which, direction) {
  if (!ZOOM_VAR[which]) return;
  const next = Math.round((zoomState[which] + direction * ZOOM_STEP) * 100) / 100;
  zoomState[which] = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, next));
  applyZoom(which);
  try { localStorage.setItem('2i_zoom', JSON.stringify(zoomState)); }
  catch (e) { /* storage unavailable — zoom still works, just won't persist */ }
}

function loadZoom() {
  try {
    const saved = JSON.parse(localStorage.getItem('2i_zoom') || 'null');
    if (saved && typeof saved === 'object') {
      for (const key of Object.keys(zoomState)) {
        const v = saved[key];
        if (typeof v === 'number' && v >= ZOOM_MIN && v <= ZOOM_MAX) zoomState[key] = v;
      }
    }
  } catch (e) { /* corrupt or blocked storage — defaults stand */ }
  Object.keys(zoomState).forEach(applyZoom);
}
loadZoom(); // runs synchronously as soon as this second <script> block parses —
            // block 0's init() already ran by this point, but these are CSS
            // custom properties on :root, so already-rendered text picks up
            // the restored zoom immediately, before the first paint.

/* ── boot ──────────────────────────────────────────────────────────── */

window.addEventListener('load', () => {
  // Opening an ordinary file must not initiate collaboration or send its text.
  if(new URLSearchParams(location.search).has('file'))return;
  setTimeout(ppHealthCheck, 1200);
  // Periodic commit catches work that never passed through approveBuffer,
  // such as a long solo-mode session.
  setInterval(() => {
    if (committed.length && Date.now() - PP.lastCommit > 120000) ppCommit();
  }, 60000);
});

/* ── generated-line provenance ─────────────────────────────────────
   A rewrite is only a training signal if the original came from the
   model. Without this, fixing your own typo would teach the system
   that its prose was wrong. Session-scoped: an origin fact, not part
   of the manuscript.
   ────────────────────────────────────────────────────────────────── */

const PP_GEN = new Set();
function ppKey(t) { return (t || '').trim(); }
function ppMarkGenerated(t) { const k = ppKey(t); if (k) PP_GEN.add(k); }
function ppWasGenerated(t) { return PP_GEN.has(ppKey(t)); }
function ppForgetGenerated(t) { PP_GEN.delete(ppKey(t)); }

</script>
<script src="/2i-assets/reach.js"></script>
<script src="/static/foresight_files.js"></script>
<script src="/2i-assets/file-workspace.js"></script>
</body>
</html>
````

## package.json

SHA-256: `fb9e5222623f32ba49e5ec5fed348f5dd84a292761419d36b840dfb3df60d815`

````text
{
  "name": "pubcast-reach-dev-tests",
  "private": true,
  "version": "0.0.0",
  "description": "Development/test-only Node dependencies for the PubCast Reach source tree.",
  "engines": {
    "node": ">=16"
  },
  "scripts": {
    "test:editor": "node tests/test_reach_editor.cjs",
    "test:reader": "node tests/test_reader.cjs",
    "test:node": "node --test tests/test_avatar_glb_motion_consumer_node.js tests/test_program_audio_runtime_node.js tests/test_reach_editor.cjs tests/test_reader.cjs tests/test_studio_console_hotspots_node.js tests/test_voxel_block_preview_client_node.js tests/test_switcher_keyboard_node.js"
  },
  "devDependencies": {
    "jsdom": "26.1.0"
  }
}
````

## README.md

SHA-256: `03e6016dd1ab7e29422f26dedd3f30f6b40b970bde89c31cb1d2d3654a505384`

````text
# Foresight offline file and code workspace — current handoff

This is the current implementation report. Earlier same-day audits remain historical. It is an update to the existing October source, baseline 82ebf26755d3706f8d4d7d75d823bb73f4d1b07e. It is not an installation into the user's computer or a full source distribution. No remote push was made.

## Governing constraints

Essential file work is local. Google services, cloud accounts, Chromium, Playwright and the optional Node utilities are not runtime prerequisites for opening and editing text. Browser tests use Playwright as development tooling only. Files use documented formats and ordinary folders; integrations must remain replaceable. The tray hosts existing programs, including the actual 2i v22 editor.

## Working capabilities and evidence

| Capability | Current behavior |
| --- | --- |
| Text, Markdown, XML and scripts | Open in 2i, edit, native undo/copy/paste, keep original, save working copy, export and reopen |
| Save As / folders | Save to ordinary files under the user's local PubCast workspace, including nested folders, through a browser-independent local API |
| Save existing local file | Subsequent Save updates the chosen workspace file; content revisions reject conflicting replacements |
| Native manuscripts | Both normal 2i and file-mode 2i can save complete .2i manuscript state to local folders |
| Optional device picker | Save to device remains available where supported; download fallback works without that picker |
| Reopen after restart | Disk files survive router restart and are listed under Local PubCast folders in Saved files; browser working copies remain available too |
| DOCX | Local main-body/table text reading; native ZIP/XML DOCX text-copy export verified by an independent reader; no Word or Google Docs required |
| Other documents | Existing local ODT/PPTX/XLSX/PDF text extraction retained, with explicit fidelity limits; original bytes remain recoverable |
| Images | Rotate, crop, save PNG working copy, export and reopen inside 2i; original retained; cancelled crop leaves original output intact |
| Audio/media | Existing browser media playback retained; a local WAV was decoded, played muted and reopened with external requests blocked |
| Coding | Local Python syntax check without execution; explicit Run Python opens an owned local process console with stdout, stdin, traceback, exit status and Stop |
| Terminal | Existing owner-only host shell console; streamed standard input/output; process-group cleanup on disconnect and Quit |
| Account access | Reuses the local Reach authentication adapter and login/setup pages; no Google sign-in. Login and served 2i font requests no longer contact Google |
| Startup / Quit | Normal startup never installs optional Node dependencies. Explicit --install-legacy-2i is required to permit that download. Supervised authenticated Quit exits Reach and its owned consoles |

## Independence checks

- The 2i Google Fonts import and login-page Google Fonts link were removed. Local/system font fallbacks remain.
- Ordinary file-mode opening no longer initiates automatic collaboration checks or periodic manuscript submission. Explicit collaboration controls remain available.
- Browser tests abort external requests and fail if any were attempted. All tested file workflows passed that check.
- Tests disable showSaveFilePicker; local-folder Save As and later Save still write actual disk files.
- Native DOCX export was tested with the external docx writer module unavailable. The writer now uses standard-library ZIP/XML; python-docx is a development compatibility oracle only.
- Core runtime requirements do not include Playwright or Chromium. Browser binaries used for verification are not installed or launched by PubCast.
- Optional Node-service startup was tested with installer execution forbidden. Already-installed utilities remain usable; their absence does not block the native file workflow.

## Verification

- Latest functional suite: **27 passed** across workspace files, document formats, owned host controls and browser file workflows. This includes real disk persistence/restart, ownership isolation, stale-write conflicts, local syntax checking, actual Python execution/traceback, media reopening and native 2i manuscript saving, and preservation of manuscript titles and extension metadata.
- Related integration suite: **17 passed** for existing Foresight wiring, cohesive program routes, front door and real Reach startup. These are separate tests from the functional suite.
- Real launcher/HTTP audit passed: default offline-safe startup, page/assets, authentication, local disk save/readback, Python syntax API and supervised exit with code zero.
- JavaScript syntax, Python compilation, targeted Ruff checks and patch whitespace checks pass. The inherited Starlette AnyIO deprecation warning remains.
- The most recent broader Counter regression remains **87 passed, 1 failed**: unchanged physics timing measured 20.19 ms against its 16 ms budget. It was not loosened or hidden and no new physics optimization was undertaken in this pass.
- Firefox verification was attempted but did not become usable in this sandbox and was interrupted. It is not reported as passed. The passing browser tests establish behavior with the vendor-specific picker absent; a real Firefox/Windows workstation check is still required.

Functional command:
`python -m pytest -q tests/test_foresight_workspace.py tests/test_foresight_file_formats.py tests/test_foresight_host_tools.py tests/test_foresight_file_workspace.py`

Related integration command:
`python -m pytest -q tests/test_foresight_8787_wiring.py tests/test_foresight_cohesive_program.py tests/test_foresight_front_door.py tests/test_foresight_reach_runtime.py`

Launcher command: `python tools/foresight_checks/audit_launcher.py`

## Boundaries and remaining work

- Internet browsing remains the existing embedded webpage plus external-browser fallback. Sites that reject embedding still require the fallback. No compulsory Chrome/Chromium engine or unrestricted page proxy was added.
- Online Google Docs/Drive access and writeback remain optional integration work requiring runtime account authorization. Downloaded supported document files are readable locally. A .gdoc shortcut is a pointer, not its document contents.
- DOCX text copies do not preserve Word layout, images, headers, footers or footnotes. Spreadsheet formulas are text, not recalculated spreadsheets. Legacy .doc/.xls/.ppt and RTF conversion, PDF OCR/annotation and advanced media editing remain unsupported here; originals remain available.
- The shell console is useful for coding and troubleshooting but is not a full TTY emulator or breakpoint debugger. The Python runner executes only after explicit owner action; syntax checking does not execute source.
- Local folder paths are relative to each authenticated user's PubCast data workspace. This is a real disk folder on the Reach host. Arbitrary host folders can be reached through supported device-saving/downloading workflows; native OS picker permissions remain unverified on the user's machine.
- Browser recovery belongs to the browser profile; it is not account-isolated storage for a shared profile. Local disk folders are separated by authenticated identity.
- Browser recovery is not a substitute for exporting or saving important work to disk. Pending normal-2i recovery now prompts before leaving; asynchronous browser shutdown cannot be certified for every platform.
- Studio, PubPartner, PubWorld and control-room pages remain hosted by their existing routes. Physical camera/audio/GPU/model and full production workflow commissioning requires the actual workstation. Route availability does not certify those subsystems.
- The animation-viewer question and Performance/protected-background-task proposal remain deferred in PUBCAST_DEFERRED_FEATURES.md. They were not allowed to displace this work.

## Apply exactly one patch

Back up or preserve the current git state first. Use the patch matching the installed source:

1. `changes.patch`: original upstream baseline 82ebf26755d3706f8d4d7d75d823bb73f4d1b07e.
2. `changes-from-audited-update.patch`: earlier audited Counter update with the 74-test report.
3. `changes-from-file-workspace-update.patch`: immediately preceding file-workspace update with the 17-new-test report.

Run `git apply --check PATH_TO_PATCH`, then `git apply PATH_TO_PATCH`. Do not apply multiple patches. Conflicts in a newer repository must be reconciled, not overwritten. All supplied patches were actually applied to their matching snapshots and resulting changed files compared byte-for-byte.

Install runtime dependencies with `python -m pip install -r requirements.txt` during setup; normal application use does not run an installer. Launch `python run_reach.py --start-page foresight-counter`. First-run local account setup uses /login. In a blank tray choose Import, or use File > Open. Saved files includes both working copies and local folder files. Development > Host shell opens the console; Python files also expose Check Python and Run Python.

For development verification only, install requirements-dev.txt and the local browser needed by the test runner. Those tools are not runtime prerequisites.
````

## STATUS.md

SHA-256: `b942c484442014e0c0e191dfc02dd36bbec291476e5ca4134e1680971484b70e`

````text
# Build — Foresight integration status

**2026-10-22, integration checkpoint.** This is the authoritative short status for
Foresight inside this Build. It is **not** a declaration that all of PubCast is
finished. Never treat a file, route, recovered donor, or test fixture as proof
of live functionality.

## 2026-10-28: saving across PubCast (in progress)

Ledger: `handoffs/SAVING_2026-10-28.md`.

- **2i file workspace tests:** `tests/test_foresight_file_workspace.py` now runs against the real writers-room and auth routes. It was 13 failed, now 14 passed.
- **Bella Faux Pas progress** is now saved on the host per owner (`modules/studio_progress.py`, `/api/studio/progress`). It covers room, spot, who you walk as, your library avatar for each character, hologram, size tuning and cans.
  - The studio can wear avatars from the avatar library.
  - `tests/test_bella_faux_pas_progress.py` quits and restarts `run_reach.py` and checks that all of it comes back: 11 passed.
- **Counter layout** is now also kept on the host per owner (`/api/foresight/counter-layout`), and the newer copy is used on start. It comes back after a restart in a fresh browser. `tests/test_foresight_counter_layout_host.py`: 9 passed.
- **PubPartner cartridges:** File › New cartridge… makes a real cartridge (`init_cartridge`, proved with `load_cartridge`) in `data/pubpartner/cartridges/`. It becomes a friend you can talk to, and it can have an avatar from the library. The Alex vessel is untouched. `tests/test_pubpartner_cartridges.py`: 8 passed.
- **PubPartner menus were unusable:** the top bar's clip-path hid every drop-down. They now show and click; the bar's design is unchanged. `tests/test_pubpartner_menus_browser.py`: 2 passed.
- **Full suite after all of this** (Python 3.12, 120 s limit per test): 1,981 passed, 5 failed, 3 skipped. Before: 1,938 passed, 17 failed, 0 errors on 2026-10-27, and 1,798 passed, 15 failed, 2 errors on clean `022d9ec`.
  - 4 of the 5 are the known `test_foresight_airgapped_ui.py` tray-admission timeouts, the same as on clean October-24.
  - The 5th, `test_foresight_file_workspace.py::test_python_syntax_check_in_native_editor_without_external_services`, timed out in the browser during the full run. It passed three times out of three on its own. It is load-sensitive, not fixed.
- **Every save survives a restart:** `tests/test_saves_survive_restart.py` saves a 2i document, a workspace file, a PubPartner session and turn, a conversation, a chat message, an avatar, a cartridge, studio progress and the Counter layout, then quits and restarts `run_reach.py` and reads each one back: 1 passed. DMs are not covered yet.

## 2026-10-27: Bella Faux Pas Studio (walkable world) integrated

Details and ledger: `handoffs/WORLD_WALK_INTEGRATION_2026-10-27.md`. Guide: `docs/WORLD_WALK.md`.

- **The studio:** Bella Faux Pas Studio, the game section, opens from its own fan blade or File › Open…, in the dressing room. It runs at `/walk` and is live on the same PubWorld socket and hotspot backend as `/world`.
- **Canvas 2D fallback:** it was not actually wired into `foresight_counter.html`. It is now: on a WebGL2 failure the page falls back to `ForesightCanvas2D` and shows a "Graphics compatibility mode" status badge.
- **Full suite** (Python 3.12, 120 s limit per test):
  - clean `022d9ec`: 1,798 passed, 15 failed, 2 errors
  - with this change: 1,938 passed, 17 failed, 0 errors
  - The failing set is the same Foresight browser tests. 13 are in `test_foresight_file_workspace.py` and 4 in `test_foresight_airgapped_ui.py`; the two Canvas 2D tests among them used to error at setup and now reach tray admission, where they time out like the other two.
- **Launch acceptance:** `tests/test_bella_faux_pas_launch_acceptance.py` passes. It covers `run_reach.py`, login, the empty Counter, 2i, PubPartner and the studio.

## Already implemented — do not rebuild from scratch

- Foresight Counter entry point, locally hosted under `/foresight-counter`.
  `run_reach.py` now opens it by default; the original `/foresight` route and
  explicit `--start-page foresight-legacy` remain for compatibility.
- Real Counter geometry, collision physics, five-tray support, fan, locking,
  sizing, menus, persistence and per-program content-provider contract.
- A **Canvas 2D fallback** for devices where HDR/WebGL2 initialization fails:
  ordinary controls and layout remain available with a clearly labeled,
  visually simpler renderer. The original HDR renderer is unchanged.
- Same-origin Reach routes and assets for 2i, PubPartner and other program
  pages. 2i text/manuscript handling, offline local-file workspace and rich
  archive recovery exist; editing rich DOCX *inside* 2i is still unmounted.
- Authenticated supervisor-controlled Quit, saved working copies, local folder
  save/reopen, and source-original preservation.
- The verified Pete identity metadata is now packaged; do not replace the
  distinct PubPartner Alex vessel with donor bytes.

## Verified in this integration run

| Check | Result | Scope |
| --- | --- | --- |
| `pytest` application and workspace subset | 57 passed | Python, FastAPI, formats, roles, routes, local storage contracts |
| `pytest` geometry/physics subset | 35 passed | Deterministic Counter engine; not a target-hardware FPS proof |
| `pytest tests/test_foresight_airgapped_ui.py` | 4 passed | Actual menu clicks, lock/unlock, close/reopen, 2i iframe creation, snapshot restoration; GPU-stubbed for two, actual Canvas 2D fallback for two |
| `pytest tests/test_writers_room_real_http.py` | 1 passed | Real HTTP process and manuscript restart path |
| `python tools/workbench_preflight.py` | passed | Served Counter, 2i, PubPartner pages, scripts and registrations |
| `python tools/foresight_checks/audit_launcher.py` | passed | Real owner setup, anonymous denial, file write/readback, Python syntax, supervised Quit |

The commands above were run on Linux in an isolated test environment using
Python 3.13. The test files and logs are shipped; outcomes are not cumulative
proof of a full studio acceptance run.

## Unverified, and **not** claimed complete

- A clean offline Windows/PowerShell 5 installation on the owner's hardware;
  native file chooser and user permissions, WebGL performance and physical GPU.
- Real page-to-page communication and 2i input inside a Foresight iframe on an
  authenticated browser session. Sandbox browser navigation is administratively
  blocked, so the browser regressions exercised isolated DOM scripts instead.
- Live PubPartner provider/model, multi-document chat continuity, external
  recorder capture, camera/audio hardware and every hosted program's own Save.
- Full five-window GUI stress/load cycle under laptop hardware. A historical
  20.19 ms physics measurement exceeded its **16 ms** target; a passing logic
  suite does not overturn that performance issue.

## Blocked/deferred

- Rich DOCX editor engine binary bundle, HarfBuzz WASM and offline fonts are
  absent from this source checkpoint. Rich `.2i` v5 remains safely recoverable
  without claiming rich editing.
- The recovered donor `data/pubpartner/vessels/alex.pubpartner` in local donor
  ZIPs differs from the repository's authoritative Git blob
  `96fa66a728d07d5ff43b0d3d7fc17a466765cec1`. It is deliberately excluded
  from this distribution rather than impersonating the canonical vessel.
  That vessel remains in the `October` repository under `Backup-Consolidation`.
- The model named `ministral-pubcast:3b` may not exist on the user's machine;
  do not promise a live reply from PubPartner until a provider is verified.
- Automatic ChatGPT-surface capture is not established. It is not needed for
  the Foresight Counter commissioning milestone.
- Github Actions `startup_failure` with zero jobs has not been diagnosed.

## Where work goes next

1. Run `CHECK_FORESIGHT_WINDOWS.ps1` on Windows with a disposable user-data
   directory, installing declared dependencies once and caching wheels where
   possible. Collect command/output/date for every check.
2. Commission Counter in a full browser with real Reach auth. Open, move,
   resize, lock, park, close and restore five application trays. Exercise
   menu actions with mouse and keyboard, saving, denial/cancel, restart, and
   unsupported graphics fallback. Track layout jitter and dropped frames.
3. Connect the existing 2i conversation pane (without rewriting its chat
   engine), then check PubPartner model/vessel separately when authorized.
4. Check the original source and unchanged SHA manifests before promoting to
   a finished production milestone.

**No user's manuscripts, data stores, private keys, recordings or credentials
were intentionally included in this packaged source milestone.**
````

## tests/test_world_walk_host_integration.py

SHA-256: `90a076c88481ae9240ba26619dc170ae4879b76c7330c1eb50ca500344e809df`

````text
"""The walkable world (static/world_walk.html) inside the real PubCast host.

Boots the real ``main.app`` with uvicorn in a separate process against a disposable data directory, then checks:
the /walk routes; the Counter, legacy Foresight and launcher entries; and, in real Chromium, that the walker joins the
same PubWorld socket world.html uses, reports rooms by their live ids (and the host acknowledges them), moves the room
audio runtime with it, runs dressing-room hotspots through /pubworld/api/hotspot, and hops to and from the classic page.
No user data is touched. Browser checks skip when Playwright/Chromium is unavailable.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def host(tmp_path_factory):
    data = tmp_path_factory.mktemp("walk_host_data")
    port = _free_port()
    env = dict(os.environ, PUBCAST_DATA_DIR=str(data), PYTHONUNBUFFERED="1")
    env.pop("PUBCAST_ENFORCE_AUTH", None)
    log = open(data / "host.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                log.flush()
                raise AssertionError("PubCast host exited during startup:\n" + (data / "host.log").read_text(encoding="utf-8")[-4000:])
            try:
                if httpx.get(base + "/health", timeout=0.5).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.2)
        else:
            raise AssertionError("PubCast host did not come up within 90 s")
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(5)
        log.close()


# ── HTTP: the host serves the walker and everything it loads ────────────────

@pytest.fixture(scope="module")
def owner(host):
    """The first-run owner account, created through the real setup route (pages need a Reach session)."""
    import secrets
    password = secrets.token_urlsafe(24)
    r = httpx.post(host + "/api/auth/setup", json={"username": "walk-owner", "password": password, "confirm_password": password}, timeout=10)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data.get("access_token")
    return data


@pytest.mark.parametrize("route", ["/walk", "/world-walk"])
def test_the_host_serves_the_walkable_world(host, route):
    r = httpx.get(host + route, timeout=10)
    assert r.status_code == 200
    page = r.text
    assert "<title>Bella Faux Pas Studio</title>" in page
    for script in ("/static/reach_auth.js", "/static/world_walk_glb.js", "/static/world_walk_live.js"):
        assert f'src="{script}"' in page, script
        assert httpx.get(host + script, timeout=10).status_code == 200, script
    # the room audio runtime is loaded by the live link once it knows the host is there
    assert httpx.get(host + "/static/program_audio_runtime.js", timeout=10).status_code == 200
    world = httpx.get(host + "/static/world/world.json", timeout=10)
    assert world.status_code == 200 and world.json()["rooms"]
    for f in ("build/three.module.js", "examples/jsm/loaders/GLTFLoader.js", "examples/jsm/utils/SkeletonUtils.js"):
        assert httpx.get(host + "/static/vendor/three-0.160.0/" + f, timeout=10).status_code == 200, f


def test_the_walk_is_on_every_way_into_the_program():
    counter = (STATIC / "foresight_programs.js").read_text(encoding="utf-8")
    assert "{id: 'bella_faux_pas', title: 'Bella Faux Pas Studio', short: 'Studio', group: 'Programs', kind: 'page', url: '/walk'" in counter
    legacy = (STATIC / "foresight.html").read_text(encoding="utf-8")
    assert "{id:'bella_faux_pas',label:'Bella Faux Pas Studio',group:'Studio Rooms', kind:'iframe', url:'/walk'" in legacy
    assert '<a href="/walk" class="nav-pill">Bella Faux Pas</a>' in (STATIC / "launch.html").read_text(encoding="utf-8")
    classic = (STATIC / "world.html").read_text(encoding="utf-8")
    assert '<a id="walk-link" href="/walk"' in classic
    assert "a.href = '/walk?live=' + encodeURIComponent(e.detail.room)" in classic


def test_every_live_room_id_the_walker_reports_is_one_the_program_already_uses():
    """The walker reports rooms by live_id; those must be ids the classic page and the room audio runtime know."""
    import json, re
    world = json.loads((STATIC / "world" / "world.json").read_text(encoding="utf-8"))
    classic = (STATIC / "world.html").read_text(encoding="utf-8")
    classic_ids = set(re.findall(r"^  ([a-z_]+): \{$", classic[classic.index("const ROOMS = {"):classic.index("GAME STATE")], re.M))
    live = {r["live_id"] for r in world["rooms"] if r["live_id"]}
    assert live and live <= classic_ids | {"palace_theater"}, live - classic_ids
    # the dressing room is where the audio rule applies: its id must match the runtime's
    assert next(r for r in world["rooms"] if r["id"] == "dressing_room")["live_id"] == "dressing"


# ── Browser: the walker inside the real host ─────────────────────────────────

sync_api = pytest.importorskip("playwright.sync_api")

SPY = """
(() => {
  const Native = window.WebSocket;
  window.__wsSent = []; window.__wsGot = [];
  window.WebSocket = class extends Native {
    constructor(...a) {
      super(...a);
      this.addEventListener('message', e => { try { window.__wsGot.push(JSON.parse(e.data)); } catch (err) {} });
    }
    send(d) { try { window.__wsSent.push(JSON.parse(d)); } catch (err) {} return super.send(d); }
  };
})();
"""


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(args=["--no-sandbox"])
        except Exception as exc:  # no browser installed for this Playwright
            pytest.skip(f"no Chromium available: {exc}")
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    pg = browser.new_page(viewport={"width": 1400, "height": 860})
    pg.problems = []
    pg.on("pageerror", lambda e: pg.problems.append(str(e)))
    pg.add_init_script(SPY)
    yield pg
    pg.close()


@pytest.fixture()
def signed_in(page, owner):
    """A page whose Reach session is the owner's, saved the way login.html saves it (ReachAuth.saveSession)."""
    import json
    session = json.dumps({"token": owner["access_token"], "user": owner.get("username") or "walk-owner", "role": owner.get("role") or "owner"})
    page.add_init_script(f"""
      (s => {{
        if (!sessionStorage.getItem('pubcast_token')) {{
          sessionStorage.setItem('pubcast_token', s.token);
          sessionStorage.setItem('pubcast_user', JSON.stringify({{username: s.user, user_id: s.user, role: s.role}}));
        }}
      }})({session});
    """)
    return page


def _open(page, url):
    page.goto(url)
    page.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastLive", timeout=30000)


def _use_hotspot(page, hotspot_id, button):
    page.evaluate("(id) => { const W = window.PubCastWalk; W.showHotspotBubble(W.S.view.hotspots.find(h => h.id === id)); }", hotspot_id)
    page.get_by_role("button", name=button, exact=True).click()
    page.wait_for_function("() => { const b = document.getElementById('bubble'); return !b.hidden && !/Working/.test(b.textContent); }", timeout=15000)
    return page.evaluate("() => ({ title: document.querySelector('#bubble h3').textContent, body: (document.querySelector('#bubble p') || {}).textContent || '' })")


def test_the_walker_joins_the_pubworld_socket_and_the_host_acknowledges_its_rooms(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=dressing")
    assert page.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    assert page.locator("#chipLive").inner_text().endswith("Connected")
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'dressing')", timeout=10000)
    # walking through a door is a room change the host hears about, under the id the rest of PubCast uses
    page.evaluate("window.PubCastWalk.goTo('green_room', 'dressing_room')")
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'greenroom')", timeout=10000)
    sent = page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').map(m => [m.room, m.world_room])")
    assert ["greenroom", "green_room"] in sent
    assert page.problems == []


def test_the_room_audio_rule_follows_the_walker(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=greenroom")
    page.wait_for_function("window.PubCastLive.state.online === true && !!window.PubcastProgramAudio", timeout=15000)
    page.wait_for_function("window.PubcastProgramAudio.room === 'greenroom'", timeout=10000)
    page.evaluate("window.PubCastWalk.goTo('dressing_room', 'green_room')")
    page.wait_for_function("window.PubcastProgramAudio.room === 'dressing'", timeout=10000)
    assert page.evaluate("window.PubcastProgramAudio.allowed()") is False                      # only director announcements
    assert page.evaluate("window.PubcastProgramAudio.allowed({directorAnnouncement: true})") is True
    # a close-up inside the dressing room is the same room: no new room change
    before = page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').length")
    page.evaluate("window.PubCastWalk.setView('dressing_room', 'corkboard', {})")
    page.wait_for_function("window.PubCastWalk.S.view.id === 'corkboard'")
    assert page.evaluate("window.PubcastProgramAudio.room") == "dressing"
    assert page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').length") == before + 1  # view update, same room
    assert page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').pop().room") == "dressing"
    assert page.problems == []


def test_dressing_room_hotspots_run_on_the_host(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=dressing")
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    typed = _use_hotspot(page, "typewriter", "Use it here")
    assert typed["title"] == "Typewriter" and "Script draft" in typed["body"]
    page.get_by_role("button", name="My scripts", exact=True).click()
    page.wait_for_function("document.querySelector('#bubble h3').textContent === 'Scripts'", timeout=15000)
    assert "Draft" in page.evaluate("document.querySelector('#bubble p').textContent")
    worn = _use_hotspot(page, "wardrobe", "Use")
    assert worn["title"] == "Wardrobe"
    page.get_by_role("button", name="Formal Suit", exact=True).click()
    page.wait_for_function("/Wearing: Formal Suit/.test(document.querySelector('#bubble p').textContent)", timeout=15000)
    board = _use_hotspot(page, "message-board", "Use it here")      # it also opens the corkboard close-up
    assert board["title"] == "Message board" and "Stage Manager" in board["body"]
    look = _use_hotspot(page, "makeup-station", "Use it here")
    assert look["title"] == "Hair and makeup" and "Natural" in look["body"]
    # the walker sends the same hotspot call world.html makes
    calls = page.evaluate("window.__wsSent.filter(m => m.type === 'hotspot').map(m => [m.action, m.room])")
    assert ["typewriter", "dressing"] in calls and ["wardrobe", "dressing"] in calls
    assert page.problems == []


def test_sitting_and_the_tv_in_the_green_room(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=greenroom")
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    sat = _use_hotspot(page, "couch-sit-left", "Use")
    assert sat["title"] == "Take a seat" and "left curve" in sat["body"]
    tv = _use_hotspot(page, "tv", "Use")
    assert tv["title"] == "TV" and tv["body"].startswith("Channel: ")
    first = tv["body"]
    page.get_by_role("button", name="Flip channel", exact=True).click()
    page.wait_for_function("(b) => document.querySelector('#bubble p').textContent !== b", arg=first, timeout=15000)
    assert page.problems == []


def test_hotspots_the_host_has_no_action_for_stay_local(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=controlroom")
    page.evaluate("() => { const W = window.PubCastWalk; W.showHotspotBubble(W.S.view.hotspots.find(h => h.id === 'director-console')); }")
    assert page.get_by_role("button", name="Use", exact=True).count() == 0
    assert "Not wired yet" in page.locator("#bubble p").inner_text()
    assert page.problems == []


def test_classic_pubworld_and_the_walker_hop_to_each_other_at_the_same_room(host, signed_in):
    page = signed_in
    page.goto(host + "/world?room=greenroom")
    page.wait_for_function("document.getElementById('walk-link').getAttribute('href') === '/walk?live=greenroom'", timeout=15000)
    page.click("#walk-link")
    page.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastWalk", timeout=30000)
    assert page.evaluate("window.PubCastWalk.S.room.id") == "green_room"
    assert page.locator("#classicLink").get_attribute("href") == "/world?room=greenroom"
    assert page.problems == []


def test_without_the_host_behind_it_the_walker_says_so_and_keeps_walking(page, tmp_path):
    # the same page served by a plain file server: no socket, no hotspot API
    port = _free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                httpx.get(f"http://127.0.0.1:{port}/static/world_walk.html", timeout=0.3); break
            except httpx.RequestError:
                time.sleep(0.1)
        _open(page, f"http://127.0.0.1:{port}/static/world_walk.html?live=dressing")
        page.wait_for_function("window.PubCastLive.state.host === false", timeout=10000)
        assert page.evaluate("window.PubCastLive.state.online") is False
        assert page.evaluate("!window.PubcastProgramAudio")                # no host: no room-audio polling
        assert page.locator("#chipLive").inner_text().endswith("Offline")
        got = _use_hotspot(page, "wardrobe", "Use")
        assert got["title"] == "Not connected" and "Walking still works" in got["body"]
        assert page.problems == []
    finally:
        srv.terminate(); srv.wait(5)


def test_bella_faux_pas_studio_opens_from_the_foresight_counter_in_the_dressing_room(host, browser, owner):
    """The Counter is the program's front door: its menu opens the walker in a tray, live, under the same session.
    Uses a plain page (no WebSocket recorder: the Counter does not start under it)."""
    import json
    page = browser.new_page(viewport={"width": 1400, "height": 860})
    page.problems = []
    page.on("pageerror", lambda e: page.problems.append(str(e)))
    page.add_init_script("sessionStorage.setItem('pubcast_token', %s); sessionStorage.setItem('pubcast_user', JSON.stringify({username: 'walk-owner', user_id: 'walk-owner', role: 'owner'}));" % json.dumps(owner["access_token"]))
    # ?once: no continuous animation loop (software graphics here cannot keep up with it); fresh, nosave: a clean Counter
    page.goto(host + "/foresight-counter?once&fresh&nosave")
    try:
        page.wait_for_function("!!window.__programs && !!window.__counter", timeout=30000)
    except Exception:
        pytest.fail(f"the Counter did not start: now at {page.url}; page errors {page.problems}")
    # File > Open... is the Counter's way to open a program: its picker must offer the walker
    page.evaluate("window.__counter.openPicker(null)")
    entry = page.get_by_text("Bella Faux Pas Studio", exact=True)
    entry.first.wait_for(timeout=10000)
    assert entry.count() == 1
    entry.first.evaluate("el => (el.closest('button,[role=button],li') || el).click()")
    page.wait_for_function("() => [...document.querySelectorAll('iframe')].some(f => /\\/walk(\\?|$)/.test(f.getAttribute('src') || ''))", timeout=20000)
    frame = next(f for f in page.frames if "/walk" in f.url)
    frame.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastLive", timeout=30000)
    frame.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    assert frame.evaluate("window.PubCastWalk.S.view.zones.length") > 0
    assert frame.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"        # the studio starts in the dressing room
    assert frame.evaluate("window.PubCastLive.state.room") == "dressing"
    assert page.problems == []
    page.close()



def test_the_studio_starts_in_the_dressing_room_with_no_start_given(host, signed_in):
    page = signed_in
    _open(page, host + "/walk")
    assert page.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"
    assert page.evaluate("window.PubCastWalk.S.world.start") == "dressing_room"
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'dressing')", timeout=10000)
    assert page.problems == []
````
