import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import '../styles/validex-cinematic.css';
import Preloader from './Preloader';
import SmoothScroll from './SmoothScroll';
import Header from './Header';
import HeroSection from './HeroSection';
import ScrollTransition from './ScrollTransition';
import AuditModules from './AuditModules';
import WorkflowSection from './WorkflowSection';
import ProductDemo from './ProductDemo';
import FinalCTA from './FinalCTA';

gsap.registerPlugin(ScrollTrigger);

export default function ValidexLanding({ onLaunch, onFileAccepted }) {
  const landingRef = useRef(null);

  useEffect(() => {
    const handleDone = () => {
      ScrollTrigger.refresh();
    };
    window.addEventListener('preloader:done', handleDone);

    return () => {
      window.removeEventListener('preloader:done', handleDone);
      // Kill only ScrollTriggers whose trigger element is inside this landing page
      ScrollTrigger.getAll().forEach(t => {
        if (t.trigger && landingRef.current && landingRef.current.contains(t.trigger)) {
          t.kill();
        }
      });
    };
  }, []);

  return (
    <div className="validex-cinematic" ref={landingRef}>
      <Preloader />
      <SmoothScroll>
        <Header onLaunch={onLaunch} />
        <HeroSection onLaunch={onLaunch} />
        <ScrollTransition />
        <AuditModules />
        <WorkflowSection />
        <ProductDemo onLaunch={onLaunch} onFileAccepted={onFileAccepted} />
        <FinalCTA onLaunch={onLaunch} />
      </SmoothScroll>
    </div>
  );
}
