import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Folder, Plus, FileText, LogOut, Users,
  Search, ChevronRight, Zap, UserPlus, Activity,
  Copy, Check, Clock, Upload, FileUp, Sparkles, TrendingUp,
  BarChart3, BookMarked
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import { documentApi } from '../api';
import Modal from '../components/Modal';

// ─── Sub-components defined BEFORE Dashboard to avoid hoisting issues ──────────
const ArrowRight = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

const NavButton = ({ id, icon: Icon, label, active, onClick }) => (
  <button
    onClick={() => onClick(id)}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold uppercase tracking-tight transition-all border ${
      active
        ? 'bg-accent text-background border-accent shadow-lg shadow-accent/20'
        : 'text-muted border-transparent hover:bg-white/5 hover:text-white'
    }`}
  >
    <Icon className="w-4 h-4 shrink-0" /> {label}
  </button>
);

// ─── Main Component ────────────────────────────────────────────────────────────
const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('repository');
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [folders, setFolders] = useState([]);
  const [selectedFolderId, setSelectedFolderId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [vaultFiles, setVaultFiles] = useState([]);
  const [analyticsData, setAnalyticsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  // Modal states
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDocType, setNewDocType] = useState('general');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteLink, setInviteLink] = useState('');
  const [copied, setCopied] = useState(false);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  // ── Safe fetch that never throws ──────────────────────────────────────────
  const safeFetch = async (promise, fallback = []) => {
    try {
      const res = await promise;
      return res.data ?? fallback;
    } catch {
      return fallback;
    }
  };

  // ── Initial load ──────────────────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        const wsData = await safeFetch(documentApi.listWorkspaces(), []);
        setWorkspaces(wsData);
        if (wsData.length > 0) {
          await loadOrg(wsData[0]);
        }
      } catch (err) {
        if (err?.response?.status === 401) {
          navigate('/login');
        } else {
          setError('Failed to load workspace. Please refresh.');
        }
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const loadOrg = async (org) => {
    setSelectedOrg(org);
    setSelectedFolderId(null);

    const [docs, fols, acts, vault, analytics] = await Promise.all([
      safeFetch(documentApi.listDocuments(org.id)),
      safeFetch(documentApi.listFolders(org.id)),
      safeFetch(documentApi.getActivity(org.id)),
      safeFetch(documentApi.listVault(org.id)),
      safeFetch(documentApi.getAnalytics(org.id)),
    ]);

    setDocuments(docs);
    setFolders(fols);
    setActivities(acts);
    setVaultFiles(vault);
    setAnalyticsData(analytics);
  };

  // ── Actions ───────────────────────────────────────────────────────────────
  const createDoc = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      const res = await documentApi.createDocument({
        title: newName,
        content: '',
        org_id: selectedOrg.id,
        folder_id: selectedFolderId || null,
        writing_type: newDocType,
      });
      const docId = res.data?.id;
      if (!docId) throw new Error('No document ID returned');
      navigate(`/editor/${docId}`);
    } catch {
      alert('Failed to create document');
    }
  };

  const createFolder = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      const res = await documentApi.createFolder({ name: newName, org_id: selectedOrg.id });
      setFolders(prev => [...prev, res.data]);
      setIsFolderModalOpen(false);
      setNewName('');
    } catch {
      alert('Failed to create folder');
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    try {
      const res = await documentApi.inviteMember(selectedOrg.id, inviteEmail);
      setInviteLink(window.location.origin + (res.data.invite_link || ''));
    } catch {
      alert('Only workspace owners can invite members');
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleVaultUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await documentApi.uploadVaultFile(selectedOrg.id, file);
      const fresh = await safeFetch(documentApi.listVault(selectedOrg.id));
      setVaultFiles(fresh);
    } catch {
      alert('Upload failed');
    }
  };

  // ── Derived state ─────────────────────────────────────────────────────────
  const filteredDocs = documents.filter(d => {
    const matchSearch = (d.title || '').toLowerCase().includes(search.toLowerCase());
    const matchFolder = selectedFolderId ? d.folder_id === selectedFolderId : true;
    return matchSearch && matchFolder;
  });

  // ── Render guards ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Zap className="w-12 h-12 text-accent mx-auto mb-4 animate-pulse" />
          <p className="text-muted text-sm font-bold uppercase tracking-widest">Loading Workspace...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md px-6">
          <p className="text-red-400 font-bold mb-4">{error}</p>
          <button onClick={() => window.location.reload()} className="button-primary px-6 py-2">Refresh</button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'repository', icon: Folder, label: 'Repository' },
    { id: 'vault', icon: BookMarked, label: 'Research Vault' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'activity', icon: Activity, label: 'Activity Feed' },
    { id: 'team', icon: Users, label: 'Team' },
  ];

  return (
    <div className="flex h-screen bg-background text-white overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="w-64 border-r border-white/10 flex flex-col glass-effect shrink-0">
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <Zap className="w-8 h-8 text-accent fill-accent" />
            <div>
              <span className="text-xl font-black uppercase italic tracking-tighter block leading-none">Nexus AI</span>
              <span className="text-[9px] text-muted uppercase tracking-widest">Ultimate Edition</span>
            </div>
          </div>

          {/* Nav */}
          <div className="space-y-1 mb-8">
            <p className="text-[9px] font-black text-muted uppercase tracking-widest mb-3 px-2">Navigation</p>
            {tabs.map(tab => (
              <NavButton key={tab.id} {...tab} active={activeTab === tab.id} onClick={setActiveTab} />
            ))}
          </div>

          {/* Workspaces */}
          {workspaces.length > 0 && (
            <div>
              <p className="text-[9px] font-black text-muted uppercase tracking-widest mb-3 px-2">Workspaces</p>
              {workspaces.map(ws => (
                <button
                  key={ws.id}
                  onClick={() => loadOrg(ws)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                    selectedOrg?.id === ws.id ? 'text-accent' : 'text-muted hover:text-white'
                  }`}
                >
                  <span className="truncate">{ws.name}</span>
                  {ws.role === 'owner' && (
                    <span className="ml-1 text-[8px] bg-accent text-background px-1 rounded font-black shrink-0">HQ</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sign Out */}
        <div className="mt-auto p-4 border-t border-white/10">
          <div className="premium-card p-3 mb-3 bg-accent/5 border-accent/10">
            <div className="flex items-center gap-2 mb-1 text-accent">
              <Sparkles className="w-3 h-3" />
              <span className="text-[9px] font-black uppercase tracking-widest">Pro Active</span>
            </div>
            <p className="text-[9px] text-muted">Unlimited vault storage enabled.</p>
          </div>
          <button
            onClick={() => { localStorage.removeItem('enterprise_token'); navigate('/login'); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold text-red-400 hover:bg-red-500/10 transition-all"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-white/10 glass-effect px-8 py-4 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-2xl font-black uppercase italic tracking-tight capitalize">{activeTab.replace('-', ' ')}</h1>
            {selectedOrg && <p className="text-[10px] text-muted uppercase tracking-widest mt-0.5">{selectedOrg.name}</p>}
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search..."
                className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-accent/50 w-56"
              />
            </div>

            {activeTab === 'repository' && (
              <button
                onClick={() => { setNewName(''); setIsDocModalOpen(true); }}
                className="button-primary flex items-center gap-2 px-4 py-2 text-sm"
              >
                <Plus className="w-4 h-4" /> New File
              </button>
            )}
            {activeTab === 'vault' && (
              <>
                <input
                  type="file" ref={fileInputRef} className="hidden"
                  accept=".pdf,.txt,.docx" onChange={handleVaultUpload}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="button-primary flex items-center gap-2 px-4 py-2 text-sm"
                >
                  <Upload className="w-4 h-4" /> Upload PDF
                </button>
              </>
            )}
            {activeTab === 'team' && (
              <button
                onClick={() => { setInviteEmail(''); setInviteLink(''); setIsInviteModalOpen(true); }}
                className="button-primary flex items-center gap-2 px-4 py-2 text-sm"
              >
                <UserPlus className="w-4 h-4" /> Invite Member
              </button>
            )}
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {/* ── Repository Tab ── */}
          {activeTab === 'repository' && (
            <div className="space-y-6">
              {/* Folder Filter */}
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => setSelectedFolderId(null)}
                  className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest border transition-all ${
                    !selectedFolderId ? 'bg-white text-background border-white' : 'border-white/20 text-muted hover:border-white/40'
                  }`}
                >
                  All Files
                </button>
                {folders.map(f => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFolderId(f.id)}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest border transition-all ${
                      selectedFolderId === f.id ? 'bg-accent text-background border-accent' : 'border-white/20 text-muted hover:border-white/40'
                    }`}
                  >
                    {f.name}
                  </button>
                ))}
                <button
                  onClick={() => { setNewName(''); setIsFolderModalOpen(true); }}
                  className="px-4 py-1.5 rounded-full text-xs font-bold border border-dashed border-white/20 text-muted hover:text-accent hover:border-accent transition-all flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" /> Folder
                </button>
              </div>

              {/* Document list */}
              <div className="premium-card divide-y divide-white/5">
                {filteredDocs.length === 0 ? (
                  <div className="p-16 text-center text-muted">
                    <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="text-sm font-bold uppercase tracking-widest opacity-50">No files yet</p>
                    <p className="text-xs mt-2 opacity-30">Click "New File" to create your first project.</p>
                  </div>
                ) : filteredDocs.map(doc => (
                  <motion.div
                    key={doc.id}
                    whileHover={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
                    className="px-6 py-4 flex items-center justify-between cursor-pointer group"
                    onClick={() => navigate(`/editor/${doc.id}`)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-accent/10 group-hover:border-accent/30 transition-all">
                        <FileText className="w-5 h-5 text-muted group-hover:text-accent" />
                      </div>
                      <div>
                        <p className="font-bold text-sm group-hover:text-accent transition-colors">{doc.title || 'Untitled'}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[9px] uppercase text-muted font-bold tracking-widest">{doc.writing_type || 'General'}</span>
                          {doc.folder_id && (
                            <>
                              <span className="text-white/10">·</span>
                              <span className="text-[9px] uppercase text-accent/50 font-bold tracking-widest">
                                {folders.find(f => f.id === doc.folder_id)?.name || ''}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-muted">
                      <span className="text-[10px] hidden sm:block">
                        {doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : ''}
                      </span>
                      <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all" />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* ── Vault Tab ── */}
          {activeTab === 'vault' && (
            <div className="space-y-6 max-w-4xl">
              <div className="premium-card p-8 bg-gradient-to-br from-accent/5 to-transparent">
                <BookMarked className="w-10 h-10 text-accent mb-4" />
                <h2 className="text-2xl font-black uppercase italic tracking-tight mb-2">Research Vault</h2>
                <p className="text-muted text-sm leading-relaxed max-w-lg">
                  Upload PDFs, research papers, or textbooks. The AI will index them and use them to fact-check and cite sources in your editor.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {vaultFiles.map(vf => (
                  <div key={vf.id} className="premium-card p-5 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
                      <FileUp className="w-5 h-5 text-accent" />
                    </div>
                    <div className="overflow-hidden">
                      <p className="font-bold text-sm truncate">{vf.filename}</p>
                      <p className="text-[9px] text-muted uppercase tracking-widest mt-0.5">Indexed</p>
                    </div>
                  </div>
                ))}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="premium-card p-5 border-dashed border-white/10 flex items-center justify-center gap-2 text-muted hover:text-accent hover:border-accent transition-all text-sm font-bold"
                >
                  <Plus className="w-4 h-4" /> Add Document
                </button>
              </div>
            </div>
          )}

          {/* ── Analytics Tab ── */}
          {activeTab === 'analytics' && (
            <div className="space-y-6 max-w-5xl">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="premium-card p-6 bg-accent/5">
                  <p className="text-[10px] font-black uppercase text-accent tracking-widest mb-2">Total Activity</p>
                  <p className="text-4xl font-black">{activities.length}</p>
                  <p className="text-[10px] text-muted mt-2 flex items-center gap-1"><TrendingUp className="w-3 h-3" /> Team operations</p>
                </div>
                <div className="premium-card p-6">
                  <p className="text-[10px] font-black uppercase text-muted tracking-widest mb-2">Research Files</p>
                  <p className="text-4xl font-black">{vaultFiles.length}</p>
                  <p className="text-[10px] text-muted mt-2">Indexed documents</p>
                </div>
                <div className="premium-card p-6">
                  <p className="text-[10px] font-black uppercase text-muted tracking-widest mb-2">Projects</p>
                  <p className="text-4xl font-black">{documents.length}</p>
                  <p className="text-[10px] text-muted mt-2">Total files</p>
                </div>
              </div>

              {analyticsData.length > 0 && (
                <div className="premium-card p-6">
                  <h3 className="font-black uppercase text-sm tracking-widest mb-6">Activity Trend (7 days)</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={analyticsData}>
                      <defs>
                        <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7c9dff" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#7c9dff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="day" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#121a2f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff', fontSize: 11 }}
                      />
                      <Area type="monotone" dataKey="value" stroke="#7c9dff" strokeWidth={2} fill="url(#grad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {analyticsData.length === 0 && (
                <div className="premium-card p-12 text-center text-muted">
                  <BarChart3 className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p className="text-sm font-bold uppercase tracking-widest opacity-50">No data yet</p>
                  <p className="text-xs mt-1 opacity-30">Start writing to generate analytics.</p>
                </div>
              )}
            </div>
          )}

          {/* ── Activity Tab ── */}
          {activeTab === 'activity' && (
            <div className="max-w-3xl mx-auto space-y-4">
              {activities.length === 0 ? (
                <div className="premium-card p-12 text-center text-muted">
                  <Activity className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p className="text-sm font-bold uppercase tracking-widest opacity-50">No activity yet</p>
                </div>
              ) : activities.map((log, i) => (
                <div key={i} className="premium-card p-5 flex items-start gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${i === 0 ? 'bg-accent/20 border border-accent/40' : 'bg-white/5 border border-white/10'}`}>
                    <Activity className={`w-4 h-4 ${i === 0 ? 'text-accent' : 'text-muted'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-[10px] font-black uppercase tracking-widest text-accent">{log.action || 'Action'}</span>
                      <span className="text-[9px] text-muted flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                      </span>
                    </div>
                    <p className="text-sm text-white/70">
                      <span className="font-bold text-white">{(log.user_email || 'System').split('@')[0]}</span>
                      {' '}{log.details || ''}
                    </p>
                    {log.document_title && (
                      <p className="text-[10px] text-muted/50 mt-1 italic">↳ {log.document_title}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Team Tab ── */}
          {activeTab === 'team' && (
            <div className="max-w-3xl mx-auto space-y-6">
              <div className="premium-card p-10 text-center bg-gradient-to-br from-accent/5 to-transparent">
                <Users className="w-12 h-12 text-accent mx-auto mb-4" />
                <h2 className="text-2xl font-black uppercase italic tracking-tighter mb-3">Team Workspace</h2>
                <p className="text-muted text-sm max-w-sm mx-auto mb-6">
                  Invite collaborators to share your workspace, documents, and research vault.
                </p>
                <button
                  onClick={() => { setInviteEmail(''); setInviteLink(''); setIsInviteModalOpen(true); }}
                  className="button-primary flex items-center gap-2 mx-auto px-6 py-3"
                >
                  <UserPlus className="w-4 h-4" /> Invite Team Member
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ── Modals ── */}
      <Modal isOpen={isDocModalOpen} onClose={() => setIsDocModalOpen(false)} title="New Project">
        <form onSubmit={createDoc} className="space-y-5">
          <div>
            <label className="text-xs font-bold text-muted uppercase tracking-widest block mb-2">Project Name</label>
            <input
              autoFocus
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="e.g. Research Thesis Draft"
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:ring-2 focus:ring-accent/50 outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-muted uppercase tracking-widest block mb-2">Writing Type</label>
            <select
              value={newDocType}
              onChange={e => setNewDocType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-accent/50"
            >
              <option value="general">General</option>
              <option value="academic">Academic / Thesis</option>
              <option value="email">Email / Correspondence</option>
              <option value="technical">Technical Documentation</option>
              <option value="creative">Creative Writing</option>
              <option value="blog">Blog / Article</option>
            </select>
          </div>
          <button type="submit" className="button-primary w-full py-3">Create Project</button>
        </form>
      </Modal>

      <Modal isOpen={isFolderModalOpen} onClose={() => setIsFolderModalOpen(false)} title="New Folder">
        <form onSubmit={createFolder} className="space-y-5">
          <div>
            <label className="text-xs font-bold text-muted uppercase tracking-widest block mb-2">Folder Name</label>
            <input
              autoFocus
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="e.g. Client Research"
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:ring-2 focus:ring-accent/50 outline-none"
            />
          </div>
          <button type="submit" className="button-primary w-full py-3">Create Folder</button>
        </form>
      </Modal>

      <Modal isOpen={isInviteModalOpen} onClose={() => { setIsInviteModalOpen(false); setInviteLink(''); }} title="Invite Team Member">
        {!inviteLink ? (
          <form onSubmit={handleInvite} className="space-y-5">
            <div>
              <label className="text-xs font-bold text-muted uppercase tracking-widest block mb-2">Member Email</label>
              <input
                autoFocus
                type="email"
                required
                value={inviteEmail}
                onChange={e => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:ring-2 focus:ring-accent/50 outline-none"
              />
            </div>
            <button type="submit" className="button-primary w-full py-3">Generate Invite Link</button>
          </form>
        ) : (
          <div className="text-center space-y-5">
            <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto">
              <Check className="w-8 h-8 text-accent" />
            </div>
            <p className="text-sm text-muted">Invite link generated! Share it with your teammate.</p>
            <div className="flex items-center gap-2 p-3 bg-white/5 rounded-xl border border-white/10">
              <input readOnly value={inviteLink} className="flex-1 bg-transparent text-xs outline-none text-white/50 truncate" />
              <button onClick={copyLink} className="p-1.5 hover:bg-white/10 rounded text-accent">
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <button onClick={() => { setIsInviteModalOpen(false); setInviteLink(''); }} className="text-muted text-xs hover:text-white">Done</button>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Dashboard;
