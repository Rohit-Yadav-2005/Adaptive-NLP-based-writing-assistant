import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, Save, Sparkles, History, Clock, 
  AlertCircle, Zap, Target, ArrowRight, MessageSquare, 
  Wind, Music, Eye, EyeOff, Send, BookMarked
} from 'lucide-react';
import { documentApi } from '../api';
import Modal from '../components/Modal';

const WRITING_TYPES = [
  { id: 'general', label: 'General Sync' },
  { id: 'academic', label: 'Academic Thesis' },
  { id: 'email', label: 'Command Outreach' },
  { id: 'technical', label: 'Spec Documentation' },
  { id: 'creative', label: 'Deep Narrative' },
  { id: 'blog', label: 'Broadcast Article' },
];

const AMBIENT_SOUNDS = [
  { id: 'rain', label: 'Heavy Rain', url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3' }, // Placeholder URLs
  { id: 'lofi', label: 'Lo-Fi Pulse', url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3' },
  { id: 'library', label: 'The Library', url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3' },
];

const Editor = () => {
  const { docId } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [writingType, setWritingType] = useState('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  
  // View Modes
  const [showHistory, setShowHistory] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [zenMode, setZenMode] = useState(false);
  const [ambientSelected, setAmbientSelected] = useState(null);
  
  // Modal State
  const [isCommitModalOpen, setIsCommitModalOpen] = useState(false);
  const [commitSummary, setCommitSummary] = useState('Workspace Sync');

  const audioRef = useRef(null);

  useEffect(() => {
    loadDocument();
  }, [docId]);

  const loadDocument = async () => {
    try {
      const [histResp, commResp] = await Promise.all([
        documentApi.getHistory(docId),
        documentApi.listComments(docId)
      ]);
      setHistory(histResp.data);
      setComments(commResp.data);
      if (histResp.data.length > 0) {
        const latest = histResp.data[histResp.data.length - 1];
        setContent(latest.content_snapshot);
        setTitle("Active Draft"); 
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await documentApi.updateDocument(docId, {
        content,
        change_summary: commitSummary
      });
      const histResp = await documentApi.getHistory(docId);
      setHistory(histResp.data);
      setIsCommitModalOpen(false);
    } catch (err) {
      alert('Sync failed');
    } finally {
      setSaving(false);
    }
  };

  const handleAnalyze = async () => {
    if (!content.trim()) return;
    setAnalyzing(true);
    setAiResult(null);
    try {
      const resp = await documentApi.analyze(content, writingType);
      setAiResult(resp.data);
    } catch (err) {
      alert('Intelligence analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      await documentApi.addComment({ content: newComment, document_id: parseInt(docId) });
      setNewComment('');
      const resp = await documentApi.listComments(docId);
      setComments(resp.data);
    } catch (err) {
      alert('Failed to post comment');
    }
  };

  const toggleAmbient = (sound) => {
    if (ambientSelected?.id === sound.id) {
      setAmbientSelected(null);
      audioRef.current.pause();
    } else {
      setAmbientSelected(sound);
      audioRef.current.src = sound.url;
      audioRef.current.play();
    }
  };

  const applyAllSuggestions = () => {
    if (!aiResult || !aiResult.explanations) return;
    setCommitSummary('Auto-sync: AI Optimization applied');
    let newContent = content;
    const sortedExplanations = [...aiResult.explanations].sort((a,b) => b.original.length - a.original.length);
    sortedExplanations.forEach(exp => {
      newContent = newContent.replace(exp.original, exp.suggestion);
    });
    setContent(newContent);
    setAiResult(null);
  };

  if (loading) return <div className="h-screen bg-background flex items-center justify-center text-accent uppercase font-black tracking-widest animate-pulse italic">Connecting to Intelligence Node...</div>;

  return (
    <div className={`h-screen flex flex-col bg-background text-white selection:bg-accent/40 ${zenMode ? 'cursor-none' : ''}`}>
      <audio ref={audioRef} loop />
      
      {/* Header - Hidden in Zen if not hovered? Let's keep it minimalist */}
      <AnimatePresence>
        {!zenMode && (
          <motion.header 
            initial={{ y: -50 }}
            animate={{ y: 0 }}
            exit={{ y: -50 }}
            className="glass-effect border-b border-white/5 p-4 flex items-center justify-between px-10 z-50 shadow-2xl"
          >
            <div className="flex items-center gap-6">
              <button onClick={() => navigate('/dashboard')} className="p-2.5 hover:bg-white/5 rounded-xl text-muted transition-all">
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div className="h-8 w-[1px] bg-white/5" />
              <div>
                <h1 className="text-xs font-black tracking-[0.2em] uppercase italic opacity-70 mb-1">{title}</h1>
                <div className="flex items-center gap-3">
                   <div className="flex items-center gap-2 text-[9px] font-black text-accent bg-accent/10 px-2 py-0.5 rounded border border-accent/10 uppercase tracking-widest">
                     <Target className="w-3 h-3" />
                     <select 
                       value={writingType}
                       onChange={(e) => setWritingType(e.target.value)}
                       className="bg-transparent border-none outline-none cursor-pointer hover:text-white"
                     >
                       {WRITING_TYPES.map(t => <option key={t.id} value={t.id} className="bg-background">{t.label}</option>)}
                     </select>
                   </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center bg-white/5 rounded-2xl p-1 border border-white/5">
                <button 
                  onClick={() => setShowHistory(!showHistory)}
                  className={`p-2.5 rounded-xl transition-all ${showHistory ? 'text-accent bg-accent/10' : 'text-muted hover:text-white'}`}
                >
                  <History className="w-5 h-5" />
                </button>
                <button 
                  onClick={() => setShowComments(!showComments)}
                  className={`p-2.5 rounded-xl transition-all ${showComments ? 'text-accent-secondary bg-accent-secondary/10' : 'text-muted hover:text-white'}`}
                >
                  <MessageSquare className="w-5 h-5" />
                </button>
              </div>

              <div className="flex items-center bg-white/5 rounded-2xl p-1 border border-white/5">
                {AMBIENT_SOUNDS.map(s => (
                   <button 
                    key={s.id}
                    onClick={() => toggleAmbient(s)}
                    className={`p-2.5 rounded-xl transition-all ${ambientSelected?.id === s.id ? 'text-accent bg-accent/10' : 'text-muted hover:text-white'}`}
                    title={s.label}
                   >
                    {s.id === 'rain' ? <Wind className="w-5 h-5" /> : <Music className="w-5 h-5" />}
                   </button>
                ))}
              </div>

              <button 
                onClick={() => setZenMode(true)}
                className="p-3 bg-white/5 border border-white/10 rounded-2xl text-muted hover:text-accent transition-all"
              >
                 <EyeOff className="w-5 h-5" />
              </button>

              <div className="w-[1px] h-6 bg-white/10 mx-2" />
              
              <button 
                onClick={() => setIsCommitModalOpen(true)}
                disabled={saving}
                className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 px-6 py-3 rounded-2xl text-xs font-black uppercase tracking-[0.2em] transition-all text-muted hover:text-white"
              >
                <Save className="w-4 h-4" /> Commit
              </button>
              <button 
                onClick={handleAnalyze}
                disabled={analyzing}
                className="flex items-center gap-2 bg-accent text-background px-6 py-3 rounded-2xl text-xs font-black uppercase tracking-[0.2em] shadow-[0_10px_30px_rgba(var(--accent-rgb),0.3)] hover:scale-105 transition-all"
              >
                <Sparkles className="w-4 h-4" /> {analyzing ? 'Thinking...' : 'Analyze'}
              </button>
            </div>
          </motion.header>
        )}
      </AnimatePresence>

      {/* Main Drafting Zone */}
      <div className="flex-1 flex overflow-hidden relative">
        <main className={`flex-1 flex flex-col transition-all duration-700 items-center justify-center ${zenMode ? 'p-0' : 'p-10'}`}>
          <div className={`${zenMode ? 'w-full max-w-3xl' : 'w-full max-w-5xl'} h-full flex flex-col relative`}>
             {zenMode && (
                <button 
                  onClick={() => setZenMode(false)}
                  className="fixed top-8 left-8 p-4 bg-white/2 opacity-0 hover:opacity-100 transition-opacity rounded-full text-white/20 hover:text-white z-50"
                  onMouseEnter={() => document.body.style.cursor = 'default'}
                  onMouseLeave={() => document.body.style.cursor = 'none'}
                >
                  <Eye className="w-8 h-8" />
                </button>
             )}
             
             <textarea 
                className={`flex-1 bg-transparent p-12 text-2xl leading-[1.8] outline-none resize-none font-medium placeholder:text-white/5 caret-accent transition-all duration-700 text-center ${zenMode ? 'text-lg opacity-80' : ''}`}
                placeholder="Initialize creative sync..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                spellCheck={false}
              />
          </div>
        </main>

        <AnimatePresence>
          {(aiResult || showHistory || showComments) && !zenMode && (
            <motion.aside 
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              className="w-[400px] glass-effect border-l border-white/5 flex flex-col z-40 overflow-hidden"
            >
              {showHistory && (
                <div className="p-8 h-full flex flex-col">
                    <h2 className="sidebar-label !ml-0 mb-8 flex items-center gap-2 text-accent">
                        <History className="w-4 h-4" /> Workspace Synchronizations
                    </h2>
                    <div className="space-y-4 overflow-y-auto pr-2 no-scrollbar">
                        {history.slice().reverse().map((ver, idx) => (
                        <div 
                            key={ver.id}
                            className="p-5 rounded-3xl border border-white/5 bg-white/[0.02] hover:border-accent/40 transition-all cursor-pointer group"
                            onClick={() => setContent(ver.content_snapshot)}
                        >
                            <div className="flex justify-between items-start mb-3">
                                <p className="font-black text-[10px] text-accent uppercase tracking-widest italic">Node v{history.length - idx}</p>
                                <span className="text-[10px] font-bold text-muted uppercase tracking-tighter">{new Date(ver.created_at).toLocaleTimeString()}</span>
                            </div>
                            <p className="text-sm font-medium text-white/50 group-hover:text-white transition-colors capitalize leading-relaxed italic">"{ver.change_summary}"</p>
                        </div>
                        ))}
                    </div>
                </div>
              )}

              {showComments && (
                <div className="p-8 h-full flex flex-col">
                    <h2 className="sidebar-label !ml-0 mb-8 flex items-center gap-2 text-accent-secondary">
                        <MessageSquare className="w-4 h-4" /> Collaborative Meta
                    </h2>
                    <div className="flex-1 space-y-6 overflow-y-auto pr-2 no-scrollbar mb-6">
                        {comments.map((comm, idx) => (
                          <div key={idx} className="space-y-2">
                             <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-accent-secondary/20 flex items-center justify-center text-[10px] font-black text-accent-secondary italic">
                                   {comm.user_email[0].toUpperCase()}
                                </div>
                                <span className="text-[10px] font-black uppercase text-muted tracking-widest">{comm.user_email.split('@')[0]}</span>
                                <span className="text-[8px] text-muted opacity-30 ml-auto">{new Date(comm.created_at).toLocaleTimeString()}</span>
                             </div>
                             <div className="p-4 rounded-3xl bg-white/5 border border-white/5 text-sm leading-relaxed text-white/70 italic">
                                {comm.content}
                             </div>
                          </div>
                        ))}
                    </div>
                    <form onSubmit={handleAddComment} className="mt-auto relative">
                       <input 
                         className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-6 pr-14 text-sm outline-none focus:ring-1 focus:ring-accent-secondary transition-all"
                         placeholder="Post annotation..."
                         value={newComment}
                         onChange={e => setNewComment(e.target.value)}
                       />
                       <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 text-accent-secondary hover:text-white transition-colors">
                          <Send className="w-4 h-4" />
                       </button>
                    </form>
                </div>
              )}

              {aiResult && !showHistory && !showComments && (
                <div className="p-8 overflow-y-auto flex-1 no-scrollbar">
                  <div className="flex items-center justify-between mb-10">
                    <h2 className="text-2xl font-black italic uppercase tracking-tighter flex items-center gap-3">
                      <Zap className="text-accent fill-accent" /> Intelligence
                    </h2>
                    <button 
                      onClick={applyAllSuggestions}
                      className="text-[10px] font-black uppercase tracking-widest bg-accent/10 text-accent border border-accent/20 px-4 py-2 rounded-2xl hover:bg-accent/20 transition-all active:scale-95 shadow-xl shadow-accent/10"
                    >
                      Sync All
                    </button>
                  </div>

                  <div className="space-y-8">
                    <div className="p-6 rounded-3xl bg-accent/5 border border-accent/10 relative overflow-hidden group">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-all">
                         <Target className="w-20 h-20" />
                      </div>
                      <p className="text-[10px] font-black uppercase text-accent mb-3 tracking-[0.2em]">Strategy Identity</p>
                      <p className="text-sm font-bold leading-relaxed italic text-white/80">"{aiResult.domain_advice}"</p>
                    </div>

                    {aiResult.context_used && (
                      <div className="p-4 rounded-2xl bg-white/5 border border-dashed border-white/10 flex items-center gap-3 text-muted">
                         <Library className="w-4 h-4 text-accent" />
                         <span className="text-[10px] font-black uppercase tracking-widest">Research Context Applied</span>
                      </div>
                    )}

                    <div className="space-y-4">
                      <p className="sidebar-label !ml-0 mb-4">Refinement Nodes</p>
                      {aiResult.explanations.map((exp, i) => (
                        <div key={i} className="premium-card p-6 bg-white/[0.01]">
                          <div className="flex items-center gap-3 text-accent mb-4">
                            <AlertCircle className="w-3.5 h-3.5" />
                            <span className="font-black uppercase text-[10px] tracking-widest">{exp.error_type}</span>
                          </div>
                          <div className="space-y-3 mb-5">
                             <div className="flex items-center gap-3">
                                <span className="bg-red-500/10 text-red-400/50 px-3 py-1 rounded-xl line-through text-xs font-bold">{exp.original}</span>
                                <ArrowRight className="w-3 h-3 text-muted/30" />
                                <span className="bg-accent/10 text-accent px-3 py-1 rounded-xl font-black text-xs italic">{exp.suggestion}</span>
                             </div>
                          </div>
                           <p className="text-[11px] text-white/40 leading-relaxed italic border-t border-white/5 pt-4 opacity-80">{exp.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* Commit Modal */}
      <Modal isOpen={isCommitModalOpen} onClose={() => setIsCommitModalOpen(false)} title="Commit Evolution">
        <form onSubmit={handleSave} className="space-y-8 px-2 py-4">
          <div>
            <label className="text-[11px] font-black text-muted uppercase tracking-[0.3em] mb-4 block">Commit Summary</label>
            <input 
              autoFocus
              className="w-full bg-white/5 border border-white/10 rounded-[2rem] py-5 px-10 text-lg font-black italic tracking-tighter focus:ring-4 focus:ring-accent/20 outline-none transition-all"
              value={commitSummary}
              onChange={e => setCommitSummary(e.target.value)}
              placeholder="e.g. CORE_LOGIC_SYNCHRONIZED"
            />
          </div>
          <div className="p-5 bg-accent/5 rounded-[1.5rem] border border-accent/10">
             <div className="flex items-center gap-2 mb-2 text-accent">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-[10px] font-black uppercase tracking-widest">Permanent Index</span>
             </div>
             <p className="text-[11px] text-muted italic leading-relaxed">This commit will be permanently indexed in the global workspace activity feed and document history.</p>
          </div>
          <button type="submit" disabled={saving} className="button-primary w-full py-5 text-sm font-black italic uppercase tracking-[0.3em] shadow-2xl shadow-accent/30">
             Authorize Sync
          </button>
        </form>
      </Modal>
    </div>
  );
};

export default Editor;
