# Validex Cinematic Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing `ArtefaktLanding` with a D2C-inspired cinematic landing page (`ValidexLanding`) built from 9 new React components, GSAP + Lenis animation, and a scoped CSS design system — without touching any existing product, API, or upload logic.

**Architecture:** Option A from the design spec. `App.jsx` gets one import change. All new landing CSS lives in `src/styles/validex-cinematic.css` scoped under `.validex-cinematic`. The existing `handleFileAccepted` flows from App → ValidexLanding → ProductDemo → UploadZone unchanged.

**Tech Stack:** React 18, Vite 5, GSAP 3, @gsap/react, Lenis, manual text splitting (no SplitText), CSS custom properties.

**Spec:** `docs/superpowers/specs/2026-05-18-validex-frontend-design.md`

---

## Pre-flight Checks

### Task 0: Verify pre-conditions

**Files:**
- Read: `frontend/src/App.jsx`
- Read: `frontend/src/components/UploadZone.jsx`
- Check: `frontend/public/assets/`

- [ ] **Step 1: Confirm App.jsx landing render**

```bash
grep -n "ArtefaktLanding\|landing" /Users/aryav/code/validex/frontend/src/App.jsx | head -10
```
Expected: lines importing and rendering `ArtefaktLanding` when `view === "landing"`.

- [ ] **Step 2: Confirm UploadZone single prop**

```bash
grep -n "onFileAccepted\|props" /Users/aryav/code/validex/frontend/src/components/UploadZone.jsx
```
Expected: only `onFileAccepted` as prop.

- [ ] **Step 3: Confirm assets missing (to be created)**

```bash
ls /Users/aryav/code/validex/frontend/public/assets 2>/dev/null || echo "MISSING — will create"
```

---

## Setup

### Task 1: Copy assets from Downloads

**Files:**
- Create: `frontend/public/assets/fonts/` (3 woff2 files)
- Create: `frontend/public/assets/images/` (16 image files)

- [ ] **Step 1: Create asset directories and copy fonts**

```bash
mkdir -p /Users/aryav/code/validex/frontend/public/assets/fonts
mkdir -p /Users/aryav/code/validex/frontend/public/assets/images
cp ~/Downloads/subset-AtiplaND-Bold.woff2 /Users/aryav/code/validex/frontend/public/assets/fonts/
cp ~/Downloads/subset-PPFraktionMono-Regular.woff2 /Users/aryav/code/validex/frontend/public/assets/fonts/
cp ~/Downloads/subset-PPFraktionMono-Bold.woff2 /Users/aryav/code/validex/frontend/public/assets/fonts/
```

- [ ] **Step 2: Copy image assets**

```bash
cd ~/Downloads && cp \
  "intro-cube@2x.png" \
  "transition-cube@2x.png" \
  "stats-cube@2x.png" \
  "pillars-cube@2x.png" \
  "secondary-transition@2x.png" \
  "helix@2x.png" \
  "helix2@2x.png" \
  "helix-pill@2x.png" \
  "stelle-risk.png" \
  "stelle-resources.png" \
  "stelle-performance.png" \
  "stelle-foundations.png" \
  "stelle-culture.png" \
  "stelle-ai.png" \
  "services-stone-1@2x.png" \
  "services-stone-2@2x.png" \
  /Users/aryav/code/validex/frontend/public/assets/images/
```

- [ ] **Step 3: Verify**

```bash
ls /Users/aryav/code/validex/frontend/public/assets/fonts/
ls /Users/aryav/code/validex/frontend/public/assets/images/ | wc -l
```
Expected: 3 font files, 16 image files.

- [ ] **Step 4: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/public/assets/
git commit -m "chore: add D2C font and image assets to public/assets"
```

---

### Task 2: Install animation packages

**Files:**
- Modify: `frontend/package.json` (via npm install)

- [ ] **Step 1: Install packages**

```bash
cd /Users/aryav/code/validex/frontend && npm install gsap @gsap/react lenis
```

- [ ] **Step 2: Verify installed**

```bash
node -e "require('gsap'); require('@gsap/react'); require('lenis'); console.log('OK')" --input-type=module 2>/dev/null || \
  cd /Users/aryav/code/validex/frontend && node -e "const g=require('./node_modules/gsap'); console.log('gsap OK')"
```

- [ ] **Step 3: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: install gsap, @gsap/react, lenis for cinematic landing"
```

---

## Core Infrastructure

### Task 3: Create text splitting utility

**Files:**
- Create: `frontend/src/utils/splitText.js`

- [ ] **Step 1: Create the utility**

Create `frontend/src/utils/splitText.js`:

```js
/**
 * Splits element text into individual character spans.
 * Returns array of span elements for GSAP targeting.
 * Spaces become non-breaking spaces to preserve layout.
 */
export function splitChars(element) {
  const text = element.textContent;
  element.textContent = '';
  const spans = [];
  for (const char of text) {
    const span = document.createElement('span');
    span.className = 'char';
    span.textContent = char === ' ' ? '\u00A0' : char;
    span.style.display = 'inline-block';
    element.appendChild(span);
    spans.push(span);
  }
  return spans;
}

/**
 * Splits element text into word spans wrapped in overflow:hidden containers.
 * Returns array of inner word spans for GSAP targeting.
 */
export function splitWords(element) {
  const text = element.textContent;
  element.textContent = '';
  const words = text.split(' ');
  const innerSpans = [];
  words.forEach((word, i) => {
    const outer = document.createElement('span');
    outer.style.display = 'inline-block';
    outer.style.overflow = 'hidden';
    outer.style.verticalAlign = 'bottom';

    const inner = document.createElement('span');
    inner.className = 'word';
    inner.textContent = word;
    inner.style.display = 'inline-block';

    outer.appendChild(inner);
    element.appendChild(outer);

    if (i < words.length - 1) {
      element.appendChild(document.createTextNode(' '));
    }
    innerSpans.push(inner);
  });
  return innerSpans;
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/utils/splitText.js
git commit -m "feat: add manual text splitting utilities (chars + words)"
```

