# Validex Cinematic Frontend — Design Spec
**Date:** 2026-05-18  
**Status:** Approved  
**Scope:** Replace the existing landing page (`ArtefaktLanding`) with a premium cinematic frontend modeled on the D2C Life Science visual system. All backend, API, upload, context form, and audit result logic is preserved untouched.

---

## 1. Project Context

**Stack:** React 18 + Vite 5, FastAPI backend  
**Package manager:** npm  
**Existing product flow:** `App.jsx` manages `view` state (`landing` | `upload` | `context` | `running` | `results`). The landing renders when `view === "landing"`. All state and API calls live in `App.jsx` and are not modified.

**What changes:**
- `ArtefaktLanding` → replaced by `ValidexLanding`
- `frontend/src/App.jsx` — one line changed: import + render `ValidexLanding` instead of `ArtefaktLanding`, passing `onLaunch` and `onFileAccepted`
- New file: `frontend/src/styles/validex-cinematic.css`
- New folder: `frontend/public/assets/fonts/` and `frontend/public/assets/images/`
- New components: 9 files under `frontend/src/components/`

**What does not change:**
- `frontend/src/index.css`
- `UploadZone.jsx`, `ContextForm.jsx`, `AuditResults.jsx`, `DataPreview.jsx`
- All backend logic, API routes, state management in `App.jsx`
- All existing UI component styles

---

## 2. Visual System

### Color Tokens
All scoped under `.validex-cinematic` except font-face declarations which are global.

```css
--v-bg:          #3d443d;              /* dark sage — page background */
--v-bg-mid:      #4c564c;              /* mid sage — section overlays */
--v-bg-light:    #717f71;              /* light sage — preloader, cards */
--v-ceramic:     #e6f6ed;              /* off-white — all text and objects */
--v-ceramic-dim: #e6f6ed80;            /* 50% — secondary text */
--v-ghost:       #e6f6ed1a;            /* ghost UI — button fills, HUD */
--v-amber:       #f59e0b;              /* warnings only */
--v-red:         #f87171;              /* errors/high-priority flags */
--v-cyan:        rgba(100,220,200,0.6);/* data lines only */
--v-valid:       #a7f3d0;              /* audit pass */
--v-partial:     #fde68a;              /* audit partial */
--v-invalid:     #fca5a5;              /* audit fail */
--v-muted-line:  rgba(230,246,237,0.18);/* dividers, borders */
```

### Grid Tokens (exact D2C)
```css
--gridGap:    24px;
--gridMargin: 40px;
--margin-xl:  72px;
--margin-l:   48px;
--margin-m:   24px;
--margin-s:   12px;
```

### Fonts
Font-face declarations at top of `validex-cinematic.css` (global, no scope):
- `Atipla ND` Bold → `/assets/fonts/subset-AtiplaND-Bold.woff2`
- `PP Fraktion Mono` Regular → `/assets/fonts/subset-PPFraktionMono-Regular.woff2`
- `PP Fraktion Mono` Bold → `/assets/fonts/subset-PPFraktionMono-Bold.woff2`

### Typography Classes (D2C parity)
```
.type__title-main       Atipla ND 700, clamp(27px, 5.4rem, 54px), uppercase, lh 1.04
.type__title-secondary  Atipla ND 700, clamp(20px, 4rem, 40px),   uppercase, lh 1.04
.type__body             PP Fraktion Mono 400, clamp(12px, 1.4rem, 14px), uppercase, lh 1.4
.type__hints            PP Fraktion Mono 400, 1rem, letter-spacing 0.1em, uppercase
```

### Button Variants (D2C parity)
```
.global__btn.type--primary  background #e6f6ed, color #717f71
.global__btn.type--ghost    background #e6f6ed1a, border 1px solid #e6f6ed,
                            color #e6f6ed, backdrop-filter blur(5px)
```

### Asset Paths
After copying from `~/Downloads`:
```
frontend/public/assets/fonts/
  subset-AtiplaND-Bold.woff2
  subset-PPFraktionMono-Regular.woff2
  subset-PPFraktionMono-Bold.woff2

frontend/public/assets/images/
  intro-cube@2x.png
  transition-cube@2x.png
  stats-cube@2x.png
  pillars-cube@2x.png
  secondary-transition@2x.png
  helix@2x.png  helix2@2x.png  helix-pill@2x.png
  stelle-risk.png  stelle-resources.png  stelle-performance.png
  stelle-foundations.png  stelle-culture.png  stelle-ai.png
  services-stone-1@2x.png  services-stone-2@2x.png
```

