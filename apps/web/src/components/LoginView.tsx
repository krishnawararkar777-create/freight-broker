import React, { useState } from 'react';
import { Shield, Lock, Mail, ArrowRight, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { useAuth, DEMO_USERS } from '../context/AuthContext';

export const LoginView: React.FC = () => {
  const { login, loginAsDemoUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedTenantTab, setSelectedTenantTab] = useState<'broker' | 'shipper' | 'carrier'>('broker');

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
        badgeColor: 'border-rose-500/40 bg-rose-950/40 text-rose-400',
        icon: '🔴'
      };
    } else if (score === 2) {
      return {
        score: 2,
        label: 'MEDIUM',
        color: 'bg-amber-500',
        width: 'w-2/4',
        badgeColor: 'border-amber-500/40 bg-amber-950/40 text-amber-400',
        icon: '🟡'
      };
    } else if (score === 3) {
      return {
        score: 3,
        label: 'HARD',
        color: 'bg-emerald-500',
        width: 'w-3/4',
        badgeColor: 'border-emerald-500/40 bg-emerald-950/40 text-emerald-400',
        icon: '🟢'
      };
    } else {
      return {
        score: 4,
        label: 'VERY HARD / CARMACK ENCRYPTED',
        color: 'bg-indigo-400',
        width: 'w-full',
        badgeColor: 'border-indigo-500/40 bg-indigo-950/40 text-indigo-300',
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

  const handleSelectDemoUser = (userEmail: string) => {
    setError(null);
    loginAsDemoUser(userEmail);
  };

  const tenantUsers = DEMO_USERS.filter(u => u.organization.type === selectedTenantTab);

  return (
    <div className="min-h-screen bg-black flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans selection:bg-white selection:text-black">
      {/* Subtle Grid Pattern Background */}
      <div 
        className="absolute inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }}
      />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        {/* Monochromatic Brand Header Pill */}
        <div className="inline-flex items-center justify-center space-x-2 bg-zinc-950 border border-zinc-800 px-4 py-1.5 rounded-full mb-6 shadow-md">
          <Shield className="h-4 w-4 text-zinc-100" />
          <span className="text-xs font-semibold tracking-wider text-zinc-200 uppercase font-mono">
            MARAJET PLATFORM
          </span>
          <span className="text-zinc-600">/</span>
          <span className="text-[11px] font-mono text-zinc-400">
            v4.0
          </span>
        </div>

        <h1 className="text-3xl font-bold text-white tracking-tight sm:text-4xl font-montserrat">
          Multi-Tenant Portal
        </h1>
        <p className="mt-2 text-xs sm:text-sm text-zinc-400 max-w-sm mx-auto font-montserrat">
          Evidence-grounded cargo claim workflows & statutory SLA recovery engine.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-0 sm:px-2">
        <div className="bg-zinc-950/90 border border-zinc-800/90 p-6 sm:p-8 shadow-2xl rounded-2xl space-y-6 backdrop-blur-sm">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-3.5 flex items-start space-x-3 text-rose-200 text-xs animate-fade-in">
              <AlertCircle className="h-4 w-4 text-rose-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-bold text-zinc-400 uppercase tracking-widest mb-1.5 font-mono">
                Work Email Address
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.jenkins@apex.com"
                  className="block w-full pl-10 pr-3.5 py-3 bg-zinc-900/80 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-sm transition-all font-sans"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-[11px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
                  Password
                </label>
              </div>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3.5 py-3 bg-zinc-900/80 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-sm transition-all font-sans"
                />
              </div>

              {/* Dynamic Scrolling Password Strength Meter */}
              {strength && (
                <div className="mt-3 space-y-2 animate-fade-in font-mono">
                  {/* Progress Bar Track */}
                  <div className="w-full bg-zinc-900 border border-zinc-800 rounded-full h-1.5 overflow-hidden p-0.5">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ease-out ${strength.color} ${strength.width}`}
                    />
                  </div>

                  {/* Scrolling / Morphing Badge Indicator */}
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-zinc-500 uppercase tracking-widest font-semibold">PASSWORD SECURITY</span>
                    <div className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold tracking-wider flex items-center gap-1.5 transition-all duration-300 ${strength.badgeColor}`}>
                      <span>{strength.icon}</span>
                      <span className="uppercase tracking-widest">{strength.label}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center space-x-2 py-3 px-4 rounded-xl text-sm font-bold text-black bg-white hover:bg-zinc-200 active:scale-[0.99] transition-all disabled:opacity-50 cursor-pointer shadow-lg mt-3 uppercase tracking-wider font-mono"
            >
              <span>{isSubmitting ? 'AUTHENTICATING...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="h-4 w-4 text-black" />
            </button>
          </form>

          {/* Clean Monochromatic Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase">
              <span className="bg-zinc-950 px-3 text-zinc-400 font-mono tracking-widest flex items-center space-x-1.5">
                <Sparkles className="h-3 w-3 text-zinc-400" />
                <span>Instant Demo Access</span>
              </span>
            </div>
          </div>

          {/* Segmented Tenant Tab Control */}
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-1 p-1 bg-zinc-900/90 border border-zinc-800 rounded-xl">
              <button
                type="button"
                onClick={() => setSelectedTenantTab('broker')}
                className={`py-2 px-2 text-[11px] font-bold uppercase font-mono rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'broker'
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                🏢 Broker
              </button>
              <button
                type="button"
                onClick={() => setSelectedTenantTab('shipper')}
                className={`py-2 px-2 text-[11px] font-bold uppercase font-mono rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'shipper'
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                🏭 Shipper
              </button>
              <button
                type="button"
                onClick={() => setSelectedTenantTab('carrier')}
                className={`py-2 px-2 text-[11px] font-bold uppercase font-mono rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'carrier'
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                🚚 Carrier
              </button>
            </div>

            {/* Tenant User Quick Select Buttons */}
            <div className="space-y-2 pt-1">
              <div className="text-[11px] font-mono text-zinc-400 flex items-center justify-between px-1">
                <span>
                  {selectedTenantTab === 'broker' && 'Apex Freight Brokers (Broker)'}
                  {selectedTenantTab === 'shipper' && 'Apex Advanced Electronics (Shipper)'}
                  {selectedTenantTab === 'carrier' && 'Swift Line Logistics (Carrier)'}
                </span>
                <span className="text-zinc-600">Select Role ↵</span>
              </div>

              <div className="grid grid-cols-1 gap-2">
                {tenantUsers.map(u => (
                  <button
                    key={u.id}
                    onClick={() => handleSelectDemoUser(u.email)}
                    className="flex items-center justify-between p-3 bg-zinc-900/60 hover:bg-zinc-800/90 border border-zinc-800 hover:border-zinc-700 rounded-xl text-left transition-all group cursor-pointer"
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-white shrink-0 group-hover:bg-zinc-700 transition-colors font-mono">
                        {u.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-zinc-200 group-hover:text-white truncate font-montserrat">
                          {u.name}
                        </div>
                        <div className="text-[11px] text-zinc-400 font-mono truncate">
                          {u.email}
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 shrink-0 ml-2">
                      {u.role}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Minimal Security Footer */}
        <div className="mt-6 text-center">
          <p className="text-[11px] font-mono text-zinc-500 flex items-center justify-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Supabase Auth Encrypted • Multi-Tenant RLS Isolated</span>
          </p>
        </div>
      </div>
    </div>
  );
};