---

### Task 4: Create validex-cinematic.css

**Files:**
- Create: `frontend/src/styles/validex-cinematic.css`

- [ ] **Step 1: Create the stylesheet**

Create `frontend/src/styles/validex-cinematic.css` with the full contents below. Font-face declarations are global (no scope). All other rules are under `.validex-cinematic`.

```css
/* ── FONTS (global — no scope) ─────────────────────────────────────────────── */
@font-face {
  font-family: 'Atipla ND';
  src: url('/assets/fonts/subset-AtiplaND-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'PP Fraktion Mono';
  src: url('/assets/fonts/subset-PPFraktionMono-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'PP Fraktion Mono';
  src: url('/assets/fonts/subset-PPFraktionMono-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

/* ── ROOT SCOPE ─────────────────────────────────────────────────────────────── */
.validex-cinematic {
  /* Color tokens */
  --v-bg:          #3d443d;
  --v-bg-mid:      #4c564c;
  --v-bg-light:    #717f71;
  --v-ceramic:     #e6f6ed;
  --v-ceramic-dim: rgba(230, 246, 237, 0.5);
  --v-ghost:       rgba(230, 246, 237, 0.1);
  --v-amber:       #f59e0b;
  --v-red:         #f87171;
  --v-cyan:        rgba(100, 220, 200, 0.6);
  --v-valid:       #a7f3d0;
  --v-partial:     #fde68a;
  --v-invalid:     #fca5a5;
  --v-muted-line:  rgba(230, 246, 237, 0.18);

  /* Grid tokens */
  --gridGap:    24px;
  --gridMargin: 40px;
  --margin-xl:  72px;
  --margin-l:   48px;
  --margin-m:   24px;
  --margin-s:   12px;

  /* Layout */
  position: relative;
  background: var(--v-bg);
  color: var(--v-ceramic);
  min-height: 100vh;
  overflow-x: hidden;
}

/* ── SMOOTH SCROLL WRAPPER ──────────────────────────────────────────────────── */
.validex-cinematic .smooth__scroll-wrapper {
  position: relative;
}

/* ── TYPOGRAPHY ─────────────────────────────────────────────────────────────── */
.validex-cinematic .type__title-main {
  font-family: 'Atipla ND', sans-serif;
  font-size: clamp(27px, 5.4rem, 54px);
  line-height: 1.04;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--v-ceramic);
}
.validex-cinematic .type__title-secondary {
  font-family: 'Atipla ND', sans-serif;
  font-size: clamp(20px, 4rem, 40px);
  line-height: 1.04;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--v-ceramic);
}
.validex-cinematic .type__body {
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(12px, 1.4rem, 14px);
  line-height: 1.4;
  font-weight: 400;
  text-transform: uppercase;
  color: var(--v-ceramic);
}
.validex-cinematic .type__hints {
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(10px, 1rem, 10px);
  line-height: 1.4;
  font-weight: 400;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--v-ceramic-dim);
}

/* ── BUTTONS ────────────────────────────────────────────────────────────────── */
.validex-cinematic .global__btn {
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(12px, 1.4rem, 14px);
  line-height: 1;
  letter-spacing: -0.04em;
  text-transform: uppercase;
  font-weight: 400;
  border: none;
  background: none;
  outline: none;
  border-radius: 4px;
  padding: 16px 24px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s ease;
}
.validex-cinematic .global__btn:hover {
  opacity: 0.85;
}
.validex-cinematic .global__btn.type--primary {
  background: var(--v-ceramic);
  color: var(--v-bg-light);
}
.validex-cinematic .global__btn.type--ghost {
  background: var(--v-ghost);
  backdrop-filter: blur(5px);
  color: var(--v-ceramic);
  border: 1px solid var(--v-ceramic);
}

/* ── GRID WRAPPER ───────────────────────────────────────────────────────────── */
.validex-cinematic .wrapper {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 0 var(--gridGap);
  margin: 0 var(--gridMargin);
}

/* ── PRELOADER ──────────────────────────────────────────────────────────────── */
.validex-cinematic .preloader {
  position: fixed;
  inset: 0;
  background: var(--v-bg-light);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: initial;
}
.validex-cinematic .preloader__ui-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}
.validex-cinematic .preloader__bar-container {
  position: relative;
  margin-top: 128px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.validex-cinematic .bar__fill,
.validex-cinematic .bar__background {
  display: flex;
  align-items: center;
  gap: 8px;
}
.validex-cinematic .bar__fill {
  --progress: 100%;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 4;
  clip-path: inset(0% var(--progress) 0% 0%);
  transition: clip-path 0.3s ease-out;
}
.validex-cinematic .bar__background {
  opacity: 0.25;
}
.validex-cinematic .bar-label {
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(10px, 1rem, 10px);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--v-ceramic);
  padding: 4px 8px;
  border: 1px solid var(--v-muted-line);
  border-radius: 2px;
}
.validex-cinematic .ui__text {
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(10px, 1rem, 10px);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--v-ceramic);
  text-align: center;
  margin-top: 24px;
}

/* ── HEADER ─────────────────────────────────────────────────────────────────── */
.validex-cinematic .header__logo {
  position: fixed;
  left: var(--gridMargin);
  top: var(--gridMargin);
  z-index: 210;
  cursor: pointer;
  text-decoration: none;
}
.validex-cinematic .header__logo .type__title-secondary {
  font-size: clamp(16px, 2rem, 20px);
}
.validex-cinematic .header__cta {
  position: fixed;
  top: var(--gridMargin);
  right: var(--gridMargin);
  z-index: 210;
}

/* ── SECTIONS BASE ──────────────────────────────────────────────────────────── */
.validex-cinematic .home__section {
  position: relative;
  padding: 120px 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* ── HERO ───────────────────────────────────────────────────────────────────── */
.validex-cinematic .section__introduction {
  background: radial-gradient(54.62% 63.28% at 50% 47.67%, #818983, #3d443d);
  overflow: hidden;
}
.validex-cinematic .introduction__hud {
  position: absolute;
  top: 50%;
  left: var(--gridMargin);
  right: var(--gridMargin);
  transform: translateY(-50%);
  letter-spacing: 0.1em;
  pointer-events: none;
}
.validex-cinematic .hud__middle {
  display: flex;
  align-items: center;
  gap: 0 24px;
  margin: 8px 0;
}
.validex-cinematic .middle__separator {
  height: 1px;
  flex: 1;
  background: linear-gradient(
    to right,
    rgba(181, 186, 182, 0.5) 0%,
    transparent 40%,
    transparent 60%,
    rgba(181, 186, 182, 0.5) 100%
  );
}
.validex-cinematic .introduction__left-block {
  grid-column: 1 / span 6;
  display: flex;
  flex-direction: column;
  gap: 32px;
  justify-content: center;
  padding-top: 80px;
}
.validex-cinematic .introduction__title-hud {
  display: flex;
  gap: 12px;
}
.validex-cinematic .introduction__actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.validex-cinematic .introduction__right-block {
  grid-column: 8 / span 5;
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: center;
  justify-content: center;
  padding-top: 80px;
}
.validex-cinematic .introduction__right-block img {
  max-width: 100%;
  height: auto;
  display: block;
  will-change: transform;
}

/* ── SCROLL TRANSITION ──────────────────────────────────────────────────────── */
.validex-cinematic .section__transition {
  min-height: 300vh;
  position: relative;
}
.validex-cinematic .section__transition .wrapper {
  position: sticky;
  top: 0;
  height: 100vh;
  align-items: center;
  justify-items: center;
}
.validex-cinematic .transition__block-container {
  --progress: 0%;
  grid-column: 1 / span 12;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  mask-image: linear-gradient(
    -90deg,
    #000 0% calc((1 - var(--progress, 0)) * 100%),
    transparent calc(1 * 100%) 100%
  );
  mask-repeat: no-repeat;
}
.validex-cinematic .transition__block {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.validex-cinematic .transition__block img {
  max-width: 500px;
  height: auto;
  display: block;
}
.validex-cinematic .transition__secondary {
  position: absolute;
  right: -80px;
  top: 40px;
  width: 200px;
  opacity: 0.6;
}
.validex-cinematic .transition__icons {
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}
.validex-cinematic .transition__fault-label {
  background: var(--v-ghost);
  backdrop-filter: blur(5px);
  border: 1px solid var(--v-muted-line);
  border-radius: 4px;
  padding: 4px 12px;
  white-space: nowrap;
  transition: opacity 0.3s ease;
}
.validex-cinematic .transition__text {
  text-align: center;
  opacity: 0.9;
}

/* ── AUDIT MODULES ──────────────────────────────────────────────────────────── */
.validex-cinematic .section__pillars {
  background: var(--v-bg-mid);
  padding: 120px 0;
}
.validex-cinematic .pillars__block {
  grid-column: 2 / span 10;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.validex-cinematic .pillars__selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.validex-cinematic .pillars__selector-item {
  padding: 24px;
  border-radius: 8px;
  border: 1px solid var(--v-muted-line);
  background: var(--v-ghost);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: default;
  transition: border-color 0.3s ease, transform 0.3s ease;
}
.validex-cinematic .pillars__selector-item:hover {
  border-color: var(--v-ceramic-dim);
  transform: translateY(-2px);
}
.validex-cinematic .pillars__selector-item .inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.validex-cinematic .pillars__selector-item img {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

/* ── WORKFLOW ───────────────────────────────────────────────────────────────── */
.validex-cinematic .section__vision {
  position: relative;
  overflow: hidden;
  padding: 120px 0;
  background: radial-gradient(59.14% 69.11% at 50% 47.67%, #7d827d 33.34%, #2a2f2a);
}
.validex-cinematic .vision__decorative-icons {
  position: absolute;
  right: -100px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  opacity: 0.15;
}
.validex-cinematic .helix-bg {
  height: 80vh;
  width: auto;
  will-change: transform;
}
.validex-cinematic .vision__block {
  grid-column: 2 / span 7;
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  z-index: 2;
}
.validex-cinematic .workflow__steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 0;
  align-items: center;
  list-style: none;
  padding: 0;
  margin: 0;
}
.validex-cinematic .workflow__step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.validex-cinematic .step__label {
  background: var(--v-ghost);
  border: 1px solid var(--v-muted-line);
  border-radius: 4px;
  padding: 8px 16px;
  white-space: nowrap;
  font-family: 'PP Fraktion Mono', monospace;
  font-size: clamp(11px, 1.2rem, 12px);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--v-ceramic);
}
.validex-cinematic .step__arrow {
  color: var(--v-ceramic-dim);
  font-size: 1.2em;
  margin: 0 4px;
}

/* ── PRODUCT DEMO ───────────────────────────────────────────────────────────── */
.validex-cinematic .section__service {
  padding: 120px 0;
  background: var(--v-bg);
}
.validex-cinematic .service__block {
  grid-column: 2 / span 10;
  display: flex;
  flex-direction: column;
  gap: 48px;
}
.validex-cinematic .demo__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}
.validex-cinematic .demo__upload-panel {
  border: 1px solid var(--v-muted-line);
  border-radius: 12px;
  overflow: hidden;
  background: var(--v-ghost);
}
.validex-cinematic .demo__audit-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px;
  border: 1px solid var(--v-muted-line);
  border-radius: 12px;
  background: var(--v-ghost);
}
.validex-cinematic .audit__score-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--v-muted-line);
}
.validex-cinematic .audit__score-number {
  font-size: clamp(32px, 4rem, 48px);
}
.validex-cinematic .audit__flags {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.validex-cinematic .flag {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 6px;
  border: 1px solid var(--v-muted-line);
}
.validex-cinematic .flag[data-status="valid"] {
  border-left: 3px solid var(--v-valid);
}
.validex-cinematic .flag[data-status="invalid"] {
  border-left: 3px solid var(--v-invalid);
}
.validex-cinematic .flag[data-status="partial"] {
  border-left: 3px solid var(--v-partial);
}
.validex-cinematic .flag__note[data-status="valid"],
.validex-cinematic .flag[data-status="valid"] .flag__note {
  color: var(--v-valid);
}
.validex-cinematic .flag[data-status="invalid"] .flag__note {
  color: var(--v-invalid);
}
.validex-cinematic .flag[data-status="partial"] .flag__note {
  color: var(--v-partial);
}
.validex-cinematic .audit__recommendation {
  padding: 16px;
  border: 1px solid var(--v-muted-line);
  border-radius: 6px;
  background: rgba(230, 246, 237, 0.05);
  font-style: italic;
}
.validex-cinematic .service__cta {
  display: flex;
  justify-content: flex-start;
}

/* ── FINAL CTA ──────────────────────────────────────────────────────────────── */
.validex-cinematic .section__primary-transition {
  min-height: 100vh;
  display: flex;
  align-items: center;
}
.validex-cinematic .section__primary-transition .section__background {
  width: 100%;
  padding: 120px 0;
  background: radial-gradient(54.62% 63.28% at 50% 47.67%, #818983, #3d443d),
              radial-gradient(59.14% 69.11% at 50% 47.67%, #7d827d 33.34%, #2a2f2a);
}
.validex-cinematic .title__block {
  grid-column: 3 / span 8;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 48px;
}
.validex-cinematic .title__block img {
  max-width: 300px;
  height: auto;
  will-change: transform;
}

/* ── MOBILE ─────────────────────────────────────────────────────────────────── */
@media (max-width: 1000px) {
  .validex-cinematic {
    --gridMargin: 16px;
    --gridGap: 16px;
  }

  .validex-cinematic .header__logo,
  .validex-cinematic .header__cta {
    top: 16px;
  }
  .validex-cinematic .header__logo { left: 16px; }
  .validex-cinematic .header__cta  { right: 16px; }

  .validex-cinematic .home__section {
    padding: 100px 0 60px;
    min-height: auto;
  }

  .validex-cinematic .introduction__left-block {
    grid-column: 1 / span 12;
    padding-top: 40px;
  }
  .validex-cinematic .introduction__right-block {
    grid-column: 1 / span 12;
    order: -1;
    padding-top: 0;
  }
  .validex-cinematic .introduction__right-block img {
    max-width: 260px;
    margin: 0 auto;
  }
  .validex-cinematic .introduction__actions {
    flex-direction: column;
  }
  .validex-cinematic .introduction__actions .global__btn {
    width: 100%;
    text-align: center;
  }

  .validex-cinematic .section__transition {
    min-height: 100vh;
  }
  .validex-cinematic .transition__block img {
    max-width: 280px;
  }
  .validex-cinematic .transition__secondary {
    display: none;
  }

  .validex-cinematic .pillars__block {
    grid-column: 1 / span 12;
  }
  .validex-cinematic .pillars__selector {
    grid-template-columns: repeat(2, 1fr);
  }

  .validex-cinematic .vision__block {
    grid-column: 1 / span 12;
  }
  .validex-cinematic .vision__decorative-icons {
    display: none;
  }
  .validex-cinematic .workflow__steps {
    flex-direction: column;
    align-items: flex-start;
  }
  .validex-cinematic .step__arrow {
    transform: rotate(90deg);
    display: block;
  }

  .validex-cinematic .service__block {
    grid-column: 1 / span 12;
  }
  .validex-cinematic .demo__grid {
    grid-template-columns: 1fr;
  }

  .validex-cinematic .title__block {
    grid-column: 1 / span 12;
    padding: 0 var(--gridMargin);
  }
}

/* ── REDUCED MOTION ─────────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .validex-cinematic *,
  .validex-cinematic *::before,
  .validex-cinematic *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/styles/validex-cinematic.css
git commit -m "feat: add validex-cinematic.css design system (D2C-inspired)"
```

