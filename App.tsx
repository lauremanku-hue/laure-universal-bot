import React, { useState, useEffect, useRef } from 'react';
import { 
  Copy, Check, Terminal, Info, Link as LinkIcon, Lock, AlertCircle, Sparkles,
  Send, Facebook, ShieldAlert, Share2, HelpCircle, Activity, ChevronRight
} from 'lucide-react';
import { initializeChat, sendMessageStream } from './services/geminiService';
import { Role, Message } from './types';

function App() {
  const [activeTab, setActiveTab] = useState<'config' | 'terminal' | 'diagnose' | 'deploy'>('config');
  const [selectedChannel, setSelectedChannel] = useState<'messenger' | 'instagram' | 'whatsapp' | 'telegram' | 'youtube'>('messenger');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  const [ngrokUrl, setNgrokUrl] = useState("https://interzonal-unanchored-tierra.ngrok-free.dev");
  const [verifyToken, setVerifyToken] = useState("laure_secret");

  useEffect(() => {
    initializeChat();
    setMessages([{
      id: '1',
      role: Role.MODEL,
      content: "### 🆘 Pourquoi cette étape est nécessaire ?\n\nImagine que tu donnes ton numéro de téléphone à un ami : c'est l'**URL de rappel**. Le **Jeton** est comme un code secret pour être sûr que c'est bien Facebook qui t'appelle.\n\nSi ça ne marche pas, utilise l'onglet **'DIAGNOSTIC'** en haut, je vais t'aider à trouver le problème.",
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    const userMsg: Message = { id: Date.now().toString(), role: Role.USER, content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    const modelMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: modelMsgId, role: Role.MODEL, content: '', timestamp: new Date() }]);
    try {
      let fullContent = '';
      await sendMessageStream(input, (chunk) => {
        fullContent += chunk;
        setMessages(prev => prev.map(m => m.id === modelMsgId ? { ...m, content: fullContent } : m));
      });
    } catch (err) {
      setMessages(prev => [...prev, { id: 'err', role: Role.MODEL, content: "Erreur technique IA.", timestamp: new Date(), isError: true }]);
    } finally { setIsTyping(false); }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30">
      <header className="p-4 border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-xl sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/20">
            <Share2 className="text-white" size={22} />
          </div>
          <div>
            <h1 className="text-md font-black text-white tracking-tighter italic uppercase">Laure<span className="text-indigo-500">.</span>Support</h1>
            <p className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Aide à l'intégration Webhook</p>
          </div>
        </div>
        
        <nav className="flex bg-slate-900/50 p-1 rounded-full border border-slate-800">
          {[
            { id: 'messenger', label: 'Messenger', icon: <Facebook size={12}/> },
            { id: 'instagram', label: 'Instagram', icon: <Sparkles size={12}/> },
            { id: 'whatsapp', label: 'WhatsApp', icon: <Share2 size={12}/> },
            { id: 'telegram', label: 'Telegram', icon: <Send size={12}/> },
            { id: 'youtube', label: 'YouTube', icon: <Activity size={12}/> }
          ].map((ch) => (
            <button 
              key={ch.id}
              onClick={() => setSelectedChannel(ch.id as any)}
              className={`px-3 py-1.5 rounded-full text-[9px] font-black transition-all uppercase tracking-wider flex items-center gap-2 ${selectedChannel === ch.id ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30' : 'text-slate-500 hover:text-white'}`}
            >
              {ch.icon} {ch.label}
            </button>
          ))}
        </nav>

        <nav className="flex bg-slate-900/50 p-1 rounded-full border border-slate-800">
          {[
            { id: 'config', label: 'Configuration', icon: <LinkIcon size={12}/> },
            { id: 'diagnose', label: 'Diagnostic', icon: <Activity size={12}/> },
            { id: 'deploy', label: 'Mise en ligne', icon: <ShieldAlert size={12}/> },
            { id: 'terminal', label: 'Logs', icon: <Terminal size={12}/> }
          ].map((tab) => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-full text-[10px] font-black transition-all uppercase tracking-wider flex items-center gap-2 ${activeTab === tab.id ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-white'}`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-0 overflow-hidden">
        {/* Colonne de gauche : Explications */}
        <aside className="lg:col-span-3 border-r border-slate-800 p-6 space-y-6 bg-[#020617] overflow-y-auto hidden lg:block">
          <div className="space-y-4">
             <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] flex items-center gap-2">
               <Activity size={14} /> État du Système
             </h2>
             <div className="space-y-2">
               <HealthItem label="Serveur Python" status="online" />
               <HealthItem label="Worker Celery" status="online" />
               <HealthItem label="Redis Cache" status="online" />
               <HealthItem label="Ngrok Tunnel" status="online" />
             </div>
          </div>

          <div className="space-y-4">
             <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] flex items-center gap-2">
               <HelpCircle size={14} /> Est-ce nécessaire ?
             </h2>
             <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl space-y-3">
               <p className="text-[11px] text-slate-300 font-bold leading-relaxed">
                 OUI ! C'est le seul moyen pour Meta de savoir que ton bot existe.
               </p>
               <p className="text-[10px] text-slate-500 leading-relaxed">
                 Sans cette étape, ton code tourne dans le vide et Facebook ne sait pas où envoyer les messages.
               </p>
             </div>
          </div>

          <div className="p-4 bg-rose-500/5 border border-rose-500/20 rounded-2xl">
            <h3 className="text-[10px] font-bold text-rose-400 flex items-center gap-2 mb-2 uppercase tracking-widest">
              <ShieldAlert size={14} /> Attention
            </h3>
            <p className="text-[10px] text-slate-400">
              Ne ferme jamais ton terminal Ngrok pendant que tu fais la configuration sur Facebook !
            </p>
          </div>
        </aside>

        {/* Zone centrale : Action */}
        <section className="lg:col-span-5 flex flex-col bg-[#020617] border-r border-slate-800 overflow-y-auto">
          {activeTab === 'config' ? (
            <div className="p-8 space-y-8 animate-fade-in">
              <div className="space-y-2">
                <h2 className="text-2xl font-black text-white italic tracking-tight">
                  Setup {selectedChannel.charAt(0).toUpperCase() + selectedChannel.slice(1)}
                </h2>
                <p className="text-xs text-slate-400">
                  {selectedChannel === 'youtube' 
                    ? "YouTube est utilisé pour le téléchargement de vidéos via les autres bots." 
                    : `Copie ces valeurs dans ton portail ${selectedChannel === 'telegram' ? 'BotFather' : 'Meta Developers'}.`}
                </p>
              </div>

              <div className="p-6 bg-slate-900/50 border border-indigo-500/30 rounded-3xl space-y-6 relative">
                {selectedChannel !== 'youtube' ? (
                  <>
                    <ConfigField 
                      label="URL DE RAPPEL" 
                      value={`${ngrokUrl}/webhook/${selectedChannel === 'telegram' ? 'telegram' : 'meta'}`} 
                      desc="Copie ça dans 'Callback URL'" 
                    />
                    {selectedChannel !== 'telegram' && (
                      <ConfigField label="JETON DE VÉRIFICATION" value={verifyToken} desc="Tape ça dans 'Verify Token'" />
                    )}
                    {(selectedChannel === 'instagram' || selectedChannel === 'messenger') && (
                      <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex gap-3">
                        <Lock className="text-amber-500 shrink-0" size={16} />
                        <div className="space-y-1">
                          <p className="text-[10px] font-bold text-amber-200 uppercase">Note sur le Mode Live</p>
                          <p className="text-[9px] text-amber-200/70 leading-relaxed">
                            Meta limite les webhooks en mode "Développement". Pour que n'importe qui puisse parler au bot, tu devras passer l'app en mode **Live** après avoir ajouté une Politique de Confidentialité.
                          </p>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-4">
                    <p className="text-[11px] text-slate-300">YouTube n'a pas de Webhook de chat. Le bot utilise l'API pour analyser les liens envoyés sur WhatsApp/Telegram.</p>
                    <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                      <p className="text-[10px] text-indigo-300">Fonctionnalité active : Téléchargement automatique des vidéos YouTube quand un lien est détecté.</p>
                    </div>
                  </div>
                )}
                
                <div className="pt-6 border-t border-slate-800 space-y-4">
                  <p className="text-[11px] text-slate-300 font-bold uppercase tracking-widest">Commandes de gestion :</p>
                  <div className="grid grid-cols-1 gap-2">
                     <div className="p-3 bg-black/20 border border-slate-800 rounded-xl font-mono text-[10px] text-indigo-400">/menu : Affiche le menu complet</div>
                     <div className="p-3 bg-black/20 border border-slate-800 rounded-xl font-mono text-[10px] text-emerald-400">/cours Contenu | Heure : Programme un cours</div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-4 p-4 bg-blue-500/10 border border-blue-500/20 rounded-2xl">
                <Info className="text-blue-400 shrink-0" size={18} />
                <div className="space-y-1">
                  <p className="text-[11px] font-bold text-blue-200">Conseil :</p>
                  <p className="text-[10px] text-blue-200/60 leading-relaxed">
                    Si Facebook dit "Callback verification failed", vérifie que ton terminal Ngrok affiche bien des lignes qui bougent quand tu cliques sur Valider.
                  </p>
                </div>
              </div>
            </div>
          ) : activeTab === 'diagnose' ? (
            <div className="p-8 space-y-6 animate-fade-in">
              <h2 className="text-xl font-black text-white italic">Assistant de Diagnostic</h2>
              <div className="space-y-4">
                <StepItem num="1" title="Vérifier ton Ngrok" desc="Ton terminal Ngrok doit afficher 'Forwarding' vers http://localhost:5000." status="check" />
                <StepItem num="2" title="Vérifier le Token" desc="Est-ce que tu as bien écrit 'laure_secret' sans fautes ?" status="check" />
                <StepItem num="3" title="Vérifier l'URL" desc="Pour WhatsApp et Messenger, l'URL doit finir par '/webhook/meta'." status="check" />
                <StepItem num="4" title="Base de Données" desc="Vérifie que ta base PostgreSQL est bien connectée pour le stockage des cours." status="check" />
                <div className="pt-4 border-t border-slate-800 mt-6">
                   <p className="text-[10px] text-slate-500 mb-4 uppercase font-bold tracking-widest">Outil de test forcé :</p>
                   <div className="bg-black/40 p-4 rounded-xl border border-slate-800 font-mono text-[10px]">
                      <code className="text-emerald-400">curl -I {ngrokUrl}/webhook/meta</code>
                      <p className="mt-2 text-slate-500 italic"># Si cette commande renvoie une erreur dans ton terminal, alors Ngrok est mal configuré.</p>
                   </div>
                </div>
              </div>
            </div>
          ) : activeTab === 'deploy' ? (
            <div className="p-8 space-y-8 animate-fade-in">
              <div className="space-y-2">
                <h2 className="text-2xl font-black text-white italic tracking-tight">Mise en ligne (Production)</h2>
                <p className="text-xs text-slate-400">Comment rendre ton bot accessible 24h/24 sans Ngrok.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-3xl space-y-4">
                  <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-widest">1. Backend (Python)</h3>
                  <p className="text-[10px] text-slate-400">Héberge ton code Flask sur **Render.com** ou **Railway.app**.</p>
                  <ul className="text-[10px] text-slate-500 space-y-2 list-disc ml-4">
                    <li>Connecte ton GitHub</li>
                    <li>Ajoute les variables d'environnement (.env)</li>
                    <li>Commande de lancement : <code>python laure_bot.py</code></li>
                  </ul>
                </div>
                <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-3xl space-y-4">
                  <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-widest">2. Frontend (React)</h3>
                  <p className="text-[10px] text-slate-400">Héberge cette interface sur **Vercel** ou **Netlify**.</p>
                  <ul className="text-[10px] text-slate-500 space-y-2 list-disc ml-4">
                    <li>Build automatique via GitHub</li>
                    <li>Remplace l'URL Ngrok par l'URL de ton Backend Render</li>
                  </ul>
                </div>
              </div>

              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex gap-4">
                <ShieldAlert className="text-amber-500 shrink-0" size={20} />
                <p className="text-[10px] text-amber-200/80 leading-relaxed">
                  Une fois en ligne, tu devras mettre à jour l'**URL de rappel** sur Meta et Telegram avec ton nouveau lien (ex: https://mon-bot.onrender.com/webhook/meta).
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 p-8 font-mono text-[11px] space-y-3 bg-black/40 text-slate-300">
               <p className="text-slate-500"># Simulation des logs en temps réel</p>
               <p className="text-white mt-4">[GET] /webhook/meta?hub.mode=subscribe&hub.challenge=123&hub.verify_token=laure_secret</p>
               <p className="text-emerald-500 font-bold tracking-tighter">{">>>"} RÉPONSE ENVOYÉE : 123 (HTTP 200 OK)</p>
               <p className="text-slate-500 mt-6 italic opacity-50">Si tu ne vois pas de texte vert comme ça dans ton terminal PC, c'est que Facebook n'arrive pas à toucher ton ordinateur.</p>
            </div>
          )}
        </section>

        {/* AI Assistant Area */}
        <aside className="lg:col-span-4 flex flex-col bg-[#0f172a]/20">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/30">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-indigo-400" />
              <h2 className="text-[11px] font-black uppercase tracking-widest text-white italic">Guide Laure</h2>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === Role.USER ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-2xl text-[12px] shadow-2xl ${
                  m.role === Role.USER ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700/50'
                }`}>
                  {m.content}
                </div>
              </div>
            ))}
            {isTyping && <div className="text-[10px] text-slate-500 italic animate-pulse px-3">Laure analyse ton problème...</div>}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 bg-[#020617] border-t border-slate-800">
            <div className="relative group">
              <input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Dis-moi l'erreur exacte sur Facebook..."
                className="w-full bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 text-[12px] focus:outline-none focus:border-indigo-500 pr-12 text-white"
              />
              <button onClick={handleSend} className="absolute right-2 top-2 p-1.5 bg-indigo-600 rounded-lg text-white hover:bg-indigo-500 transition-colors">
                <Send size={16} />
              </button>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

function HealthItem({ label, status }: { label: string, status: 'online' | 'offline' | 'warning' }) {
  return (
    <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-slate-800/50">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${status === 'online' ? 'bg-emerald-500' : status === 'warning' ? 'bg-amber-500' : 'bg-rose-500'}`} />
        <span className={`text-[8px] font-black uppercase ${status === 'online' ? 'text-emerald-500' : status === 'warning' ? 'text-amber-500' : 'text-rose-500'}`}>
          {status}
        </span>
      </div>
    </div>
  );
}

function StepItem({ num, title, desc, status }: { num: string, title: string, desc: string, status: string }) {
  return (
    <div className="flex gap-4 p-4 bg-slate-900/40 border border-slate-800 rounded-2xl group hover:border-indigo-500/30 transition-colors">
       <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-[11px] font-black text-indigo-400 shrink-0 group-hover:bg-indigo-600 group-hover:text-white transition-all">
          {num}
       </div>
       <div className="space-y-1">
          <h4 className="text-[12px] font-bold text-white flex items-center gap-2">
            {title} {status === 'check' && <Check size={14} className="text-emerald-400" />}
          </h4>
          <p className="text-[10px] text-slate-500 leading-relaxed">{desc}</p>
       </div>
    </div>
  );
}

function ConfigField({ label, value, desc }: { label: string, value: string, desc: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 2000); };
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-end px-1">
        <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</label>
        <span className="text-[8px] text-slate-600 font-bold uppercase">{desc}</span>
      </div>
      <div className="flex gap-2">
        <div className="flex-1 bg-black/20 border border-slate-800/50 rounded-xl px-4 py-3 font-mono text-[11px] text-emerald-400 truncate">
          {value}
        </div>
        <button onClick={copy} className="bg-slate-800 p-3 rounded-xl hover:bg-slate-700 text-slate-400 border border-slate-700/50">
          {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
        </button>
      </div>
    </div>
  );
}

export default App;

