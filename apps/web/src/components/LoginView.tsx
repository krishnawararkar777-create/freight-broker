import React, { useState } from 'react';
import { Shield, Lock, Mail, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';
import { useAuth, DEMO_USERS } from '../context/AuthContext';

export const LoginView: React.FC = () => {
  const { login, loginAsDemoUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedTenantTab, setSelectedTenantTab] = useState<'broker' | 'shipper' | 'carrier'>('broker');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your work email address');
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

  const tenantUsers = DEMO_USERS.filter(u => u.organization.type === selectedTenantTab);

  return (
    <div className="min-h-screen bg-black flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans selection:bg-white selection:text-black">
      {/* Sleek Minimalist Subtle Grid (No AI slop cyan/rainbow blobs) */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }}
      />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        {/* Crisp Monochromatic Brand Pill */}
        <div className="inline-flex items-center justify-center space-x-2 bg-zinc-950 border border-zinc-800 px-3.5 py-1.5 rounded-full mb-6 shadow-sm">
          <Shield className="h-4 w-4 text-zinc-100" />
          <span className="text-xs font-semibold tracking-wider text-zinc-300 uppercase font-mono">
            MARAJET PLATFORM
          </span>
          <span className="text-zinc-600">/</span>
          <span className="text-[11px] font-mono text-zinc-400">
            v4.0
          </span>
        </div>

        <h1 className="text-3xl font-bold text-white tracking-tight sm:text-4xl">
          Multi-Tenant Portal
        </h1>
        <p className="mt-2 text-sm text-zinc-400 max-w-sm mx-auto">
          Evidence-grounded cargo claim workflows & statutory SLA recovery engine.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-0 sm:px-2">
        <div className="bg-zinc-950 border border-zinc-800/80 p-6 sm:p-8 shadow-2xl rounded-2xl space-y-6">
          {error && (
            <div className="bg-red-950/40 border border-red-800/60 rounded-xl p-3.5 flex items-start space-x-3 text-red-200 text-xs animate-fade-in">
              <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5 font-mono">
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
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-zinc-900/70 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-sm transition-all font-sans"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider font-mono">
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
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-zinc-900/70 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white text-sm transition-all font-sans"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 rounded-xl text-sm font-semibold text-black bg-white hover:bg-zinc-200 active:scale-[0.99] transition-all disabled:opacity-50 cursor-pointer shadow-sm mt-2"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="h-4 w-4 text-black" />
            </button>
          </form>

          {/* Clean Monochromatic Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase">
              <span className="bg-zinc-950 px-3 text-zinc-400 font-mono tracking-wider flex items-center space-x-1.5">
                <Sparkles className="h-3 w-3 text-zinc-400" />
                <span>Instant Demo Access</span>
              </span>
            </div>
          </div>

          {/* Segmented Tenant Tab Control */}
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-1 p-1 bg-zinc-900/80 border border-zinc-800 rounded-xl">
              <button
                type="button"
                onClick={() => setSelectedTenantTab('broker')}
                className={`py-1.5 px-2 text-[11px] font-medium rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'broker'
                    ? 'bg-white text-black font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                🏢 Broker
              </button>
              <button
                type="button"
                onClick={() => setSelectedTenantTab('shipper')}
                className={`py-1.5 px-2 text-[11px] font-medium rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'shipper'
                    ? 'bg-white text-black font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                🏭 Shipper
              </button>
              <button
                type="button"
                onClick={() => setSelectedTenantTab('carrier')}
                className={`py-1.5 px-2 text-[11px] font-medium rounded-lg transition-all cursor-pointer text-center ${
                  selectedTenantTab === 'carrier'
                    ? 'bg-white text-black font-semibold shadow-sm'
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

              <div className="grid grid-cols-1 gap-1.5">
                {tenantUsers.map(u => (
                  <button
                    key={u.id}
                    onClick={() => handleSelectDemoUser(u.email)}
                    className="flex items-center justify-between p-2.5 bg-zinc-900/50 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-600 rounded-xl text-left transition-all group cursor-pointer"
                  >
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-semibold text-white shrink-0 group-hover:bg-zinc-700 transition-colors">
                        {u.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-zinc-200 group-hover:text-white truncate">
                          {u.name}
                        </div>
                        <div className="text-[11px] text-zinc-400 font-mono truncate">
                          {u.email}
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-zinc-900 border border-zinc-700/80 text-zinc-300 shrink-0 ml-2">
                      {u.role}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Minimal Footer */}
        <div className="mt-6 text-center">
          <p className="text-[11px] font-mono text-zinc-500 flex items-center justify-center space-x-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Multi-Tenant RLS Isolated • 49 CFR § 370 Grounded</span>
          </p>
        </div>
      </div>
    </div>
  );
};