---

## Components

### Task 5: SmoothScroll.jsx

**Files:**
- Create: `frontend/src/components/SmoothScroll.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import Lenis from 'lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function SmoothScroll({ children }) {
  const wrapperRef = useRef(null);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const lenis = new Lenis({
      duration: 1.6,
      easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      direction: 'vertical',
      gestureDirection: 'vertical',
      smooth: true,
      smoothTouch: false,
      touchMultiplier: 2,
    });

    window.__lenis = lenis;

    const onScroll = () => ScrollTrigger.update();
    lenis.on('scroll', onScroll);

    const tickerFn = time => lenis.raf(time * 1000);
    gsap.ticker.add(tickerFn);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tickerFn);
      lenis.off('scroll', onScroll);
      lenis.destroy();
      delete window.__lenis;
    };
  }, []);

  return (
    <div className="smooth__scroll-wrapper" ref={wrapperRef}>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/SmoothScroll.jsx
git commit -m "feat: add SmoothScroll component (Lenis + GSAP ticker)"
```

---

### Task 6: Preloader.jsx

**Files:**
- Create: `frontend/src/components/Preloader.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { splitChars } from '../utils/splitText';

const BAR_LABELS = ['P', 'Q', 'FC', 'QC', 'META', 'SCORE'];
const PRELOADER_TEXT = 'Initializing audit engine';

export default function Preloader() {
  const rootRef = useRef(null);
  const fillRef = useRef(null);
  const textRef = useRef(null);
  const intervalRef = useRef(null);
  const charsRef = useRef([]);

  const exit = () => {
    clearInterval(intervalRef.current);
    const tl = gsap.timeline();
    if (charsRef.current.length) {
      tl.to(charsRef.current, {
        opacity: 0,
        duration: 0.3,
        ease: 'power2.out',
        stagger: { each: 0.01, from: 'random' },
      }, 0.4);
    }
    tl.to('.validex-cinematic .bar__fill .bar-label', {
      autoAlpha: 0,
      duration: 0.6,
      ease: 'power2.out',
      stagger: { each: 0.05, from: 'random' },
    }, 0);
    tl.to('.validex-cinematic .bar__background .bar-label', {
      autoAlpha: 0,
      duration: 0.6,
      ease: 'power2.out',
      stagger: { each: 0.05, from: 'random' },
    }, 0);
    tl.to(rootRef.current, {
      autoAlpha: 0,
      duration: 1,
      ease: 'power2.out',
      pointerEvents: 'none',
    }, 0.7);
    tl.add(() => {
      window.dispatchEvent(new CustomEvent('preloader:done'));
    }, 1.4);
  };

  const simulateProgress = () => {
    let progress = 0;
    intervalRef.current = setInterval(() => {
      progress += Math.random() * 8 + 3;
      if (progress >= 85) {
        progress = 85;
        clearInterval(intervalRef.current);
        fillRef.current?.style.setProperty('--progress', '15%');
        setTimeout(() => {
          fillRef.current?.style.setProperty('--progress', '0%');
          setTimeout(exit, 300);
        }, 400);
        return;
      }
      const cssProgress = 100 - progress;
      fillRef.current?.style.setProperty('--progress', `${cssProgress}%`);
    }, 120);
  };

  useEffect(() => {
    if (textRef.current) {
      charsRef.current = splitChars(textRef.current);
    }

    const isMobile = window.innerWidth <= 1000;
    if (isMobile) {
      setTimeout(exit, 400);
    } else {
      simulateProgress();
    }

    return () => {
      clearInterval(intervalRef.current);
      if (textRef.current) {
        textRef.current.textContent = PRELOADER_TEXT;
      }
    };
  }, []);

  return (
    <div className="preloader" ref={rootRef}>
      <div className="preloader__ui-container">
        <div className="preloader__bar-container">
          <div className="bar__fill" ref={fillRef}>
            {BAR_LABELS.map(label => (
              <span key={label} className="bar-label">{label}</span>
            ))}
          </div>
          <div className="bar__background">
            {BAR_LABELS.map(label => (
              <span key={label} className="bar-label">{label}</span>
            ))}
          </div>
        </div>
        <div className="ui__text" ref={textRef}>
          {PRELOADER_TEXT}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/Preloader.jsx
git commit -m "feat: add cinematic Preloader with audit-themed progress bar"
```

