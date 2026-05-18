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
