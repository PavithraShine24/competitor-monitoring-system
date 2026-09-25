import { ArrowRight, LockKeyhole, Mail, Radar } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { api } from './api';
import './login.css';

type LoginProps = {
  onAuthenticated: (token: string) => void;
};

export default function Login({ onAuthenticated }: LoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const response = await api.login(email, password);
      onAuthenticated(response.access_token);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Unable to sign in. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="login-shell">
      <section className="login-card" aria-labelledby="login-title">
        <div className="login-brand">
          <span className="brand-mark"><Radar size={18} /></span>
          <div>
            <strong>Signalwatch</strong>
            <small>content intelligence</small>
          </div>
        </div>
        <div className="login-heading">
          <p className="eyebrow">PRIVATE WORKSPACE</p>
          <h1 id="login-title">Welcome back.</h1>
          <p>Sign in to monitor the signals that matter.</p>
        </div>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="email">Email address</label>
          <div className="login-input">
            <Mail size={17} aria-hidden="true" />
            <input id="email" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required />
          </div>
          <label htmlFor="password">Password</label>
          <div className="login-input">
            <LockKeyhole size={17} aria-hidden="true" />
            <input id="password" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" minLength={8} required />
          </div>
          {error && <p className="login-error" role="alert">{error}</p>}
          <button className="login-submit" type="submit" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
            {!submitting && <ArrowRight size={16} />}
          </button>
        </form>
      </section>
    </main>
  );
}