---

### Task 7: Header.jsx

**Files:**
- Create: `frontend/src/components/Header.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function Header({ onLaunch }) {
  const logoRef = useRef(null);
  const ctaRef = useRef(null);

  useEffect(() => {
    gsap.set([logoRef.current, ctaRef.current], { autoAlpha: 0 });

    const handleDone = () => {
      gsap.to([logoRef.current, ctaRef.current], {
        autoAlpha: 1,
        duration: 0.8,
        ease: 'power2.out',
        stagger: 0.1,
      });
    };

    window.addEventListener('preloader:done', handleDone);
    return () => window.removeEventListener('preloader:done', handleDone);
  }, []);

  return (
    <>
      <div className="header__logo" ref={logoRef}>
        <span className="type__title-secondary">VALIDEX</span>
      </div>
      <div className="header__cta" ref={ctaRef}>
        <button className="global__btn type--ghost" onClick={onLaunch}>
          RUN AUDIT →
        </button>
      </div>
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/Header.jsx
git commit -m "feat: add fixed Header with logo and Run Audit CTA"
```

---

### Task 8: HeroSection.jsx

**Files:**
- Create: `frontend/src/components/HeroSection.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { splitWords } from '../utils/splitText';

export default function HeroSection({ onLaunch }) {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const titleRef = useRef(null);
  const floatAnimRef = useRef(null);

  const scrollTo = id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (window.__lenis) {
      window.__lenis.scrollTo(el, { offset: -80, duration: 1.6 });
    } else {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    gsap.set(sectionRef.current, { autoAlpha: 0 });

    const handleDone = () => {
      gsap.to(sectionRef.current, { autoAlpha: 1, duration: 0.6, ease: 'power2.out' });

      if (!reduced && titleRef.current) {
        const words = splitWords(titleRef.current);
        gsap.from(words, {
          y: 30,
          opacity: 0,
          duration: 0.8,
          stagger: 0.05,
          ease: 'power3.out',
          delay: 0.2,
        });
      }

      if (!reduced && cubeRef.current) {
        floatAnimRef.current = gsap.to(cubeRef.current, {
          y: -12,
          rotation: 2,
          duration: 3,
          ease: 'sine.inOut',
          yoyo: true,
          repeat: -1,
        });
      }
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      if (floatAnimRef.current) floatAnimRef.current.kill();
    };
  }, []);

  return (
    <section className="home__section section__introduction" ref={sectionRef} id="hero">
      <div className="introduction__hud">
        <div className="hud__top">
          <span className="type__hints">VALIDEX AUDIT ENGINE</span>
        </div>
        <div className="hud__middle">
          <div className="middle__separator" />
          <div className="middle__scroll-indicator">
            <span className="type__hints">SCROLL TO EXPLORE</span>
          </div>
        </div>
      </div>
      <div className="wrapper">
        <div className="introduction__left-block">
          <div className="introduction__title-hud">
            <span className="type__hints">METABOLOMICS VALIDATOR</span>
          </div>
          <h1 className="type__title-main" ref={titleRef}>
            VALIDATE METABOLOMICS RESULTS BEFORE INTERPRETATION
          </h1>
          <div className="introduction__actions">
            <button className="global__btn type--primary" onClick={() => scrollTo('product-demo')}>
              RUN SAMPLE AUDIT
            </button>
            <button className="global__btn type--ghost" onClick={() => scrollTo('workflow')}>
              VIEW WORKFLOW
            </button>
          </div>
        </div>
        <div className="introduction__right-block">
          <img
            ref={cubeRef}
            src="/assets/images/intro-cube@2x.png"
            alt="Validation Matrix"
            loading="lazy"
          />
          <p className="type__body">
            Validex audits result tables for statistical gaps, missing corrections,
            unclear effect sizes, and reproducibility risk.
          </p>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/HeroSection.jsx
git commit -m "feat: add HeroSection with floating cube and word-reveal headline"
```

