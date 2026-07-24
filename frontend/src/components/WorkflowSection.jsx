import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  'RAW RESULTS',
  'STATISTICAL TABLE',
  'VALIDEX AUDIT',
  'FLAGGED ISSUES',
  'VALIDITY REPORT'
];

export default function WorkflowSection() {
  const sectionRef = useRef(null);
  const helixRef = useRef(null);
  const stepsRef = useRef([]);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.set(stepsRef.current, { autoAlpha: 0, y: 24 });
      gsap.set(helixRef.current, { y: 80, rotate: -2 });

      const trigger = ScrollTrigger.create({
        trigger: section,
        start: 'top 70%',
        once: true,
        onEnter: () => {
          gsap.to(stepsRef.current, {
            autoAlpha: 1,
            y: 0,
            duration: 0.75,
            stagger: 0.09,
            ease: 'power3.out'
          });
        }
      });

      const parallax = gsap.to(helixRef.current, {
        y: -70,
        rotate: 2,
        ease: 'none',
        scrollTrigger: {
          trigger: section,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 0.6
        }
      });

      return () => {
        trigger.kill();
        parallax.kill();
      };
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section className="workflow-scene" ref={sectionRef} id="workflow">
      <div className="workflow-scene__atmosphere" />
      <img
        ref={helixRef}
        className="workflow-scene__helix"
        src="/assets/images/helix@2x.png"
        alt=""
        loading="lazy"
      />

      <div className="workflow-scene__copy">
        <p className="type__hints">AUDIT PIPELINE</p>
        <h2 className="type__title-main">
          FROM RAW DATA<br />
          TO VALIDITY REPORT
        </h2>
      </div>

      <ol className="workflow-scene__steps">
        {STEPS.map((step, index) => (
          <li
            key={step}
            className="workflow-scene__step"
            ref={el => { stepsRef.current[index] = el; }}
          >
            <span className="type__body">{step}</span>
            {index < STEPS.length - 1 && <span className="workflow-scene__arrow">→</span>}
          </li>
        ))}
      </ol>
    </section>
  );
}