---

## 3. Packages to Install

```bash
npm install gsap @gsap/react lenis
```

- Use `useGSAP` from `@gsap/react` for animation hooks
- If `@gsap/react` unavailable, fall back to `useEffect` + `gsap.context`
- Do not rely on GSAP SplitText — use manual span injection

---

## 4. Animation Architecture

### SmoothScroll.jsx
- Creates Lenis instance with duration `1.6`, easing `t => Math.min(1, 1.001 - Math.pow(2, -10 * t))`
- Drives Lenis via GSAP ticker: `gsap.ticker.add(fn)` where `fn = time => lenis.raf(time * 1000)`
- `gsap.ticker.lagSmoothing(0)`
- `lenis.on("scroll", ScrollTrigger.update)`
- Exposes instance on `window.__lenis` for debug
- **Cleanup:** store ticker fn ref → `gsap.ticker.remove(fn)` → `lenis.off("scroll", ScrollTrigger.update)` → `lenis.destroy()`
- Wraps children in `<div class="smooth__scroll-wrapper">`

### Preloader.jsx
- Background `#717f71`, z-index 300
- Progress bar: `clip-path: inset(0% var(--progress) 0% 0%)` where `--progress` = `(100 - logicalProgress) + "%"` — starts at `100%` (bar hidden), ends at `0%` (bar full)
- Bar labels: 6 `<span>` nodes — `P`, `Q`, `FC`, `QC`, `META`, `SCORE` — rendered in `.bar__fill` and `.bar__background`
- Center text: `"Initializing audit engine"` — each character wrapped in `<span class="char">` by `splitChars()` utility
- Progress simulation: `setInterval` counting 0→85 over 2s, then snap to 100 and start exit
- Exit GSAP timeline: stagger `.char` opacity out → fade bar icons → `autoAlpha: 0` on preloader div → dispatch `new CustomEvent("preloader:done")` on `window`
- **Mobile:** skip to exit after 400ms (no progress simulation)
- **Cleanup:** clear interval, revert split chars

### ScrollTrigger Scope
All ScrollTrigger instances created inside `ValidexLanding` stored in a ref array. Killed in `useGSAP` cleanup (or `useEffect` cleanup) with `triggers.forEach(t => t.kill())`. Does not kill global triggers outside the landing.

After `preloader:done` fires → call `ScrollTrigger.refresh()` → then initialize all section scroll animations.

### prefers-reduced-motion
Detected via `window.matchMedia("(prefers-reduced-motion: reduce)")`.  
When active:
- Disable Lenis (render children without SmoothScroll wrapper)
- Skip scrub animations and parallax
- Skip infinite loops (cube float, button pulse)
- Show static assets with simple `opacity: 0 → 1` fades at 300ms

---

## 5. Component Spec

### ValidexLanding.jsx
**Props:** `{ onLaunch, onFileAccepted }`  
Root page. Wraps everything in `.validex-cinematic`. Owns the GSAP context for all scroll animations. Listens for `preloader:done` to trigger `ScrollTrigger.refresh()` and start section choreography.

```jsx
<div class="validex-cinematic">
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
```

---

### Preloader.jsx
**Props:** none  
**Output:** fires `window.dispatchEvent(new CustomEvent("preloader:done"))` on complete

```
.preloader (position:fixed, inset:0, bg #717f71, z-index 300)
  .preloader__ui-container
    .preloader__bar-container
      .bar__fill (clip-path driven by --progress)
        span×6: P Q FC QC META SCORE
      .bar__background (opacity 0.25)
        span×6: P Q FC QC META SCORE
    .ui__text
      span.char×N  ("Initializing audit engine")
```

---

### SmoothScroll.jsx
**Props:** `{ children }`  
Returns `<div class="smooth__scroll-wrapper">`. Full cleanup on unmount (see §4).

---

### Header.jsx
**Props:** `{ onLaunch }`  
Fixed, z-index 210. Fades in after `preloader:done`.

```
.header__logo    (fixed top-left, Atipla ND "VALIDEX")
.header__cta     (fixed top-right, ghost button "RUN AUDIT →" → calls onLaunch)
```

---