---

### Task 9: ScrollTransition.jsx

**Files:**
- Create: `frontend/src/components/ScrollTransition.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const FAULT_LABELS = [
  'MISSING FDR',
  'UNCLEAR EFFECT SIZE',
  'INVALID P-VALUE RANGE',
  'METADATA GAP',
];
const LABEL_THRESHOLDS = [0.30, 0.50, 0.65, 0.80];

export default function ScrollTransition() {
  const sectionRef = useRef(null);
  const containerRef = useRef(null);
  const labelsRef = useRef([]);
  const triggersRef = useRef([]);

  const isStaticMode =
    typeof window !== 'undefined' &&
    (window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      window.innerWidth < 1000);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = window.innerWidth < 1000;

    if (reduced || mobile) return;

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1,
        onUpdate: self => {
          const p = self.progress;
          containerRef.current?.style.setProperty('--progress', `${(1 - p) * 100}%`);
          labelsRef.current.forEach((label, i) => {
            if (label) {
              gsap.set(label, { opacity: p >= LABEL_THRESHOLDS[i] ? 1 : 0 });
            }
          });
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
    };
  }, []);

  return (
    <section className="home__section section__transition" ref={sectionRef} id="scroll-transition">
      <div className="wrapper">
        <div
          className="transition__block-container"
          ref={containerRef}
          style={{ '--progress': isStaticMode ? '0%' : '100%' }}
        >
          <div className="transition__block">
            <img
              src="/assets/images/transition-cube@2x.png"
              alt="Validation matrix fragmenting"
              loading="lazy"
            />
            <img
              src="/assets/images/secondary-transition@2x.png"
              alt=""
              className="transition__secondary"
              loading="lazy"
            />
            <div className="transition__icons">
              {FAULT_LABELS.map((label, i) => (
                <span
                  key={label}
                  className="transition__fault-label type__hints"
                  ref={el => { labelsRef.current[i] = el; }}
                  style={{ opacity: isStaticMode ? 1 : 0 }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
          <div className="transition__text type__title-secondary">
            DETECTED. SCORED. EXPLAINED.
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/ScrollTransition.jsx
git commit -m "feat: add ScrollTransition with scrubbed cube reveal and fault labels"
```

