import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export default function HeroSection() {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const copyRef = useRef(null);
  const hudRef = useRef(null);

  const scrollTo = id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (window.__lenis) window.__lenis.scrollTo(el, { offset: -60, duration: 1.5 });
    else el.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const section = sectionRef.current;
    const cube = cubeRef.current;
    const copy = copyRef.current;
    const hud = hudRef.current;
    if (!section || !cube || !copy || !hud) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ctx = gsap.context(() => {
      gsap.set([copy, hud], { autoAlpha: 0, y: 20 });
      gsap.set(cube, { autoAlpha: 0, scale: 0.84, xPercent: -4, yPercent: 3 });

      const init = () => {
        if (reduced || window.innerWidth < 900) {
          gsap.to([copy, hud, cube], { autoAlpha: 1, y: 0, scale: 1, duration: 0.6, ease: 'power2.out' });
          return;
        }

        gsap.to([copy, hud], { autoAlpha: 1, y: 0, duration: 0.8, stagger: 0.08, ease: 'power3.out' });
        gsap.to(cube, { autoAlpha: 1, scale: 1, duration: 1, ease: 'power3.out' });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: '+=185%',
            scrub: 1,
            pin: true,
            anticipatePin: 1
          }
        });

        tl.to(cube, {
          xPercent: 34,
          yPercent: -8,
          scale: 0.92,
          rotate: 2,
          ease: 'none'
        }, 0);

        tl.to(copy, {
          y: -28,
          autoAlpha: 0,
          ease: 'none'
        }, 0.46);

        tl.to(hud, {
          autoAlpha: 0.35,
          ease: 'none'
        }, 0.35);

        tl.to(cube, {
          xPercent: 62,
          yPercent: -4,
          scale: 0.82,
          autoAlpha: 0.55,
          ease: 'none'
        }, 0.72);
      };

      window.addEventListener('preloader:done', init, { once: true });
      if (window.__validexReady) init();

      return () => window.removeEventListener('preloader:done', init);
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section className="hero-scene" ref={sectionRef} id="hero">
      <div className="hero-scene__atmosphere" />
      <div className="hero-scene__hud" ref={hudRef}>
        <span className="type__hints">VALIDEX AUDIT ENGINE</span>
        <span className="type__hints">SCROLL TO EXPLORE</span>
      </div>

      <img
        ref={cubeRef}
        className="hero-scene__cube"
        src="/assets/images/intro-cube@2x.png"
        alt="Validation Matrix"
        loading="eager"
        fetchPriority="high"
      />

      <div className="hero-scene__copy" ref={copyRef}>
        <p className="type__hints">METABOLOMICS VALIDATOR</p>
        <h1 className="type__title-main">
          VALIDATE METABOLOMICS RESULTS<br />
          BEFORE INTERPRETATION
        </h1>
        <p className="type__body hero-scene__subcopy">
          A statistical audit layer for metabolomics result tables.
        </p>
        <div className="hero-scene__actions">
          <button className="global__btn type--primary" onClick={() => scrollTo('product-demo')}>
            VIEW SAMPLE AUDIT
          </button>
          <button className="global__btn type--ghost" onClick={() => scrollTo('workflow')}>
            VIEW WORKFLOW
          </button>
        </div>
      </div>
    </section>
  );
}
