import { useRef, useEffect, useState } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// TUNING — change these values to adjust visuals without touching logic
// ─────────────────────────────────────────────────────────────────────────────
const CFG = {
  // ── Title glyph grid ────────────────────────────────────────────────────────
  charPx:        6,      // on-screen px per glyph — lower = denser letterforms
  introFrames:   96,     // stagger window (~1.6 s @ 60 fps)
  introSpring:   0.072,  // cinematic assembly spring (lower = slower)

  // ── Title scale ──────────────────────────────────────────────────────────────
  // The canvas is titleW × titleH. sampleFontScale is the fraction of canvas
  // HEIGHT used as the Impact font size for pixel-sampling.
  // titleFill controls what fraction of canvas WIDTH the word spans.
  titleW:          "96vw",  // canvas wrapper width  — was 88vw
  titleH:          "50vh",  // canvas wrapper height — was 40vh
  titleTopOffset:  "53%",   // vertical center offset (>50% = slightly lower)
  sampleFontScale: 0.80,    // Impact font = canvas-H × this  — was 0.70
  titleFill:       0.86,    // word fills this fraction of canvas width

  // ── Mouse / pointer interaction ─────────────────────────────────────────────
  mouseRadius:   110,    // px — tune for wider/narrower interaction zone
  mouseStrength: 20,     // px — max repulsion displacement
  mouseSpring:   0.13,   // return-to-base spring stiffness

  // ── Glyph brightness (title) ─────────────────────────────────────────────────
  // brightBase × flickerLo = minimum alpha. Keep both high for near-white.
  brightBase:    0.82,   // floor brightness per cell
  brightRange:   0.18,   // variance on top (range: brightBase → brightBase+brightRange)
  flickerLo:     0.88,   // per-frame flicker floor
  flickerHi:     1.00,   // per-frame flicker ceiling

  // ── Background square matrix grid ────────────────────────────────────────────
  // SVG tile: lit square cells separated by pure-black 1 px gaps.
  // gridCellColor is URL-encoded hex for cell fill. Darker = more embedded.
  gridCellPx:    9,           // cell size in px  (8 = tight, 12 = loose)
  gridGapPx:     1,           // gap between cells in px
  gridCellColor: "%230c0c0c", // cell colour — was %23161616, now darker/subtler

  // ── Ambient signal noise ─────────────────────────────────────────────────────
  noiseMax:       12,    // max simultaneous ambient glyphs on screen
  noiseAlpha:     0.18,  // peak brightness of ambient glyphs (dimmer than title)
  noiseSpawnRate: 0.05,  // probability per frame of spawning a new glyph
  noiseMinLife:   18,    // min glyph lifetime in frames (~300 ms @ 60 fps)
  noiseMaxLife:   55,    // max glyph lifetime in frames (~920 ms @ 60 fps)
  noiseFontPx:    10,    // ambient glyph font size in on-screen px

  // ── UI reveal timing ─────────────────────────────────────────────────────────
  uiDelay: 1500,         // ms before nav + corners fade in
  uiFade:  "0.9s",
};

// ─────────────────────────────────────────────────────────────────────────────
// GLYPH SET — alphanumeric weighted 2× heavier than punctuation
// ─────────────────────────────────────────────────────────────────────────────
const GLYPHS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" +
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" +
  "!@#$%&*[]{},.:;-_+=~<>/?|";
const g = () => GLYPHS[~~(Math.random() * GLYPHS.length)];