---

### Task 10: AuditModules.jsx

**Files:**
- Create: `frontend/src/components/AuditModules.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const MODULES = [
  { image: '/assets/images/stelle-risk.png',         label: 'REPRODUCIBILITY RISK',     key: 'risk' },
  { image: '/assets/images/stelle-resources.png',    label: 'METADATA COMPLETENESS',    key: 'resources' },
  { image: '/assets/images/stelle-performance.png',  label: 'EFFECT SIZE ROBUSTNESS',   key: 'performance' },
  { image: '/assets/images/stelle-foundations.png',  label: 'QC FOUNDATION',            key: 'foundations' },
  { image: '/assets/images/stelle-ai.png',           label: 'STATISTICAL INFERENCE',    key: 'ai' },
  { image: '/assets/images/stelle-culture.png',      label: 'EXPERIMENTAL CONSISTENCY', key: 'culture' },
];

export default function AuditModules() {
  const sectionRef = useRef(null);
  const cardsRef = useRef([]);
  const triggersRef = useRef([]);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    gsap.set(cardsRef.current, { opacity: 0, y: 40 });

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 75%',
        once: true,
        onEnter: () => {
          gsap.to(cardsRef.current, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.08,
            ease: 'power3.out',
          });
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
    };
  }, []);

  return (
    <section className="section__pillars" ref={sectionRef} id="audit-modules">
      <div className="wrapper">
        <div className="pillars__block">
          <p className="type__hints">AUDIT LAYERS</p>
          <h2 className="type__title-secondary">THE VALIDATION MATRIX</h2>
          <div className="pillars__selector">
            {MODULES.map((mod, i) => (
              <div
                key={mod.key}
                className="pillars__selector-item"
                ref={el => { cardsRef.current[i] = el; }}
              >
                <div className="inner">
                  <img src={mod.image} alt={mod.label} loading="lazy" />
                  <span className="type__hints">{mod.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/AuditModules.jsx
git commit -m "feat: add AuditModules grid with staggered scroll reveal"
```

---

### Task 11: WorkflowSection.jsx

