import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { splitWords } from '../utils/splitText';

export default function HeroSection({ onLaunch }) {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const titleRef = useRef(null);
  const floatAnimRef = useRef(null);

  const scrollTo = id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (window.__lenis) {
      window.__lenis.scrollTo(el, { offset: -80, duration: 1.6 });
    } else {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    gsap.set(sectionRef.current, { autoAlpha: 0 });

    const handleDone = () => {
      gsap.to(sectionRef.current, { autoAlpha: 1, duration: 0.6, ease: 'power2.out' });

      if (!reduced && titleRef.current) {
        const words = splitWords(titleRef.current);
        gsap.from(words, {
          y: 30,
          opacity: 0,
          duration: 0.8,
          stagger: 0.05,
          ease: 'power3.out',
          delay: 0.2,
        });
      }

      if (!reduced && cubeRef.current) {
        floatAnimRef.current = gsap.to(cubeRef.current, {
          y: -12,
          rotation: 2,
          duration: 3,
          ease: 'sine.inOut',
          yoyo: true,
          repeat: -1,
        });
      }
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      if (floatAnimRef.current) floatAnimRef.current.kill();
    };
  }, []);

  return (
    <section className="home__section section__introduction" ref={sectionRef} id="hero">
      <div className="introduction__hud">
        <div className="hud__top">
          <span className="type__hints">VALIDEX AUDIT ENGINE</span>
        </div>
        <div className="hud__middle">
          <div className="middle__separator" />
          <div className="middle__scroll-indicator">
            <span className="type__hints">SCROLL TO EXPLORE</span>
          </div>
        </div>
      </div>
      <div className="wrapper">
        <div className="introduction__left-block">
          <div className="introduction__title-hud">
            <span className="type__hints">METABOLOMICS VALIDATOR</span>
          </div>
          <h1 className="type__title-main" ref={titleRef}>
            Validate metabolomics results before interpretation
          </h1>
          <div className="introduction__actions">
            <button
              className="global__btn type--primary"
              onClick={() => scrollTo('product-demo')}
            >
              RUN SAMPLE AUDIT
            </button>
            <button
              className="global__btn type--ghost"
              onClick={() => scrollTo('workflow')}
            >
              VIEW WORKFLOW
            </button>
          </div>
        </div>
        <div className="introduction__right-block">
          <img
            ref={cubeRef}
            src="/assets/images/intro-cube@2x.png"
            alt="Validation Matrix"
            loading="lazy"
          />
          <p className="type__body">
            Validex audits result tables for statistical gaps, missing corrections,
            unclear effect sizes, and reproducibility risk.
          </p>
        </div>
      </div>
    </section>
  );
}
