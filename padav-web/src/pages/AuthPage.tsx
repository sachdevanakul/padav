import { useState } from 'react'
import type { ReactNode } from 'react'
import { ArrowLeft, Eye, EyeOff, GraduationCap, LockKeyhole, Mail, UserRound } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema, registerSchema, type LoginValues, type RegisterValues } from '../schemas/auth'
import { api } from '../services/api'
import { authStore } from '../store/auth'

type Props = { mode: 'login' | 'register' }

export default function AuthPage({ mode }: Props) {
  const [visible, setVisible] = useState(false)
  const navigate = useNavigate()
  const setTokens = authStore((state) => state.setTokens)
  const setUser = authStore((state) => state.setUser)
  const isRegister = mode === 'register'
  const loginForm = useForm<LoginValues>({ resolver: zodResolver(loginSchema), defaultValues: { email: '', password: '' } })
  const registerForm = useForm<RegisterValues>({ resolver: zodResolver(registerSchema), defaultValues: { full_name: '', email: '', password: '', confirm_password: '' } })
  const mutation = useMutation({
    mutationFn: async () => {
      const values = isRegister ? registerForm.getValues() : loginForm.getValues()
      const tokens = isRegister
        ? await api.register({ email: values.email, password: values.password, full_name: (values as RegisterValues).full_name })
        : await api.login({ email: values.email, password: values.password })
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await api.me()
      setUser(user)
      return user
    },
    onSuccess: () => navigate('/exams'),
  })
  const form = isRegister ? registerForm : loginForm
  const emailInput = isRegister ? registerForm.register('email') : loginForm.register('email')
  const passwordInput = isRegister ? registerForm.register('password') : loginForm.register('password')

  return <div className="auth-page"><div className="auth-visual"><Link to="/" className="brand"><span className="brand-mark"><GraduationCap size={21} /></span><span>PADAV<small>YOUR AMBITION. YOUR ADVANTAGE.</small></span></Link><div className="auth-visual-content"><div className="auth-orb"><LockKeyhole size={42} /></div><p className="eyebrow">YOUR JOURNEY, YOUR PACE</p><h2>Make every<br />study hour count.</h2><p>Build momentum with a plan that keeps your ambition in motion.</p><div className="auth-proof"><span>01</span><i /><span>FOCUSED PREPARATION</span></div></div><div className="auth-visual-foot">© 2026 Padav Learning</div></div>
    <div className="auth-panel"><Link className="back-link" to="/onboarding"><ArrowLeft size={16} /> Back</Link><div className="auth-form-wrap"><p className="eyebrow">{isRegister ? 'BEGIN WITH A CLEAR GOAL' : 'WELCOME BACK'}</p><h1>{isRegister ? 'Create your account' : 'Good to see you again'}</h1><p className="muted">{isRegister ? 'A focused routine starts with one small step.' : 'Sign in to pick up where you left off.'}</p>
      <form className="auth-form" onSubmit={form.handleSubmit(() => mutation.mutate())}>
        {isRegister && <Field label="Full name" icon={<UserRound size={17} />} error={registerForm.formState.errors.full_name?.message}><input autoComplete="name" placeholder="Your name" {...registerForm.register('full_name')} /></Field>}
        <Field label="Email address" icon={<Mail size={17} />} error={form.formState.errors.email?.message}><input autoComplete="email" type="email" placeholder="you@example.com" {...emailInput} /></Field>
        <Field label="Password" icon={<LockKeyhole size={17} />} error={form.formState.errors.password?.message}><input autoComplete={isRegister ? 'new-password' : 'current-password'} type={visible ? 'text' : 'password'} placeholder="At least 8 characters" {...passwordInput} /><button type="button" className="field-action" aria-label={visible ? 'Hide password' : 'Show password'} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={17} /> : <Eye size={17} />}</button></Field>
        {isRegister && <Field label="Confirm password" icon={<LockKeyhole size={17} />} error={registerForm.formState.errors.confirm_password?.message}><input autoComplete="new-password" type={visible ? 'text' : 'password'} placeholder="Repeat your password" {...registerForm.register('confirm_password')} /></Field>}
        {!isRegister && <div className="form-between"><label className="check-label"><input type="checkbox" /> Remember me</label><span className="muted">Forgot password?</span></div>}
        {mutation.error && <div role="alert" className="form-error">{mutation.error.message}</div>}
        <button className="button button-primary submit-button" type="submit" disabled={mutation.isPending}>{mutation.isPending ? <span className="spinner" /> : isRegister ? 'Create account' : 'Sign in'}<span aria-hidden="true">→</span></button>
      </form>
      <p className="auth-switch">{isRegister ? 'Already have an account?' : 'New to Padav?'} <Link to={isRegister ? '/auth/login' : '/auth/register'}>{isRegister ? 'Sign in' : 'Create an account'}</Link></p>
      <p className="terms-note">By continuing, you agree to our <a href="#terms">Terms of Service</a> and <a href="#privacy">Privacy Policy</a>.</p>
    </div></div></div>
}

function Field({ label, icon, error, children }: { label: string; icon: ReactNode; error?: string; children: ReactNode }) {
  return <label className="form-field"><span>{label}</span><span className={`input-wrap ${error ? 'has-error' : ''}`}><i>{icon}</i>{children}</span>{error && <small className="field-error">{error}</small>}</label>
}