**Files:**
- Create: `frontend/src/components/WorkflowSection.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const STEPS = [
  'RAW RESULTS',
  'STATISTICAL TABLE',
  'VALIDEX AUDIT',
  'FLAGGED ISSUES',
  'VALIDITY REPORT',
];

export default function WorkflowSection() {
  const sectionRef = useRef(null);
  const helixRef = useRef(null);
  const stepsRef = useRef([]);
  const triggersRef = useRef([]);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = window.innerWidth < 1000;
    if (reduced) return;

    gsap.set(stepsRef.current, { opacity: 0, x: -20 });

    const handleDone = () => {
      if (!mobile && helixRef.current) {
        const t1 = ScrollTrigger.create({
          trigger: sectionRef.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 0.5,
          onUpdate: self => {
            gsap.set(helixRef.current, { y: -60 + self.progress * 120 });
          },
        });
        triggersRef.current.push(t1);
      }

      const t2 = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 65%',
        once: true,
        onEnter: () => {
          gsap.to(stepsRef.current, {
            opacity: 1,
            x: 0,
            duration: 0.7,
            stagger: 0.1,
            ease: 'power3.out',
          });
        },
      });
      triggersRef.current.push(t2);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
    };
  }, []);

  return (
    <section className="section__vision" ref={sectionRef} id="workflow">
      <div className="vision__decorative-icons">
        <img
          ref={helixRef}
          src="/assets/images/helix@2x.png"
          alt=""
          className="helix-bg"
          loading="lazy"
        />
      </div>
      <div className="wrapper">
        <div className="vision__block">
          <p className="type__hints">AUDIT PIPELINE</p>
          <h2 className="type__title-secondary">FROM RAW DATA TO VALIDITY REPORT</h2>
          <ol className="workflow__steps">
            {STEPS.map((step, i) => (
              <li
                key={step}
                className="workflow__step"
                ref={el => { stepsRef.current[i] = el; }}
              >
                <span className="step__label type__body">{step}</span>
                {i < STEPS.length - 1 && (
                  <span className="step__arrow" aria-hidden="true">→</span>
                )}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/WorkflowSection.jsx
git commit -m "feat: add WorkflowSection with helix parallax and step reveals"
```

---

### Task 12: ProductDemo.jsx

**Files:**
- Create: `frontend/src/components/ProductDemo.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import UploadZone from './UploadZone';

const FLAGS = [
  { label: 'MISSING FDR CORRECTION', status: 'invalid', note: 'HIGH PRIORITY' },
  { label: 'FOLD CHANGE DETECTED',   status: 'valid',   note: 'PASS' },
  { label: 'P-VALUE RANGE VALID',    status: 'valid',   note: 'PASS' },
  { label: 'METADATA COMPLETENESS',  status: 'partial', note: 'PARTIAL' },
];

export default function ProductDemo({ onLaunch, onFileAccepted }) {
  const sectionRef = useRef(null);
  const triggersRef = useRef([]);

  const safeFileAccepted = typeof onFileAccepted === 'function' ? onFileAccepted : () => {};

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    gsap.set(sectionRef.current, { opacity: 0, y: 30 });

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 60%',
        once: true,
        onEnter: () => {
          gsap.to(sectionRef.current, {
            opacity: 1,
            y: 0,
            duration: 0.9,
            ease: 'power3.out',
          });
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
    };
  }, []);

  return (
    <section className="section__service service--demo" ref={sectionRef} id="product-demo">
      <div className="wrapper">
        <div className="service__block">
          <p className="type__hints">TRY IT NOW</p>
          <h2 className="type__title-secondary">UPLOAD YOUR RESULTS</h2>
          <div className="demo__grid">
            <div className="demo__upload-panel">
              <UploadZone onFileAccepted={safeFileAccepted} />
            </div>
            <div className="demo__audit-panel">
              <div className="audit__score-bar">
                <span className="type__hints">VALIDITY SCORE</span>
                <span className="type__title-secondary audit__score-number">82 / 100</span>
              </div>
              <div className="audit__flags">
                {FLAGS.map(flag => (
                  <div key={flag.label} className="flag" data-status={flag.status}>
                    <span className="flag__label type__body">{flag.label}</span>
                    <span className="flag__note type__hints">{flag.note}</span>
                  </div>
                ))}
              </div>
              <div className="audit__recommendation type__body">
                Add q-values before confirmatory interpretation
              </div>
            </div>
          </div>
          <div className="service__cta">
            <button className="global__btn type--ghost" onClick={onLaunch}>
              UPLOAD YOUR DATA
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/ProductDemo.jsx
git commit -m "feat: add ProductDemo with live UploadZone and static audit panel"
```

---

### Task 13: FinalCTA.jsx

**Files:**
- Create: `frontend/src/components/FinalCTA.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { splitWords } from '../utils/splitText';

export default function FinalCTA({ onLaunch }) {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const btnRef = useRef(null);
  const titleRef = useRef(null);
  const triggersRef = useRef([]);
  const loopsRef = useRef([]);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!reduced) {
      gsap.set(cubeRef.current, { opacity: 0, scale: 0.8 });
    }

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 70%',
        once: true,
        onEnter: () => {
          if (reduced) return;

          gsap.to(cubeRef.current, {
            opacity: 1, scale: 1, duration: 1, ease: 'power3.out',
          });

          const floatLoop = gsap.to(cubeRef.current, {
            y: -8,
            duration: 4,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1,
            delay: 1,
          });
          loopsRef.current.push(floatLoop);

          if (titleRef.current) {
            const words = splitWords(titleRef.current);
            gsap.from(words, {
              y: 20,
              opacity: 0,
              duration: 0.7,
              stagger: 0.04,
              ease: 'power3.out',
              delay: 0.3,
            });
          }

          const pulseLoop = gsap.to(btnRef.current, {
            scale: 1.02,
            duration: 1.5,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1,
            delay: 1.2,
          });
          loopsRef.current.push(pulseLoop);
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
      loopsRef.current.forEach(l => l.kill());
    };
  }, []);

  return (
    <section className="section__primary-transition" ref={sectionRef} id="final-cta">
      <div className="section__background">
        <div className="wrapper">
          <div className="title__block">
            <img
              ref={cubeRef}
              src="/assets/images/stats-cube@2x.png"
              alt="Validation complete"
              loading="lazy"
            />
            <h2 className="type__title-main" ref={titleRef}>
              TURN STATISTICAL UNCERTAINTY INTO AN AUDIT TRAIL
            </h2>
            <button ref={btnRef} className="global__btn type--primary" onClick={onLaunch}>
              LAUNCH VALIDEX
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/FinalCTA.jsx
git commit -m "feat: add FinalCTA with scroll-triggered cube and pulsing button"
```