### HeroSection.jsx
**Props:** `{ onLaunch }`  
`id="hero"`. After preloader exits, headline words stagger up, cube floats in.

```
section.home__section.section__introduction
  .introduction__hud       ("VALIDEX AUDIT ENGINE" + scroll indicator)
  .wrapper
    .introduction__left-block
      .introduction__title-hud   (mono label: "METABOLOMICS VALIDATOR")
      h1.type__title-main        ("VALIDATE METABOLOMICS RESULTS BEFORE INTERPRETATION")
      .introduction__actions
        button.global__btn.type--primary  "RUN SAMPLE AUDIT"
          → scrolls to #product-demo
        button.global__btn.type--ghost    "VIEW WORKFLOW"
          → scrolls to #workflow
    .introduction__right-block
      img /assets/images/intro-cube@2x.png   (float: y ±12px, 3s sine, yoyo)
      p.type__body  "Validex audits result tables for statistical gaps…"
```

**Mobile:** cube centered above text, buttons full-width stacked.  
**Cube float animation:** created inside GSAP context, killed on unmount.

---

### ScrollTransition.jsx
**Props:** none  
`id="scroll-transition"`. Scrubbed by scroll progress.

```
section.home__section.section__transition
  .transition__block-container  (--progress CSS var → mask-image)
    .transition__block
      img transition-cube@2x.png
      img secondary-transition@2x.png  (layered, offset)
      .transition__icons
        span "MISSING FDR"          (appears at scroll progress 0.30)
        span "UNCLEAR EFFECT SIZE"  (0.50)
        span "INVALID P-VALUE RANGE"(0.65)
        span "METADATA GAP"         (0.80)
    .transition__text.type__title-secondary
      "DETECTED. SCORED. EXPLAINED."
```

**Desktop/full-motion:** `scrub: 1`, `--progress` updated via `onUpdate`, mask-image reveals cube.  
**Mobile + reduced-motion:** static cube image, all 4 labels visible at full opacity, no scrub.

---

### AuditModules.jsx
**Props:** none  
`id="audit-modules"`. Cards stagger in from below.

```
section.section__pillars
  .wrapper
    .pillars__block
      p.type__hints  "AUDIT LAYERS"
      h2.type__title-secondary  "THE VALIDATION MATRIX"
      .pillars__selector
        .pillars__selector-item × 6
          img stelle-*.png
          span.type__hints [label]
```

| Image | Label |
|---|---|
| `stelle-risk.png` | REPRODUCIBILITY RISK |
| `stelle-resources.png` | METADATA COMPLETENESS |
| `stelle-performance.png` | EFFECT SIZE ROBUSTNESS |
| `stelle-foundations.png` | QC FOUNDATION |
| `stelle-ai.png` | STATISTICAL INFERENCE |
| `stelle-culture.png` | EXPERIMENTAL CONSISTENCY |

**Animation:** `stagger: 0.08`, `y: 40→0`, `opacity: 0→1`, trigger `start: "top 75%"`.

---

### WorkflowSection.jsx
**Props:** none  
`id="workflow"`. Helix parallax + step reveals.

```
section.section__vision
  .vision__decorative-icons
    img /assets/images/helix@2x.png  (parallax: y -60→60 over section scroll)
  .wrapper
    .vision__block
      p.type__hints  "AUDIT PIPELINE"
      h2.type__title-secondary  "FROM RAW DATA TO VALIDITY REPORT"
      ol.workflow__steps
        li "RAW RESULTS" → "STATISTICAL TABLE" → "VALIDEX AUDIT"
           → "FLAGGED ISSUES" → "VALIDITY REPORT"
```

**Animation:** steps reveal left-to-right `stagger: 0.1`. Helix `scrub: 0.5` parallax.  
**Reduced-motion:** static helix, no parallax, simple fade-in for steps.

---

### ProductDemo.jsx
**Props:** `{ onLaunch, onFileAccepted }`  
`id="product-demo"`. Slides up on scroll enter.

