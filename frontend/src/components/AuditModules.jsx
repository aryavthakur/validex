import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const MODULES = [
  { image: '/assets/images/stelle-risk.png',        label: 'REPRODUCIBILITY RISK',     key: 'risk' },
  { image: '/assets/images/stelle-resources.png',   label: 'METADATA COMPLETENESS',    key: 'resources' },
  { image: '/assets/images/stelle-performance.png', label: 'EFFECT SIZE ROBUSTNESS',   key: 'performance' },
  { image: '/assets/images/stelle-foundations.png', label: 'QC FOUNDATION',            key: 'foundations' },
  { image: '/assets/images/stelle-ai.png',          label: 'STATISTICAL INFERENCE',    key: 'ai' },
  { image: '/assets/images/stelle-culture.png',     label: 'EXPERIMENTAL CONSISTENCY', key: 'culture' },
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
