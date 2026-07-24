import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import PillarModal from './PillarModal';

gsap.registerPlugin(ScrollTrigger);

const MODULES = [
  {
    key: 'fdr',
    image: '/assets/images/stelle-risk.png',
    label: 'FDR CORRECTION',
    tag: 'Q-VALUE',
    description: 'Checks whether q-values or adjusted p-values are present when multiple testing correction is expected.',
    checks: ['Adjusted p-value column detection', 'High-dimensional context evaluation', 'Confirmatory interpretation warning']
  },
  {
    key: 'pvalue',
    image: '/assets/images/stelle-resources.png',
    label: 'P-VALUE INTEGRITY',
    tag: 'P',
    description: 'Checks parse rate, numeric range, and missing p-value structure across the uploaded results table.',
    checks: ['Numeric parse rate', 'Range validation from 0 to 1', 'Missingness pattern detection']
  },
  {
    key: 'effect',
    image: '/assets/images/stelle-performance.png',
    label: 'EFFECT SIZE CLARITY',
    tag: 'LOG2FC',
    description: 'Checks fold change or log2FC presence so statistical significance is connected to interpretable magnitude.',
    checks: ['Fold change aliases', 'log2FC aliases', 'Effect size interpretability']
  },
  {
    key: 'qc',
    image: '/assets/images/stelle-foundations.png',
    label: 'QC FOUNDATION',
    tag: 'QC',
    description: 'Checks whether reporting provides enough quality-control context to support downstream interpretation.',
    checks: ['Batch expectation', 'Quality-control context', 'Reporting completeness']
  },
  {
    key: 'metadata',
    image: '/assets/images/stelle-ai.png',
    label: 'METADATA COMPLETENESS',
    tag: 'META',
    description: 'Checks context fields needed to interpret statistical claims and study design assumptions.',
    checks: ['Study goal', 'Design type', 'Group count', 'Alpha threshold']
  },
  {
    key: 'risk',
    image: '/assets/images/stelle-culture.png',
    label: 'REPRODUCIBILITY RISK',
    tag: 'RISK',
    description: 'Scores whether missing statistical and reporting elements weaken confidence in the final interpretation.',
    checks: ['Missing correction risk', 'Ambiguous effect risk', 'Audit score penalty']
  }
];

export default function AuditModules() {
  const sectionRef = useRef(null);
  const stageRef = useRef(null);
  const tilesRef = useRef([]);
  const textRef = useRef(null);
  const reassemblyRef = useRef(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || window.innerWidth < 900) return;

    const ctx = gsap.context(() => {
      gsap.set(tilesRef.current, {
        autoAlpha: 0,
        x: -360,
        y: i => (i % 2 === 0 ? -30 : 30),
        rotate: i => (i % 2 === 0 ? -4 : 4),
        scale: 0.9
      });
      gsap.set(textRef.current, { autoAlpha: 0, x: 60 });
      gsap.set(reassemblyRef.current, { autoAlpha: 0, scale: 0.86, x: 120 });

      const init = () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: '+=230%',
            scrub: 1,
            pin: true,
            anticipatePin: 1
          }
        });

        tl.to(tilesRef.current, {
          autoAlpha: 1,
          x: 0,
          y: 0,
          rotate: 0,
          scale: 1,
          stagger: 0.05,
          ease: 'none'
        }, 0.05);

        tl.to(textRef.current, {
          autoAlpha: 1,
          x: 0,
          ease: 'none'
        }, 0.12);

        tl.to(stageRef.current, {
          xPercent: -6,
          scale: 0.96,
          ease: 'none'
        }, 0.52);

        tl.to(tilesRef.current, {
          x: i => (i - 2) * 14,
          y: i => (i % 3 - 1) * 12,
          stagger: 0.02,
          ease: 'none'
        }, 0.62);

        tl.to(reassemblyRef.current, {
          autoAlpha: 1,
          scale: 1,
          x: 0,
          ease: 'none'
        }, 0.72);

        tl.to(stageRef.current, {
          autoAlpha: 0.24,
          scale: 0.82,
          xPercent: -18,
          ease: 'none'
        }, 0.78);

        tl.to(textRef.current, {
          autoAlpha: 0.35,
          y: -30,
          ease: 'none'
        }, 0.82);
      };

      window.addEventListener('preloader:done', init, { once: true });
      if (window.__validexReady) init();

      return () => window.removeEventListener('preloader:done', init);
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section className="audit-pillars" ref={sectionRef} id="audit-modules">
      <div className="audit-pillars__atmosphere" />

      <div className="audit-pillars__stage" ref={stageRef}>
        {MODULES.map((mod, index) => (
          <button
            key={mod.key}
            ref={el => { tilesRef.current[index] = el; }}
            className={`audit-pillars__tile tile--${index + 1}`}
            onClick={() => setSelected(mod)}
            type="button"
          >
            <img src={mod.image} alt={mod.label} loading="lazy" />
            <span className="audit-pillars__tag type__hints">{mod.tag}</span>
            <span className="audit-pillars__label type__hints">{mod.label}</span>
          </button>
        ))}
      </div>

      <div className="audit-pillars__copy" ref={textRef}>
        <p className="type__hints">AUDIT LAYERS</p>
        <h2 className="type__title-main">
          THE SIX AUDIT LAYERS<br />
          OF STATISTICAL VALIDITY
        </h2>
        <p className="type__body">
          Each layer checks a different failure point between a metabolomics table and a defensible interpretation.
        </p>
      </div>

      <div className="audit-pillars__reassembly" ref={reassemblyRef}>
        <img src="/assets/images/pillars-cube@2x.png" alt="Reassembled validation matrix" loading="lazy" />
        <p className="type__hints">VALIDATION MATRIX REASSEMBLED</p>
      </div>

      <PillarModal module={selected} onClose={() => setSelected(null)} />
    </section>
  );
}