// ─────────────────────────────────────────────────────────────────────────────
// useScramble — randomises, then resolves character-by-character
// ─────────────────────────────────────────────────────────────────────────────
function useScramble(target, delayMs = 0) {
  const [out, setOut] = useState(() =>
    target.split("").map((c) => (c === " " ? " " : g())).join("")
  );
  useEffect(() => {
    let resolved = 0, raf, lastT = 0;
    const timer = setTimeout(() => {
      const tick = (now) => {
        if (now - lastT >= 36) {
          lastT = now; resolved++;
          if (resolved > target.length) { setOut(target); return; }
          setOut(target.split("").map((c, i) =>
            c === " " ? " " : i < resolved ? c : g()
          ).join(""));
        }
        raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    }, delayMs);
    return () => { clearTimeout(timer); cancelAnimationFrame(raf); };
  }, [target, delayMs]);
  return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// MatrixGrid — full-viewport square-cell background
// SVG data-URI tile: slightly-lit rectangles with 1 px black gaps.
// Tune CFG.gridCellPx, CFG.gridGapPx, CFG.gridCellColor.
// ─────────────────────────────────────────────────────────────────────────────
function MatrixGrid() {
  const C    = CFG.gridCellPx;
  const G    = CFG.gridGapPx;
  const TILE = C + G;
  const svg  = `url("data:image/svg+xml,%3Csvg width='${TILE}' height='${TILE}' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='${C}' height='${C}' fill='${CFG.gridCellColor}'/%3E%3C/svg%3E")`;
  return (
    <div aria-hidden style={{
      position: "absolute", inset: 0, zIndex: 1, pointerEvents: "none",
      backgroundColor: "#000",
      backgroundImage: svg,
      backgroundSize: `${TILE}px ${TILE}px`,
      backgroundRepeat: "repeat",
    }} />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// AmbientNoise — sparse full-viewport glyph particles
// Tune CFG.noiseMax, CFG.noiseAlpha, CFG.noiseSpawnRate.
// ─────────────────────────────────────────────────────────────────────────────
function AmbientNoise() {
  const cvRef  = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const cv = cvRef.current;
    if (!cv) return;

    const resize = () => { cv.width = window.innerWidth; cv.height = window.innerHeight; };
    resize();
    window.addEventListener("resize", resize);

    const ctx  = cv.getContext("2d");
    const particles = [];
    const FPX  = CFG.noiseFontPx;

    // Title band: 30–70 vh. Particles CAN spawn here but at 35% alpha multiplier.
    const titleAlphaMult = (y) => {
      const lo = cv.height * 0.30, hi = cv.height * 0.70;
      return (y > lo && y < hi) ? 0.35 : 1.0;
    };

    const spawn = () => {
      // Slight bias toward title-adjacent area (edges of title band)
      const nearTitle = Math.random() < 0.25;
      const y = nearTitle
        ? cv.height * (0.20 + Math.random() * 0.60) // broader title region
        : Math.random() * cv.height;
      return {
        x:        Math.random() * cv.width,
        y,
        char:     g(),
        life:     0,
        maxLife:  CFG.noiseMinLife + ~~(Math.random() * (CFG.noiseMaxLife - CFG.noiseMinLife)),
        aMult:    titleAlphaMult(y),
      };
    };

    let frame = 0;
    ctx.font = `${FPX}px "Space Mono","Courier New",Courier,monospace`;
    ctx.textBaseline = "top";

    const draw = () => {
      ctx.clearRect(0, 0, cv.width, cv.height);

      if (particles.length < CFG.noiseMax && Math.random() < CFG.noiseSpawnRate) {
        particles.push(spawn());
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life++;
        const t   = p.life / p.maxLife;
        const env = t < 0.25 ? t / 0.25 : t > 0.75 ? (1 - t) / 0.25 : 1;

        // Occasionally mutate — keeps it alive-looking
        if (frame % 6 === 0 && Math.random() < 0.35) p.char = g();

        ctx.fillStyle = `rgba(255,255,255,${env * CFG.noiseAlpha * p.aMult})`;
        ctx.fillText(p.char, p.x, p.y);

        if (p.life >= p.maxLife) particles.splice(i, 1);
      }

      frame++;
      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(rafRef.current); window.removeEventListener("resize", resize); };
  }, []);

  return (
    <canvas ref={cvRef} aria-hidden style={{
      position: "absolute", inset: 0,
      width: "100%", height: "100%",
      zIndex: 2, pointerEvents: "none", display: "block",
    }} />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// AsciiCanvas — interactive hero title
// ─────────────────────────────────────────────────────────────────────────────
function AsciiCanvas() {
  const wrapRef  = useRef(null);
  const cvRef    = useRef(null);
  const rafRef   = useRef(null);
  const mouseRef = useRef({ x: -9999, y: -9999 });

  useEffect(() => {
    const wrap = wrapRef.current, cv = cvRef.current;
    if (!wrap || !cv) return;

    const dpr = window.devicePixelRatio || 1;
    const W   = wrap.clientWidth  * dpr;
    const H   = wrap.clientHeight * dpr;
    cv.width  = W; cv.height = H;

    const ctx = cv.getContext("2d");

    // ── 1. Pixel-sample letter mask ──────────────────────────────────────────
    const mask = Object.assign(document.createElement("canvas"), { width: W, height: H });
    const mctx = mask.getContext("2d");

    mctx.fillStyle = "#000";
    mctx.fillRect(0, 0, W, H);
    mctx.fillStyle = "#fff";

    // Set font and measure natural text width
    const fontPx = H * CFG.sampleFontScale;
    mctx.font         = `900 ${fontPx}px "Impact","Arial Black","Helvetica Neue",sans-serif`;
    mctx.textBaseline = "middle";
    mctx.textAlign    = "center";
    const naturalW    = mctx.measureText("validex").width;

    // ── 2. Scale horizontally so the word fills CFG.titleFill of canvas width ─
    // This is the key change: auto-scales letters to be dominant + well-spaced.
    // Tune CFG.titleFill (0.80 = compact, 0.92 = very wide).
    const targetW = W * CFG.titleFill;
    const scaleX  = targetW / naturalW;

    // Transform: scale about horizontal center so the word stays centered
    mctx.setTransform(scaleX, 0, 0, 1, W / 2 * (1 - scaleX), 0);
    mctx.fillText("validex", W / 2, H / 2);
    mctx.resetTransform();

    const px = mctx.getImageData(0, 0, W, H).data;

    // ── 3. Build character-cell grid ─────────────────────────────────────────
    const CH = Math.round(CFG.charPx * dpr);
    const CW = Math.round(CH * 0.58); // monospace aspect ratio
    const cells = [];

    for (let cy = 0; cy < H; cy += CH) {
      for (let cx = 0; cx < W; cx += CW) {
        const sx = Math.min(~~(cx + CW / 2), W - 1);
        const sy = Math.min(~~(cy + CH / 2), H - 1);
        if (px[(sy * W + sx) * 4] > 64) {
          cells.push({
            bx: cx, by: cy,
            x:  Math.random() * W,  // scatter start for fly-in animation
            y:  Math.random() * H,
            delay:  ~~(Math.random() * CFG.introFrames),
            bright: CFG.brightBase + Math.random() * CFG.brightRange,
          });
        }
      }
    }

    // ── 4. Mouse interaction ─────────────────────────────────────────────────
    const R  = CFG.mouseRadius   * dpr;
    const R2 = R * R;
    const ST = CFG.mouseStrength * dpr;

    const onMove = ({ clientX, clientY }) => {
      const r = cv.getBoundingClientRect();
      mouseRef.current = {
        x: (clientX - r.left) * (W / r.width),
        y: (clientY - r.top)  * (H / r.height),
      };
    };
    const onLeave = () => { mouseRef.current = { x: -9999, y: -9999 }; };
    wrap.addEventListener("mousemove",  onMove);
    wrap.addEventListener("mouseleave", onLeave);

    // ── 5. RAF draw loop ──────────────────────────────────────────────────────
    ctx.font = `400 ${CH}px "Space Mono","Courier New",Courier,monospace`;
    ctx.textBaseline = "top";
    let frame = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const { x: mx, y: my } = mouseRef.current;

      for (const c of cells) {
        if (frame < c.delay) continue;

        const age  = frame - c.delay;
        const fade = Math.min(1, age / 14); // fade in over ~14 frames

        // Mouse repulsion — squared-distance check avoids sqrt for distant cells
        const ddx = c.bx - mx, ddy = c.by - my;
        const d2  = ddx * ddx + ddy * ddy;
        let tx = c.bx, ty = c.by, boost = 0;
        if (d2 < R2) {
          const dist = Math.sqrt(d2), t = 1 - dist / R;
          const a = Math.atan2(ddy, ddx);
          tx    = c.bx + Math.cos(a) * ST * t;
          ty    = c.by + Math.sin(a) * ST * t;
          boost = t * 0.40; // brighten near cursor
        }

        // Two-phase spring: slow cinematic assembly → snappy idle interaction
        const settled = age > CFG.introFrames * 0.6;
        const k = settled ? CFG.mouseSpring : CFG.introSpring;
        c.x += (tx - c.x) * k;
        c.y += (ty - c.y) * k;

        const flicker = CFG.flickerLo + Math.random() * (CFG.flickerHi - CFG.flickerLo);
        const alpha   = Math.min(1, fade * (c.bright * flicker) + boost);
        ctx.fillStyle = `rgba(255,255,255,${alpha})`;
        ctx.fillText(g(), c.x, c.y);
      }

      frame++;
      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(rafRef.current);
      wrap.removeEventListener("mousemove",  onMove);
      wrap.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div ref={wrapRef} style={{ position: "absolute", inset: 0, cursor: "crosshair" }}>
      <canvas ref={cvRef} style={{ display: "block", width: "100%", height: "100%" }} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared edge-text style — Space Mono, pure white, tight uppercase
// ─────────────────────────────────────────────────────────────────────────────
const MONO = {
  fontFamily:    '"Space Mono","Courier New",Courier,monospace',
  fontSize:      10,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  lineHeight:    "2.2",
  color:         "#fff",
};

// ─────────────────────────────────────────────────────────────────────────────
// Nav
// ─────────────────────────────────────────────────────────────────────────────
function Nav({ onLaunch, show }) {
  const d   = CFG.uiDelay;
  const logo = useScramble("validex",       d);
  const c1a  = useScramble("RUN AUDIT",     d +  80);
  const c1b  = useScramble("ABOUT",         d + 180);
  const c2a  = useScramble("GITHUB",        d + 250);
  const c2b  = useScramble("CONTACT",       d + 340);
  const c3a  = useScramble("AI AUDIT TOOL", d + 400);
  const c3b  = useScramble("METABOLOMICS",  d + 500);

  return (
    <nav style={{
      ...MONO,
      position: "absolute", top: 0, left: 0, right: 0, zIndex: 10,
      display: "flex", alignItems: "flex-start", justifyContent: "space-between",
      padding: "18px 26px",
      opacity: show ? 1 : 0,
      transition: `opacity ${CFG.uiFade} ease`,
      pointerEvents: show ? "auto" : "none",
    }}>

      {/* ── Top-left logo: heavier, larger, logo-weight authority ─────────────
          Tune fontSize (18–24) and fontWeight (700) for brand presence.        */}
      <button onClick={onLaunch} style={{
        all:           "unset",
        fontFamily:    '"Space Mono","Courier New",Courier,monospace',
        color:         "#fff",
        fontSize:      20,       // was 13 — now clearly dominant vs 10px nav text
        fontWeight:    700,
        letterSpacing: "-0.02em",
        textTransform: "lowercase",
        cursor:        "pointer",
        lineHeight:    1,
        paddingTop:    1,
      }}>{logo}</button>

      {/* Center-left */}
      <div>
        <div style={{ cursor: "pointer" }} onClick={onLaunch}>{c1a}</div>
        <div>{c1b}</div>
      </div>

      {/* Center-right */}
      <div>
        <div>{c2a}</div>
        <div>{c2b}</div>
      </div>

      {/* Top-right */}
      <div style={{ textAlign: "right" }}>
        <div>{c3a}</div>
        <div>{c3b}</div>
      </div>
    </nav>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Bottom corners
// ─────────────────────────────────────────────────────────────────────────────
function Corners({ onLaunch, show }) {
  const d   = CFG.uiDelay;
  const tl1 = useScramble("METABOLOMICS AUDIT.",                              d + 120);
  const tl2 = useScramble("REIMAGINED.",                                      d + 300);
  const tr1 = useScramble("VALIDEX IS AN AI-POWERED TOOL THAT VALIDATES",    d + 200);
  const tr2 = useScramble("METABOLOMICS DATA FOR PUBLICATION-READY SCIENCE.", d + 420);

  const base = {
    ...MONO,
    position: "absolute", bottom: 22, zIndex: 10,
    opacity:  show ? 1 : 0,
    transition: `opacity ${CFG.uiFade} ease`,
  };

  return (
    <>
      {/* Bottom-left — tagline */}
      <div onClick={onLaunch} style={{ ...base, left: 26, cursor: "pointer" }}>
        <div>{tl1}</div>
        <div>{tl2}</div>
      </div>

      {/* Bottom-right — descriptor paragraph
          Tune maxWidth (300–440px) and lineHeight for paragraph density.      */}
      <div style={{
        ...base,
        right:      26,
        textAlign:  "right",
        maxWidth:   "360px",   // was 44vw — now a fixed tight column
        lineHeight: "1.95",    // slightly tighter than MONO default
      }}>
        <div>{tr1}</div>
        <div>{tr2}</div>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Right-edge reticle icon
// ─────────────────────────────────────────────────────────────────────────────
function Reticle({ show }) {
  return (
    <div style={{
      position: "absolute", right: 22, top: "50%",
      transform: "translateY(-50%)",
      width: 30, height: 30,
      border: "1px solid rgba(255,255,255,0.22)",
      borderRadius: "50%",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 10, cursor: "pointer",
      opacity: show ? 1 : 0, transition: `opacity ${CFG.uiFade} ease`,
    }}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="7" r="5.5" stroke="rgba(255,255,255,0.40)" strokeWidth="0.85" />
        <circle cx="7" cy="7" r="2.4" stroke="rgba(255,255,255,0.30)" strokeWidth="0.75" />
        <circle cx="7" cy="7" r="0.8" fill="rgba(255,255,255,0.45)" />
      </svg>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Root
// ─────────────────────────────────────────────────────────────────────────────
export default function ArtefaktLanding({ onLaunch }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), CFG.uiDelay);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000", overflow: "hidden" }}>

      {/* ── Square matrix grid ───────────────────────────────────────────────
          Tune CFG.gridCellPx (cell size), CFG.gridCellColor (brightness).     */}
      <MatrixGrid />

      {/* ── Ambient signal noise ─────────────────────────────────────────────
          Tune CFG.noiseMax, CFG.noiseAlpha, CFG.noiseSpawnRate.               */}
      <AmbientNoise />

      {/* ── ASCII hero title ─────────────────────────────────────────────────
          Tune CFG.titleW / CFG.titleH (canvas size) and CFG.titleFill
          (how much of canvas width the word fills). CFG.titleTopOffset
          shifts the vertical centre (>50% = slightly lower on page).          */}
      <div style={{
        position:  "absolute",
        top:       CFG.titleTopOffset,
        left:      "50%",
        transform: "translate(-50%, -50%)",
        width:     CFG.titleW,
        height:    CFG.titleH,
        zIndex:    3,
      }}>
        <AsciiCanvas />
      </div>

      <Nav     onLaunch={onLaunch} show={show} />
      <Corners onLaunch={onLaunch} show={show} />
      <Reticle show={show} />
    </div>
  );
}