```
section.section__service.service--demo
  .wrapper
    .service__block
      p.type__hints  "TRY IT NOW"
      h2.type__title-secondary  "UPLOAD YOUR RESULTS"
      .demo__grid
        .demo__upload-panel
          <UploadZone onFileAccepted={onFileAccepted ?? (() => {})} />
        .demo__audit-panel
          .audit__score-bar
            span.type__hints "VALIDITY SCORE"
            span.type__title-secondary "82 / 100"
          .audit__flags
            .flag[data-status="invalid"]   "MISSING FDR CORRECTION" / "HIGH PRIORITY"
            .flag[data-status="valid"]     "FOLD CHANGE DETECTED"   / "PASS"
            .flag[data-status="valid"]     "P-VALUE RANGE VALID"    / "PASS"
            .flag[data-status="partial"]   "METADATA COMPLETENESS"  / "PARTIAL"
          .audit__recommendation.type__body
            "Add q-values before confirmatory interpretation"
      .service__cta
        button.global__btn.type--ghost  "UPLOAD YOUR DATA" → onLaunch
```

**Flag colors:** `data-status="invalid"` → `--v-invalid`, `"valid"` → `--v-valid`, `"partial"` → `--v-partial`.  
**UploadZone:** rendered as-is, no prop or style modification. `onFileAccepted` safe fallback: `onFileAccepted ?? (() => {})`.  
**CTA "Run Sample Audit" in HeroSection:** scrolls to `#product-demo` via Lenis `scrollTo`.

---

### FinalCTA.jsx
**Props:** `{ onLaunch }`  
`id="final-cta"`. Cube and headline animate in on scroll.

```
section.section__primary-transition
  .section__background
    .wrapper
      .title__block
        img /assets/images/stats-cube@2x.png   (scale 0.8→1, opacity 0→1)
        h2.type__title-main
          "TURN STATISTICAL UNCERTAINTY INTO AN AUDIT TRAIL"
        button.global__btn.type--primary  "LAUNCH VALIDEX" → onLaunch
```

**Button pulse:** subtle `scale: 1→1.02` infinite loop, created inside GSAP context, killed on unmount.  
**Cube float:** `y ±8px`, 4s loop, same pattern as hero cube, killed on unmount.

---

## 6. App.jsx Change

**Only change:** replace `ArtefaktLanding` import and render with `ValidexLanding`:

```jsx
// Before
import ArtefaktLanding from "./components/ArtefaktLanding";
// ...
<ArtefaktLanding onLaunch={() => setView("upload")} onDemo={handleDemo} />

// After
import ValidexLanding from "./components/ValidexLanding";
// ...
<ValidexLanding
  onLaunch={() => setView("upload")}
  onFileAccepted={handleFileAccepted}
/>
```

All other App.jsx logic — state, API calls, `StepBar`, `Nav`, `RunningView`, `encodeSharePayload`, `decodeSharePayload` — preserved exactly.

---

## 7. Hard Constraints

1. Do not modify `frontend/src/index.css`
2. Do not modify `UploadZone.jsx`, `ContextForm.jsx`, `AuditResults.jsx`, `DataPreview.jsx`
3. Do not modify API logic or state management in `App.jsx`
4. All new CSS scoped under `.validex-cinematic` (except font-face)
5. All infinite GSAP loops created inside GSAP context and killed on unmount
6. All ScrollTrigger instances scoped to ValidexLanding, not killed globally
7. `UploadZone` receives only `onFileAccepted` — no other props added
8. Text splitting via manual `splitChars()` / `splitWords()` utilities — no GSAP SplitText
9. `prefers-reduced-motion`: disable Lenis, loops, scrub, parallax — simple fades only
10. Mobile: simplified preloader (400ms then exit), reduced-motion reveals

---

## 8. File Change Summary

| File | Action |
|---|---|
| `frontend/src/App.jsx` | 2-line change: import + render ValidexLanding |
| `frontend/src/styles/validex-cinematic.css` | New — full design system |
| `frontend/src/components/ValidexLanding.jsx` | New |
| `frontend/src/components/Preloader.jsx` | New |
| `frontend/src/components/SmoothScroll.jsx` | New |
| `frontend/src/components/Header.jsx` | New |
| `frontend/src/components/HeroSection.jsx` | New |
| `frontend/src/components/ScrollTransition.jsx` | New |
| `frontend/src/components/AuditModules.jsx` | New |
| `frontend/src/components/WorkflowSection.jsx` | New |
| `frontend/src/components/ProductDemo.jsx` | New |
| `frontend/src/components/FinalCTA.jsx` | New |
| `frontend/public/assets/fonts/*` | Copied from ~/Downloads |
| `frontend/public/assets/images/*` | Copied from ~/Downloads |
| All other files | Untouched |
