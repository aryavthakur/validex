import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const FAULTS = [
  { label: 'MISSING FDR', className: 'fault--one' },
  { label: 'UNCLEAR EFFECT SIZE', className: 'fault--two' },
  { label: 'INVALID P-VALUE RANGE', className: 'fault--three' },
  { label: 'METADATA GAP', className: 'fault--four' }
];

export default function ScrollTransition() {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const secondaryRef = useRef(null);
  const textRef = useRef(null);
  const labelsRef = useRef([]);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || window.innerWidth < 900) return;

    const ctx = gsap.context(() => {
      gsap.set(textRef.current, { autoAlpha: 0, x: -60 });
      gsap.set(cubeRef.current, { xPercent: -24, yPercent: 8, scale: 1.12 });
      gsap.set(secondaryRef.current, { autoAlpha: 0, x: 80, y: -20 });
      gsap.set(labelsRef.current, { autoAlpha: 0, scale: 0.92 });

      const init = () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: '+=170%',
            scrub: 1,
            pin: true,
            anticipatePin: 1
          }
        });

        tl.to(cubeRef.current, {
          xPercent: 26,
          yPercent: -3,
          scale: 0.94,
          rotate: 1.5,
          ease: 'none'
        }, 0);

        tl.to(textRef.current, {
          autoAlpha: 1,
          x: 0,
          ease: 'none'
        }, 0.12);

        tl.to(secondaryRef.current, {
          autoAlpha: 0.72,
          x: 0,
          y: 0,
          ease: 'none'
        }, 0.22);

        tl.to(labelsRef.current, {
          autoAlpha: 1,
          scale: 1,
          stagger: 0.08,
          ease: 'none'
        }, 0.34);

        tl.to(cubeRef.current, {
          xPercent: 55,
          scale: 0.82,
          autoAlpha: 0.75,
          ease: 'none'
        }, 0.75);

        tl.to(textRef.current, {
          y: -24,
          autoAlpha: 0.4,
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
    <section className="data-transition" ref={sectionRef} id="scroll-transition">
      <div className="data-transition__atmosphere" />

      <div className="data-transition__text" ref={textRef}>
        <p className="type__hints">STATISTICAL INTERPRETATION CONTROL</p>
        <h2 className="type__title-main">
          WE AUDIT DATA<br />
          BEFORE IT BECOMES EVIDENCE
        </h2>
      </div>

      <div className="data-transition__visual">
        <img
          ref={cubeRef}
          className="data-transition__cube"
          src="/assets/images/transition-cube@2x.png"
          alt="Fragmented validation matrix"
          loading="eager"
        />
        <img
          ref={secondaryRef}
          className="data-transition__secondary"
          src="/assets/images/secondary-transition@2x.png"
          alt=""
          loading="lazy"
        />

        {FAULTS.map((fault, index) => (
          <span
            key={fault.label}
            ref={el => { labelsRef.current[index] = el; }}
            className={`data-transition__fault type__hints ${fault.className}`}
          >
            {fault.label}
          </span>
        ))}
      </div>
    </section>
  );
}
