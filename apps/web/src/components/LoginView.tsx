import React, { useState } from 'react';
import { ShieldCheck, Lock, Mail, ArrowRight, Building2, UserCheck, AlertCircle, Sparkles } from 'lucide-react';
import { useAuth, DEMO_USERS } from '../context/AuthContext';

export const LoginView: React.FC = () => {
  const { login, loginAsDemoUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
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

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Dynamic Background Glow & Grid Overlay */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-cyan-600/20 via-blue-600/10 to-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-30 pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <div className="inline-flex items-center justify-center space-x-3 bg-slate-900/80 border border-slate-800 backdrop-blur-md px-4 py-2 rounded-full mb-6 shadow-xl shadow-cyan-950/20">
          <ShieldCheck className="h-6 w-6 text-cyan-400 animate-pulse" />
          <span className="text-sm font-semibold tracking-wide bg-gradient-to-r from-cyan-400 via-blue-300 to-emerald-400 bg-clip-text text-transparent uppercase font-mono">
            Algolyra / Marajet Platform
          </span>
        </div>

        <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Multi-Tenant Portal Login
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Sign in to access evidence-grounded cargo claim workflows & statutory SLA engines.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800/80 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 space-y-6">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3.5 flex items-start space-x-3 text-rose-300 text-xs">
              <AlertCircle className="h-4 w-4 text-rose-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Work Email Address
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.jenkins@apex.com"
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-sm transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-sm transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center space-x-2 py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-all disabled:opacity-50 cursor-pointer"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-3 text-slate-500 font-mono flex items-center space-x-1">
                <Sparkles className="h-3 w-3 text-cyan-400" />
                <span>Multi-Tenant Demo Quick Select</span>
              </span>
            </div>
          </div>

          {/* Multi-Tenant Quick Demo Switcher */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-400 flex items-center space-x-1.5">
              <Building2 className="h-3.5 w-3.5 text-cyan-400" />
              <span>Org A: Apex Freight Brokers (Broker Tenant)</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {DEMO_USERS.filter(u => u.organization.id === 'org-apex-001').map(u => (
                <button
                  key={u.id}
                  onClick={() => handleSelectDemoUser(u.email)}
                  className="flex items-center justify-between p-2.5 bg-slate-950/60 hover:bg-cyan-950/30 border border-slate-800 hover:border-cyan-500/50 rounded-xl text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center space-x-2.5">
                    <UserCheck className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">{u.name}</div>
                      <div className="text-[10px] text-slate-400">{u.email}</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {u.role}
                  </span>
                </button>
              ))}
            </div>

            <div className="text-xs font-semibold text-slate-400 flex items-center space-x-1.5 pt-2">
              <Building2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Org B: Swift Line Logistics (Carrier Tenant)</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {DEMO_USERS.filter(u => u.organization.id === 'org-swift-002').map(u => (
                <button
                  key={u.id}
                  onClick={() => handleSelectDemoUser(u.email)}
                  className="flex items-center justify-between p-2.5 bg-slate-950/60 hover:bg-emerald-950/30 border border-slate-800 hover:border-emerald-500/50 rounded-xl text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center space-x-2.5">
                    <UserCheck className="h-4 w-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="text-xs font-medium text-slate-200">{u.name}</div>
                      <div className="text-[10px] text-slate-400">{u.email}</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {u.role}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
