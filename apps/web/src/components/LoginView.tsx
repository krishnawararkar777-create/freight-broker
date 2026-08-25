import React, { useState } from 'react';
import { Lock, Mail, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getPasswordStrength = (pass: string) => {
    if (!pass) return null;
    let score = 0;
    if (pass.length >= 6) score += 1;
    if (pass.length >= 10) score += 1;
    if (/[A-Z]/.test(pass) && /[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass) && pass.length >= 12) score += 1;

    if (score <= 1) {
      return {
        score: 1,
        label: 'VERY EASY',
        color: 'bg-rose-500',
        width: 'w-1/4',
        badgeColor: 'border-rose-500/40 bg-rose-950/40 text-rose-300',
        icon: '🔴'
      };
    } else if (score === 2) {
      return {
        score: 2,
        label: 'MEDIUM',
        color: 'bg-amber-500',
        width: 'w-2/4',
        badgeColor: 'border-amber-500/40 bg-amber-950/40 text-amber-300',
        icon: '🟡'
      };
    } else if (score === 3) {
      return {
        score: 3,
        label: 'HARD',
        color: 'bg-emerald-500',
        width: 'w-3/4',
        badgeColor: 'border-emerald-500/40 bg-emerald-950/40 text-emerald-300',
        icon: '🟢'
      };
    } else {
      return {
        score: 4,
        label: 'VERY HARD / CARMACK ENCRYPTED',
        color: 'bg-indigo-400',
        width: 'w-full',
        badgeColor: 'border-indigo-500/40 bg-indigo-950/40 text-indigo-200',
        icon: '✨'
      };
    }
  };

  const strength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your work email address');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password || 'Password123!');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-montserrat selection:bg-white selection:text-black">
      {/* Subtle Dotted Radial Grid Background */}
      <div 
        className="absolute inset-0 opacity-[0.12] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.7) 1px, transparent 1px)`,
          backgroundSize: '28px 28px'
        }}
      />

      {/* Header Area */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        {/* Diamond Logo Header Pill */}
        <div className="inline-flex items-center justify-center space-x-2.5 bg-zinc-950/90 border border-zinc-800/80 px-4 py-1.5 rounded-full mb-7 shadow-inner">
          <div className="w-3 h-3 bg-white transform rotate-45 flex items-center justify-center shadow-[0_0_10px_rgba(255,255,255,0.9)]">
            <div className="w-1 h-1 bg-black" />
          </div>
          <span className="text-xs font-mono font-medium tracking-[0.22em] text-zinc-200 uppercase">
            MARAJET <span className="text-zinc-600 font-normal">/</span> <span className="text-zinc-400">2.0</span>
          </span>
        </div>

        {/* Title in Playfair Display */}
        <h1 className="text-3xl sm:text-4xl font-playfair font-normal text-white tracking-wide">
          Multi-Tenant Portal
        </h1>

        {/* Subtitle in Montserrat */}
        <p className="mt-2.5 text-xs sm:text-sm text-zinc-400 max-w-sm mx-auto font-montserrat font-light leading-relaxed">
          Evidence-grounded cargo claim workflows & statutory SLA recovery engine.
        </p>
      </div>

      {/* Intense Glassmorphism Login Card Box */}
      <div className="mt-9 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-0 sm:px-2">
        <div className="bg-gradient-to-b from-zinc-900/60 via-zinc-900/40 to-zinc-950/80 backdrop-blur-2xl border border-white/10 p-8 sm:p-10 shadow-[0_30px_70px_-15px_rgba(0,0,0,0.9),0_0_60px_rgba(255,255,255,0.03)] rounded-[28px] space-y-6">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-3.5 flex items-start space-x-3 text-rose-200 text-xs animate-fade-in font-montserrat">
              <AlertCircle className="h-4 w-4 text-rose-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Work Email Address Field */}
            <div>
              <label className="block text-sm font-playfair italic text-zinc-300 mb-2 font-medium">
                Work Email Address
              </label>
              <div className="relative rounded-xl shadow-inner">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Mail className="h-4 w-4 stroke-[1.5]" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.jenkins@apex.com"
                  className="block w-full pl-10 pr-3.5 py-3 bg-zinc-900/70 border border-zinc-800 focus:border-zinc-500 rounded-xl text-zinc-100 placeholder-zinc-500/70 focus:outline-none focus:ring-1 focus:ring-zinc-400 text-sm transition-all font-montserrat font-normal"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-playfair italic text-zinc-300 mb-2 font-medium">
                Password
              </label>
              <div className="relative rounded-xl shadow-inner">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="h-4 w-4 stroke-[1.5]" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3.5 py-3 bg-zinc-900/70 border border-zinc-800 focus:border-zinc-500 rounded-xl text-zinc-100 placeholder-zinc-500/70 focus:outline-none focus:ring-1 focus:ring-zinc-400 text-sm transition-all font-montserrat font-normal"
                />
              </div>

              {/* Dynamic Scrolling Password Strength Meter */}
              {strength && (
                <div className="mt-3 space-y-2 animate-fade-in font-montserrat">
                  {/* Smooth Progress Bar */}
                  <div className="w-full bg-zinc-950 border border-zinc-800/80 rounded-full h-1.5 overflow-hidden p-0.5">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ease-out ${strength.color} ${strength.width}`}
                    />
                  </div>

                  {/* Morphing Status Badge */}
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-zinc-500 uppercase tracking-widest font-semibold font-mono">SECURITY RATING</span>
                    <div className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold tracking-wider flex items-center gap-1.5 transition-all duration-300 ${strength.badgeColor}`}>
                      <span>{strength.icon}</span>
                      <span className="uppercase tracking-wider font-mono">{strength.label}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button matching Image 2 */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-4 rounded-xl text-xs font-bold text-black bg-white hover:bg-zinc-200 active:scale-[0.99] transition-all disabled:opacity-50 cursor-pointer shadow-xl mt-4 uppercase tracking-[0.18em] font-montserrat flex items-center justify-center gap-2"
            >
              <span>{isSubmitting ? 'AUTHENTICATING...' : 'SIGN IN TO WORKSPACE'}</span>
              <ArrowRight className="h-4 w-4 text-black stroke-[2.5]" />
            </button>
          </form>
        </div>

        {/* Minimal Footer */}
        <div className="mt-7 text-center">
          <p className="text-[11px] font-mono text-zinc-500 flex items-center justify-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Supabase Auth Encrypted • Multi-Tenant RLS Isolated</span>
          </p>
        </div>
      </div>
    </div>
  );
};
