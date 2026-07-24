import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import UploadZone from './UploadZone';

gsap.registerPlugin(ScrollTrigger);

const FLAGS = [
  { label: 'MISSING FDR CORRECTION', status: 'invalid', note: 'HIGH PRIORITY' },
  { label: 'FOLD CHANGE DETECTED', status: 'valid', note: 'PASS' },
  { label: 'P-VALUE RANGE VALID', status: 'valid', note: 'PASS' },
  { label: 'METADATA COMPLETENESS', status: 'partial', note: 'PARTIAL' }
];

export default function ProductDemo({ onLaunch, onFileAccepted }) {
  const sectionRef = useRef(null);
  const scoreRef = useRef(null);
  const safeFileAccepted = typeof onFileAccepted === 'function' ? onFileAccepted : () => {
    console.warn('ProductDemo missing onFileAccepted');
  };

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.set('.demo-shell__upload, .demo-shell__audit, .demo-shell__copy', { autoAlpha: 0, y: 34 });

      const trigger = ScrollTrigger.create({
        trigger: section,
        start: 'top 65%',
        once: true,
        onEnter: () => {
          gsap.to('.demo-shell__copy, .demo-shell__upload, .demo-shell__audit', {
            autoAlpha: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.1,
            ease: 'power3.out'
          });

          if (scoreRef.current) {
            gsap.fromTo(scoreRef.current, { textContent: 0 }, {
              textContent: 82,
              duration: 1.1,
              delay: 0.35,
              snap: { textContent: 1 },
              ease: 'power2.out'
            });
          }
        }
      });

      return () => trigger.kill();
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section className="demo-shell" ref={sectionRef} id="product-demo">
      <div className="demo-shell__atmosphere" />

      <div className="demo-shell__copy">
        <p className="type__hints">TRY IT NOW</p>
        <h2 className="type__title-main">
          UPLOAD YOUR<br />
          RESULTS CSV
        </h2>
        <p className="type__body">
          Upload a metabolomics results CSV. Validex checks statistical reporting, correction status, effect size clarity,
          metadata completeness, and reproducibility risk. It returns a scored audit with flags and recommendations.
        </p>
      </div>

      <div className="demo-shell__grid">
        <div className="demo-shell__upload">
          <UploadZone onFileAccepted={safeFileAccepted} />
        </div>

        <div className="demo-shell__audit">
          <div className="demo-shell__score">
            <p className="type__hints">VALIDITY SCORE</p>
            <div className="demo-shell__score-number">
              <span ref={scoreRef}>82</span>
              <span>/100</span>
            </div>
          </div>

          <div className="demo-shell__flags">
            {FLAGS.map(flag => (
              <div className="demo-shell__flag" data-status={flag.status} key={flag.label}>
                <span className="type__body">{flag.label}</span>
                <span className="type__hints">{flag.note}</span>
              </div>
            ))}
          </div>

          <div className="demo-shell__recommendation type__body">
            Add q-values before confirmatory interpretation.
          </div>

          <button className="global__btn type--ghost" onClick={onLaunch}>
            UPLOAD YOUR DATA
          </button>
        </div>
      </div>
    </section>
  );
}
