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
