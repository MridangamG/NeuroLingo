"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/* ─── Types ──────────────────────────────────────────────── */
interface Analysis {
  intent: string;
  tone: string;
  figurative_language: boolean;
  ambiguity: string;
}
interface Translation {
  action: string;
  urgency: string;
  meaning: string;
  clarity_score: number;
}
interface ChatResponse {
  original_message: string;
  analysis: Analysis;
  structured_translation: Translation;
}
interface Msg {
  role: "user" | "system";
  content: string | ChatResponse;
}
interface HistoryItem {
  id: number;
  original_text: string;
  translated_text: string;
  intent: string;
  tone: string;
  clarity_score: number;
  action: string;
  urgency: string;
  created_at: string | null;
}

const API = "http://localhost:8000/api/v1";

/* ─── Component ──────────────────────────────────────────── */
export default function Home() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [recording, setRecording] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);

  const endRef = useRef<HTMLDivElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  /* ─── Auto-scroll ──────────────────────────────────────── */
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* ─── History ──────────────────────────────────────────── */
  const fetchHistory = useCallback(async () => {
    try {
      const r = await fetch(`${API}/chat/history?limit=30`);
      if (r.ok) setHistory(await r.json());
    } catch { /* noop */ }
  }, []);
  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  /* ─── Send Msg ─────────────────────────────────────────── */
  const send = async (override?: string) => {
    const text = override ?? input;
    if (!text.trim()) return;
    const next: Msg[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setSidebarOpen(false); // Close sidebar on mobile

    try {
      const r = await fetch(`${API}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!r.ok) throw new Error();
      const data: ChatResponse = await r.json();
      setMessages([...next, { role: "system", content: data }]);
      fetchHistory();
    } catch {
      setMessages([...next, {
        role: "system",
        content: {
          original_message: text,
          analysis: { tone: "Error", intent: "Error", figurative_language: false, ambiguity: "Unknown" },
          structured_translation: { action: "Check backend", urgency: "High", meaning: "Failed to process. Please ensure the backend is running and the Gemini API has available quota.", clarity_score: 0 },
        },
      }]);
    } finally {
      setLoading(false);
    }
  };

  /* ─── Voice ────────────────────────────────────────────── */
  const toggleMic = async () => {
    if (recording) { recorderRef.current?.stop(); setRecording(false); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const form = new FormData();
        form.append("audio", new Blob(chunksRef.current, { type: "audio/webm" }), "rec.webm");
        try {
          const r = await fetch(`${API}/voice/transcribe`, { method: "POST", body: form });
          if (r.ok) { const { text } = await r.json(); if (text) setInput(text); }
        } catch { /* noop */ }
      };
      rec.start();
      recorderRef.current = rec;
      setRecording(true);
    } catch { alert("Microphone access denied."); }
  };

  const speak = async (text: string, idx: number) => {
    if (speakingIdx === idx) { setSpeakingIdx(null); return; }
    setSpeakingIdx(idx);
    try {
      const r = await fetch(`${API}/voice/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (r.ok) {
        const url = URL.createObjectURL(await r.blob());
        const a = new Audio(url);
        a.onended = () => setSpeakingIdx(null);
        a.play();
      }
    } catch { setSpeakingIdx(null); }
  };

  /* ─── Render ───────────────────────────────────────────── */
  return (
    <div className="h-screen flex overflow-hidden bg-[#0B0F19] text-slate-100 selection:bg-indigo-500/30">

      {/* ─── Sidebar Panel ─── */}
      <aside className={`
        fixed md:relative z-40 h-full w-72 bg-[#0F172A] border-r border-white/5 
        flex flex-col shadow-2xl transition-transform duration-300 ease-in-out shrink-0
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
      `}>
        {/* Sidebar Header */}
        <div className="p-5 flex items-center gap-3 border-b border-white/5 bg-[#0F172A]">
          <div className="w-8 h-8 rounded-xl bg-gradient-primary flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-lg font-bold text-gradient tracking-tight">NeuroLingo</h1>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={() => { setMessages([]); setSidebarOpen(false); }}
            className="w-full bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl py-3 px-4 flex items-center gap-3 transition-all text-sm font-medium text-slate-200"
          >
            <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
            Start New Session
          </button>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
          <h3 className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Recent</h3>
          {history.length === 0 ? (
            <p className="px-3 py-4 text-sm text-slate-500 text-center">No previous sessions</p>
          ) : (
            history.map((h) => (
              <button
                key={h.id}
                onClick={() => { setInput(h.original_text); setSidebarOpen(false); }}
                className="w-full text-left px-3 py-3 rounded-xl text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-all truncate border border-transparent hover:border-white/5 group relative"
              >
                {h.original_text}
                <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className={`w-2 h-2 rounded-full ${h.urgency === 'High' ? 'bg-red-400' : h.urgency === 'Medium' ? 'bg-amber-400' : 'bg-green-400'}`} />
                </div>
              </button>
            ))
          )}
        </div>

        {/* User profile / Footer area */}
        <div className="p-4 border-t border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 text-sm font-bold">U</div>
            <span className="text-sm font-medium text-slate-300">User Account</span>
          </div>
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" title="System Online" />
        </div>
      </aside>

      {/* ─── Main Chat Area ─── */}
      <main className="flex-1 flex flex-col relative min-w-0">

        {/* Top bar (Mobile mostly) */}
        <header className="h-16 shrink-0 border-b border-white/5 bg-[#0B0F19]/80 backdrop-blur-md flex items-center px-4 absolute top-0 w-full z-20 md:hidden justify-between">
          <button onClick={() => setSidebarOpen(true)} className="p-2 text-slate-400 hover:text-white bg-white/5 rounded-lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>
          </button>
          <span className="font-bold text-gradient">NeuroLingo</span>
          <div className="w-8" /> {/* Spacer */}
        </header>

        {/* Messages Scrolling Area */}
        <div
          className="flex-1 overflow-y-auto pt-20 md:pt-8 pb-40 px-4 scroll-smooth"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="max-w-4xl mx-auto flex flex-col gap-6">

            {messages.length === 0 ? (
              // Empty State
              <div className="flex flex-col flex-1 min-h-[60vh] items-center justify-center text-center anim-fade">
                <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center mb-6 shadow-2xl">
                  <span className="text-3xl">🧠</span>
                </div>
                <h2 className="text-3xl font-bold tracking-tight text-white mb-3">How can I help decode?</h2>
                <p className="text-lg text-slate-400 max-w-lg mb-10">
                  Enter socially nuanced, vague, or complex language to receive a clear, structured translation.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                  {[
                    { label: "Decode hesitation", text: "Maybe we should revisit this." },
                    { label: "Decode priority", text: "I'll get to it when I can." },
                    { label: "Decode politeness", text: "That's an interesting approach…" },
                    { label: "Decode excitement", text: "This is a gold mine!" },
                  ].map((s, i) => (
                    <button
                      key={i}
                      onClick={() => send(s.text)}
                      className="glass-card text-left p-4 rounded-xl flex flex-col gap-1 group"
                    >
                      <span className="text-xs font-semibold text-indigo-400 tracking-wider uppercase">{s.label}</span>
                      <span className="text-slate-200 text-sm group-hover:text-white transition-colors">{s.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              // Chat Messages
              messages.map((msg, i) => (
                <div key={i} className="anim-message" style={{ animationDelay: `${i * 0.05}s` }}>
                  {msg.role === "user" ? (
                    // User Message Bubble
                    <div className="flex justify-end gap-4 ml-12">
                      <div className="bg-[#1E293B] border border-white/10 rounded-2xl rounded-tr-sm px-5 py-4 shadow-lg">
                        <p className="text-base text-slate-100 leading-relaxed whitespace-pre-wrap">{msg.content as string}</p>
                      </div>
                      <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 border border-white/10 flex items-center justify-center font-bold shadow-md">
                        U
                      </div>
                    </div>
                  ) : (
                    // AI Response Card
                    (() => {
                      const d = msg.content as ChatResponse;
                      const a = d.analysis;
                      const t = d.structured_translation;
                      return (
                        <div className="flex justify-start gap-4 mr-12">
                          <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-primary border border-indigo-400/30 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.4)]">
                            <span className="text-white font-bold text-sm">AI</span>
                          </div>

                          <div className="glass-panel w-full rounded-2xl rounded-tl-sm p-6 space-y-5">
                            {/* Meaning & Controls */}
                            <div className="flex flex-col gap-3 pb-5 border-b border-white/10">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Core Meaning</span>
                                <div className="flex items-center gap-3">
                                  <button
                                    onClick={() => speak(t.meaning, i)}
                                    className={`p-2 rounded-lg transition-all ${speakingIdx === i ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'}`}
                                    title="Listen to translation"
                                  >
                                    {speakingIdx === i ? (
                                      <svg className="w-4 h-4 animate-pulse" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19H2V5h4zm4 2h-2V3h2zm4-4h-2V7h2zm4 2h-2V5h2zm4-6h-2V11h2z" /></svg>
                                    ) : (
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M17.95 6.05a8 8 0 010 11.9M11 5L6 9H2v6h4l5 4V5z" /></svg>
                                    )}
                                  </button>
                                  <div className="px-3 py-1 rounded-lg bg-black/30 border border-white/10 flex flex-col items-center justify-center">
                                    <span className="text-xs text-slate-400 font-medium">Clarity</span>
                                    <span className={`text-sm font-bold ${t.clarity_score >= 80 ? 'text-green-400' : t.clarity_score >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                                      {t.clarity_score}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <p className="text-lg text-white leading-relaxed font-medium">
                                {t.meaning}
                              </p>
                            </div>

                            {/* Analysis Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <Metric title="Intent" value={a.intent} />
                              <Metric title="Tone" value={a.tone} />
                              <Metric title="Suggested Action" value={t.action} />
                              <div className="glass-card rounded-xl p-3 flex flex-col justify-center">
                                <span className="text-[0.65rem] text-slate-400 uppercase tracking-widest font-semibold mb-1 block">Urgency</span>
                                <div className="flex items-center gap-2">
                                  <div className={`w-2.5 h-2.5 rounded-full shadow-lg ${t.urgency === 'High' ? 'bg-red-500 shadow-red-500/50' : t.urgency === 'Medium' ? 'bg-amber-500 shadow-amber-500/50' : 'bg-green-500 shadow-green-500/50'}`} />
                                  <span className="text-sm font-medium text-white">{t.urgency}</span>
                                </div>
                              </div>
                            </div>

                            {/* Tags footer */}
                            {(a.figurative_language || a.ambiguity) && (
                              <div className="flex flex-wrap gap-2 pt-2">
                                {a.figurative_language && <span className="tag shadow-sm"><span className="text-indigo-400 mr-1">🎭</span> Figurative Setup</span>}
                                {a.ambiguity && <span className="tag shadow-sm"><span className="text-indigo-400 mr-1">🧩</span> Ambiguity: {a.ambiguity}</span>}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })()
                  )}
                </div>
              ))
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex justify-start gap-4 ml-12 anim-fade">
                <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-primary border border-indigo-400/30 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.4)]">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <div className="glass-panel rounded-2xl px-6 py-5 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-bounce" />
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: "0.15s" }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            )}
            <div ref={endRef} className="h-4" />
          </div>
        </div>

        {/* ─── Floating Input Bar ─── */}
        <div className="absolute bottom-0 w-full bg-gradient-to-t from-[#0B0F19] via-[#0B0F19] to-transparent pt-12 pb-8 px-4 z-30 pointer-events-none flex justify-center">
          <div className="w-full max-w-3xl pointer-events-auto">
            <div
              className="bg-[#1E293B] border border-white/10 rounded-2xl shadow-[0_15px_40px_-10px_rgba(0,0,0,0.5)] flex items-end p-2 transition-all focus-within:border-indigo-500/50 focus-within:shadow-[0_15px_40px_-10px_rgba(99,102,241,0.2)]"
            >
              {/* Mic Area */}
              <div className="p-2 shrink-0">
                <button
                  onClick={toggleMic}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center btn-hover btn-active ${recording ? 'bg-red-500/20 text-red-500 ring-2 ring-red-500/50 pulseGlow' : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'}`}
                  title={recording ? "Stop Recording" : "Voice Input"}
                >
                  {recording ? (
                    <div className="relative flex items-center justify-center">
                      <span className="absolute inset-0 rounded-full bg-red-500/30 animate-ping" />
                      <svg className="w-5 h-5 relative" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" /></svg>
                    </div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-14 0m7 7v4m-4 0h8M12 1a3 3 0 00-3 3v7a3 3 0 006 0V4a3 3 0 00-3-3z" /></svg>
                  )}
                </button>
              </div>

              {/* Textarea / Input */}
              <div className="flex-1 min-h-[56px] flex items-center justify-center px-1">
                <input
                  id="chat-input"
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()}
                  placeholder="Message NeuroLingo..."
                  className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-[15px] focus:outline-none"
                  autoComplete="off"
                />
              </div>

              {/* Send Button */}
              <div className="p-2 shrink-0">
                <button
                  onClick={() => send()}
                  disabled={loading || !input.trim()}
                  className="w-10 h-10 rounded-xl bg-gradient-primary text-white flex items-center justify-center btn-hover btn-active disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/30"
                >
                  <svg className="w-5 h-5 ml-0.5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
                  </svg>
                </button>
              </div>
            </div>
            <p className="text-center text-[0.65rem] text-slate-500 mt-3 font-medium tracking-wide">
              NeuroLingo is an AI-powered bridge. Messages are analyzed by Gemini 2.5 Flash.
            </p>
          </div>
        </div>

      </main>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-[#0B0F19]/80 backdrop-blur-sm z-30 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  );
}

/* ─── Metric Card ────────────────────────────────────────── */
function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="glass-card rounded-xl p-3 flex flex-col justify-center">
      <span className="text-[0.65rem] text-slate-400 uppercase tracking-widest font-semibold mb-1">{title}</span>
      <p className="text-sm text-white font-medium line-clamp-2 leading-snug">{value}</p>
    </div>
  );
}
