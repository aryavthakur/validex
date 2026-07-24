import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function FinalCTA({ onLaunch }) {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const copyRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.set([cubeRef.current, copyRef.current, buttonRef.current], { autoAlpha: 0, y: 32 });
      gsap.set(cubeRef.current, { scale: 0.82 });

      const trigger = ScrollTrigger.create({
        trigger: section,
        start: 'top 70%',
        once: true,
        onEnter: () => {
          gsap.to(cubeRef.current, {
            autoAlpha: 1,
            y: 0,
            scale: 1,
            duration: 1,
            ease: 'power3.out'
          });
          gsap.to([copyRef.current, buttonRef.current], {
            autoAlpha: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.12,
            ease: 'power3.out',
            delay: 0.18
          });
          gsap.to(cubeRef.current, {
            y: -10,
            duration: 3.8,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1,
            delay: 1
          });
        }
      });

      return () => trigger.kill();
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section className="final-scene" ref={sectionRef} id="final-cta">
      <div className="final-scene__atmosphere" />

      <img
        ref={cubeRef}
        className="final-scene__cube"
        src="/assets/images/stats-cube@2x.png"
        alt="Validated audit matrix"
        loading="lazy"
      />

      <div className="final-scene__copy" ref={copyRef}>
        <p className="type__hints">VALIDATION COMPLETE</p>
        <h2 className="type__title-main">
          TURN STATISTICAL<br />
          UNCERTAINTY INTO<br />
          AN AUDIT TRAIL
        </h2>
        <p className="type__body">A structured validation layer before interpretation, review, or publication.</p>
      </div>

      <button ref={buttonRef} className="global__btn type--primary" onClick={onLaunch}>
        LAUNCH VALIDEX
      </button>
    </section>
  );
}