---

### Task 14: ValidexLanding.jsx

**Files:**
- Create: `frontend/src/components/ValidexLanding.jsx`

- [ ] **Step 1: Create component**

```jsx
import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import '../styles/validex-cinematic.css';
import Preloader from './Preloader';
import SmoothScroll from './SmoothScroll';
import Header from './Header';
import HeroSection from './HeroSection';
import ScrollTransition from './ScrollTransition';
import AuditModules from './AuditModules';
import WorkflowSection from './WorkflowSection';
import ProductDemo from './ProductDemo';
import FinalCTA from './FinalCTA';

gsap.registerPlugin(ScrollTrigger);

export default function ValidexLanding({ onLaunch, onFileAccepted }) {
  const landingRef = useRef(null);

  useEffect(() => {
    const handleDone = () => {
      ScrollTrigger.refresh();
    };
    window.addEventListener('preloader:done', handleDone);

    return () => {
      window.removeEventListener('preloader:done', handleDone);
      // Kill only triggers whose trigger element is inside this landing
      ScrollTrigger.getAll().forEach(t => {
        if (t.trigger && landingRef.current?.contains(t.trigger)) {
          t.kill();
        }
      });
    };
  }, []);

  return (
    <div className="validex-cinematic" ref={landingRef}>
      <Preloader />
      <SmoothScroll>
        <Header onLaunch={onLaunch} />
        <HeroSection onLaunch={onLaunch} />
        <ScrollTransition />
        <AuditModules />
        <WorkflowSection />
        <ProductDemo onLaunch={onLaunch} onFileAccepted={onFileAccepted} />
        <FinalCTA onLaunch={onLaunch} />
      </SmoothScroll>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/components/ValidexLanding.jsx
git commit -m "feat: add ValidexLanding root component composing all cinematic sections"
```

---

## Integration

### Task 15: Update App.jsx

**Files:**
- Modify: `frontend/src/App.jsx` — 2 lines only (import + render)

- [ ] **Step 1: Replace ArtefaktLanding import**

In `frontend/src/App.jsx`, find:
```js
import ArtefaktLanding from "./components/ArtefaktLanding";
```
Replace with:
```js
import ValidexLanding from "./components/ValidexLanding";
```

- [ ] **Step 2: Replace landing render**

In `frontend/src/App.jsx`, find (inside the `view === "landing"` block):
```jsx
<ArtefaktLanding onLaunch={() => setView("upload")} onDemo={handleDemo} />
```
Replace with:
```jsx
<ValidexLanding
  onLaunch={() => setView("upload")}
  onFileAccepted={handleFileAccepted}
/>
```

- [ ] **Step 3: Verify no other changes made**

```bash
git diff frontend/src/App.jsx | grep "^[+-]" | grep -v "^---\|^+++" | head -20
```
Expected: only the 2 import lines and 3 render lines changed.

- [ ] **Step 4: Commit**

```bash
cd /Users/aryav/code/validex
git add frontend/src/App.jsx
git commit -m "feat: wire ValidexLanding into App.jsx as the new landing page"
```

---

## Build & Fix

### Task 16: Build and verify

**Files:** N/A — verification only

- [ ] **Step 1: Run build**

```bash
cd /Users/aryav/code/validex/frontend && npm run build 2>&1 | tail -40
```
Expected: build completes with no errors. If errors appear, proceed to Step 2.

- [ ] **Step 2: Fix common build errors**

Common issues and fixes:
- `Cannot find module 'lenis'` → `npm install lenis` (ensure package installed)
- `Cannot find module '../utils/splitText'` → verify file exists at `frontend/src/utils/splitText.js`
- `Cannot find module '../styles/validex-cinematic.css'` → verify file exists at `frontend/src/styles/validex-cinematic.css`
- Missing image in public → re-run asset copy from Task 1
- GSAP ScrollTrigger not registered → confirm `gsap.registerPlugin(ScrollTrigger)` in `ValidexLanding.jsx`

- [ ] **Step 3: Re-run build after fixes**

```bash
cd /Users/aryav/code/validex/frontend && npm run build 2>&1 | tail -20
```
Expected: `✓ built in X.XXs` with no errors.

- [ ] **Step 4: Commit build artifacts if needed, otherwise commit fix**

```bash
cd /Users/aryav/code/validex
git add -A frontend/src/
git commit -m "fix: resolve build errors in cinematic landing implementation"
```

---

## Self-Review

### Spec Coverage Check

| Spec Section | Task |
|---|---|
| Fonts + assets copied | Task 1 |
| Packages installed | Task 2 |
| splitChars / splitWords utilities | Task 3 |
| CSS design tokens + typography | Task 4 |
| SmoothScroll (Lenis + GSAP ticker) | Task 5 |
| Preloader (clip-path bar, exit event) | Task 6 |
| Header (fixed, fades after preloader) | Task 7 |
| Hero (cube float, word reveal, scroll CTA) | Task 8 |
| ScrollTransition (scrub, fault labels) | Task 9 |
| AuditModules (stagger reveal) | Task 10 |
| WorkflowSection (helix parallax, steps) | Task 11 |
| ProductDemo (real UploadZone, static panel) | Task 12 |
| FinalCTA (cube enter, pulse loop) | Task 13 |
| ValidexLanding (root compose + cleanup) | Task 14 |
| App.jsx (2-line change) | Task 15 |
| Build verification | Task 16 |
| prefers-reduced-motion | CSS Task 4 + each component |
| Mobile layout | CSS Task 4 media queries |
| ScrollTrigger.refresh() after preloader | Task 14 |
| Loops killed on unmount | Tasks 8, 13 |
| Triggers scoped to landing | Task 14 |
| UploadZone unchanged | Task 12 (read-only) |
| index.css unchanged | Never touched |
