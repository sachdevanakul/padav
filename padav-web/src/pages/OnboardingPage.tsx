import { useState } from 'react'
import { ArrowLeft, ArrowRight, Check, GraduationCap, Languages, Sparkles, Target, Trophy } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { preferencesStore } from '../store/preferences'
import { Button } from '../components/ui/Button'

const slides = [
  { icon: GraduationCap, kicker: 'A smarter way to prepare', title: 'Learn smart.\nAchieve more.', body: 'Your personal learning companion for competitive examinations.', glow: 'violet' },
  { icon: Target, kicker: 'Everything in one place', title: 'Prepare. Practice.\nExcel.', body: 'Structured courses, focused practice, and mock exams built around your goals.', glow: 'blue' },
  { icon: Trophy, kicker: 'Your goal, in focus', title: 'Your success.\nOur mission.', body: 'Build a consistent routine, understand your progress, and move closer to your dream rank.', glow: 'mint' },
]

export default function OnboardingPage() {
  const [step, setStep] = useState(0)
  const navigate = useNavigate()
  const language = preferencesStore((state) => state.language)
  const setLanguage = preferencesStore((state) => state.setLanguage)
  const slide = slides[step]
  const Icon = slide.icon
  function finish() { localStorage.setItem('padav-onboarded', 'true'); navigate('/auth/register') }

  return <div className="onboarding-page">
    <header className="onboarding-top"><Link to="/" className="brand"><span className="brand-mark"><GraduationCap size={21} /></span><span>PADAV<small>YOUR AMBITION. YOUR ADVANTAGE.</small></span></Link><div className="onboarding-actions"><button className="language-pill" onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}><Languages size={15} />{language === 'en' ? 'English' : 'हिन्दी'}</button><Link to="/auth/login" className="signin-link">Already a member? <b>Sign in</b></Link></div></header>
    <div className="onboarding-body">
      <div className="onboarding-copy">
        <AnimatePresence mode="wait"><motion.div key={step} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: .24 }}>
          <div className="eyebrow"><Sparkles size={14} />{slide.kicker}</div><h1>{slide.title.split('\n').map((line) => <span key={line}>{line}<br /></span>)}</h1><p className="onboarding-description">{slide.body}</p>
        </motion.div></AnimatePresence>
        <div className="onboarding-bottom"><div className="pagination">{slides.map((item, i) => <button key={item.title} aria-label={`Go to step ${i + 1}`} onClick={() => setStep(i)} className={step === i ? 'current' : ''} />)}</div><div className="onboarding-controls">{step > 0 && <Button variant="ghost" aria-label="Previous step" onClick={() => setStep(step - 1)} icon={<ArrowLeft size={17} />} />}{step < 2 ? <Button onClick={() => setStep(step + 1)}>Continue <ArrowRight size={17} /></Button> : <Button onClick={finish}>Start your journey <ArrowRight size={17} /></Button>}</div></div>
      </div>
      <div className={`onboarding-art art-${slide.glow}`}><div className="art-grid" /><div className="art-glow" /><div className="art-ring ring-one" /><div className="art-ring ring-two" /><div className="art-ring ring-three" /><motion.div className="hero-emblem" key={step} initial={{ scale: .84, rotate: -8, opacity: 0 }} animate={{ scale: 1, rotate: 0, opacity: 1 }} transition={{ type: 'spring', stiffness: 160, damping: 18 }}><Icon size={92} strokeWidth={1.15} /></motion.div><span className="float-chip chip-one"><Check size={14} /> Study plan ready</span><span className="float-chip chip-two"><span className="tiny-spark">✦</span> Your next chapter</span><span className="art-caption">A little progress each day adds up.</span></div>
    </div>
    <button className="skip-onboarding" onClick={finish}>Skip for now</button>
  </div>
}
