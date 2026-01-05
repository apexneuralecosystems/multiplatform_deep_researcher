import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import {
    Zap,
    Search,
    Instagram,
    Linkedin,
    Youtube,
    Globe,
    Copy,
    Download,
    Activity,
    ArrowLeft
} from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import type { AgentsState, ResearchResponse } from './types';
import LandingPage from './components/LandingPage';
import PrivacyPolicy from './components/PrivacyPolicy';
import TermsAndConditions from './components/TermsAndConditions';
import Footer from './components/Footer';
import './components/LandingPage.css';

// ═══════════════════════════════════════════════════════════════════
// API Configuration
// ═══════════════════════════════════════════════════════════════════

// Use environment variable for production, relative path for development
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// ═══════════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════════

async function startResearch(query: string): Promise<ResearchResponse> {
    // Sanitize query: remove control characters that cause JSON decode errors
    const sanitizedQuery = query
        .replace(/[\x00-\x1F\x7F]/g, ' ')  // Remove control characters
        .replace(/\s+/g, ' ')              // Collapse multiple spaces
        .trim();

    const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: sanitizedQuery }),
    });

    if (!response.ok) {
        // Check if response is HTML (common proxy misconfiguration)
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('text/html')) {
            throw new Error(
                'Server returned HTML instead of JSON. Check Nginx/proxy configuration. ' +
                'See docs/NGINX_CONFIG.md for setup guide.'
            );
        }
        throw new Error(`Failed to start research (${response.status})`);
    }

    // Safely parse JSON with error handling
    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch {
        if (text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
            throw new Error(
                'API returned HTML page instead of JSON. ' +
                'Backend may not be running or Nginx proxy is misconfigured.'
            );
        }
        throw new Error('Invalid response from server');
    }
}

// ═══════════════════════════════════════════════════════════════════
// Platform Icon Component
// ═══════════════════════════════════════════════════════════════════

function XIcon({ size = 24 }: { size?: number }) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
    );
}

const platformIcons: Record<string, React.ReactNode> = {
    search: <Search size={20} />,
    instagram: <Instagram size={20} />,
    linkedin: <Linkedin size={20} />,
    youtube: <Youtube size={20} />,
    x: <XIcon size={20} />,
    web: <Globe size={20} />,
    synthesis: <Activity size={20} />,
};

const platformLabels: Record<string, string> = {
    search: 'Search',
    instagram: 'Instagram',
    linkedin: 'LinkedIn',
    youtube: 'YouTube',
    x: 'X / Twitter',
    web: 'Web',
    synthesis: 'Synthesis',
};

// ═══════════════════════════════════════════════════════════════════
// TopBar Component
// ═══════════════════════════════════════════════════════════════════

interface TopBarProps {
    isResearching: boolean;
    onBack: () => void;
}

function TopBar({ isResearching, onBack }: TopBarProps) {
    return (
        <header className="top-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                <motion.button
                    onClick={onBack}
                    className="back-button"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-sm)',
                        padding: 'var(--space-sm) var(--space-md)',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-default)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all var(--transition-normal)',
                        fontSize: '0.875rem',
                        fontFamily: 'var(--font-sans)',
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--accent-neon)';
                        e.currentTarget.style.color = 'var(--accent-neon)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border-default)';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                >
                    <ArrowLeft size={16} />
                    Back to Home
                </motion.button>
                <div className="logo">
                    <div className="logo-icon">
                        <Zap size={22} color="#FAFAFA" />
                    </div>
                    <h1 className="logo-text">
                        DEEP<span>RESEARCHER</span>
                    </h1>
                </div>
            </div>

            <div className="status-indicator">
                <div className={`status-dot ${isResearching ? 'active' : ''}`} />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {isResearching ? 'Researching...' : 'Ready'}
                </span>
            </div>
        </header>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Sidebar Component
// ═══════════════════════════════════════════════════════════════════

interface SidebarProps {
    agents: AgentsState;
}

function Sidebar({ agents }: SidebarProps) {
    const platforms: (keyof AgentsState)[] = ['instagram', 'linkedin', 'youtube', 'x', 'web'];

    return (
        <aside className="sidebar">
            {platforms.map((platform) => {
                const status = agents[platform]?.status || 'waiting';
                return (
                    <motion.div
                        key={platform}
                        className={`platform-icon ${status}`}
                        title={platformLabels[platform]}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        {platformIcons[platform]}
                    </motion.div>
                );
            })}
        </aside>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Command Center Component
// ═══════════════════════════════════════════════════════════════════

interface CommandCenterProps {
    onSubmit: (query: string) => void;
    isLoading: boolean;
    result: string | null;
    agents: AgentsState;
}

function CommandCenter({ onSubmit, isLoading, result, agents }: CommandCenterProps) {
    const [query, setQuery] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isLoading) {
            onSubmit(query.trim());
        }
    };

    const copyToClipboard = () => {
        if (result) {
            navigator.clipboard.writeText(result);
        }
    };

    const downloadResult = () => {
        if (result) {
            const blob = new Blob([result], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'research-results.md';
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    return (
        <main className="main-content">
            <div className="command-center">
                <div className="command-header">
                    <h1>Multiplatform Deep Research</h1>
                    <p>Powered by MCP agents exploring Instagram, LinkedIn, YouTube, X, and the open web</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="input-container">
                        <textarea
                            className="research-input"
                            placeholder="Enter your research query... (e.g., 'Latest trends in AI development')"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <motion.button
                        type="submit"
                        className="start-button"
                        disabled={isLoading || !query.trim()}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        {isLoading ? (
                            <>
                                <Activity size={18} className="animate-spin" />
                                Researching...
                            </>
                        ) : (
                            <>
                                <Zap size={18} />
                                Start Deep Research
                            </>
                        )}
                    </motion.button>
                </form>

                <AnimatePresence>
                    {result && (
                        <motion.div
                            className="results-section"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <div className="results-header">
                                <h2>Research Results</h2>
                                <div className="results-actions">
                                    <button className="action-button" onClick={copyToClipboard}>
                                        <Copy size={14} />
                                        Copy
                                    </button>
                                    <button className="action-button" onClick={downloadResult}>
                                        <Download size={14} />
                                        Export
                                    </button>
                                </div>
                            </div>

                            <div className="results-content">
                                <ReactMarkdown>{result}</ReactMarkdown>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Enhanced Loading State - Show if loading OR any agents are active */}
                {((isLoading || Object.values(agents).some(a => a.status === 'running')) && !result) && (
                    <motion.div
                        className="results-section"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <div className="results-header">
                            <h2>🔍 Research in Progress</h2>
                            <div className="loading-status">
                                <motion.div
                                    className="loading-pulse"
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 1.5, repeat: Infinity }}
                                />
                                <span>
                                    {Object.values(agents).some(a => a.status === 'running')
                                        ? 'Analyzing...'
                                        : 'Initializing...'}
                                </span>
                            </div>
                        </div>

                        <div className="results-content loading-content">
                            {/* Active Agent Status */}
                            {(() => {
                                const runningAgents = Object.values(agents).filter(
                                    agent => agent.status === 'running'
                                );
                                const activeAgents = Object.values(agents).filter(
                                    agent => agent.status === 'running' || agent.status === 'done'
                                );

                                return (
                                    <>
                                        {(runningAgents.length > 0 || isLoading) && (
                                            <div className="agent-progress">
                                                <h3 style={{ 
                                                    color: 'var(--accent-neon)', 
                                                    marginBottom: 'var(--space-md)',
                                                    fontSize: '0.9rem',
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '1px'
                                                }}>
                                                    {runningAgents.length > 0 ? '🤖 Active Agents' : '⏳ Starting Research...'}
                                                </h3>
                                                {runningAgents.length === 0 && isLoading && (
                                                    <motion.div
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        style={{
                                                            padding: 'var(--space-md)',
                                                            textAlign: 'center',
                                                            color: 'var(--text-secondary)',
                                                            fontSize: '0.875rem',
                                                        }}
                                                    >
                                                        <motion.span
                                                            animate={{ opacity: [0.5, 1, 0.5] }}
                                                            transition={{ duration: 1.5, repeat: Infinity }}
                                                        >
                                                            Connecting to research agents...
                                                        </motion.span>
                                                    </motion.div>
                                                )}
                                                {runningAgents.map((agent) => (
                                                    <motion.div
                                                        key={agent.id}
                                                        className="agent-status-item"
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        style={{
                                                            padding: 'var(--space-sm) var(--space-md)',
                                                            marginBottom: 'var(--space-sm)',
                                                            background: 'var(--bg-elevated)',
                                                            border: '1px solid var(--accent-neon)',
                                                            borderRadius: 'var(--radius-md)',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: 'var(--space-sm)',
                                                        }}
                                                    >
                                                        <motion.div
                                                            className="status-indicator"
                                                            animate={{ 
                                                                opacity: [0.5, 1, 0.5],
                                                                scale: [1, 1.1, 1]
                                                            }}
                                                            transition={{ 
                                                                duration: 1.5, 
                                                                repeat: Infinity 
                                                            }}
                                                            style={{
                                                                width: '8px',
                                                                height: '8px',
                                                                borderRadius: '50%',
                                                                background: 'var(--accent-neon)',
                                                                boxShadow: '0 0 8px var(--accent-neon)',
                                                            }}
                                                        />
                                                        <span style={{ 
                                                            color: 'var(--text-primary)',
                                                            fontSize: '0.875rem',
                                                            textTransform: 'capitalize'
                                                        }}>
                                                            {agent.platform}
                                                        </span>
                                                        {agent.message && (
                                                            <span style={{ 
                                                                color: 'var(--text-secondary)',
                                                                fontSize: '0.75rem',
                                                                marginLeft: 'auto',
                                                                fontStyle: 'italic'
                                                            }}>
                                                                {agent.message}
                                                            </span>
                                                        )}
                                                    </motion.div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Progress Animation */}
                                        <div className="research-progress">
                                            <div className="progress-steps">
                                                {[
                                                    { name: 'Search', agentId: 'search' },
                                                    { name: 'Extract', agentId: 'instagram' }, // Using first platform as representative
                                                    { name: 'Analyze', agentId: 'synthesis' },
                                                    { name: 'Synthesize', agentId: 'synthesis' }
                                                ].map((step, index) => {
                                                    // Check if any extraction agents are active (instagram, linkedin, youtube, x, web)
                                                    const extractionAgents = ['instagram', 'linkedin', 'youtube', 'x', 'web'];
                                                    const anyExtractionActive = extractionAgents.some(
                                                        id => agents[id as keyof AgentsState]?.status === 'running'
                                                    );
                                                    const anyExtractionDone = extractionAgents.some(
                                                        id => agents[id as keyof AgentsState]?.status === 'done'
                                                    );
                                                    
                                                    const stepAgent = agents[step.agentId as keyof AgentsState];
                                                    let stepActive = false;
                                                    let stepDone = false;
                                                    
                                                    if (step.agentId === 'search') {
                                                        stepActive = stepAgent?.status === 'running';
                                                        stepDone = stepAgent?.status === 'done';
                                                    } else if (step.name === 'Extract') {
                                                        stepActive = anyExtractionActive;
                                                        stepDone = anyExtractionDone;
                                                    } else if (step.name === 'Analyze' || step.name === 'Synthesize') {
                                                        stepActive = stepAgent?.status === 'running';
                                                        stepDone = stepAgent?.status === 'done';
                                                    }
                                                    
                                                    return (
                                                        <motion.div
                                                            key={step}
                                                            className="progress-step"
                                                            initial={{ opacity: 0.3 }}
                                                            animate={{ 
                                                                opacity: stepActive ? 1 : 0.3,
                                                                scale: stepActive ? 1.05 : 1
                                                            }}
                                                            style={{
                                                                display: 'flex',
                                                                flexDirection: 'column',
                                                                alignItems: 'center',
                                                                gap: 'var(--space-xs)',
                                                                flex: 1,
                                                            }}
                                                        >
                                                            <motion.div
                                                                className="step-indicator"
                                                                animate={stepActive ? {
                                                                    borderColor: 'var(--accent-neon)',
                                                                    boxShadow: '0 0 12px var(--accent-neon)',
                                                                } : {}}
                                                                style={{
                                                                    width: '40px',
                                                                    height: '40px',
                                                                    borderRadius: '50%',
                                                                    border: `2px solid ${stepDone ? 'var(--accent-neon)' : 'var(--border-default)'}`,
                                                                    background: stepDone ? 'var(--accent-neon)' : 'transparent',
                                                                    display: 'flex',
                                                                    alignItems: 'center',
                                                                    justifyContent: 'center',
                                                                    position: 'relative',
                                                                }}
                                                            >
                                                                {stepDone ? (
                                                                    <motion.div
                                                                        initial={{ scale: 0 }}
                                                                        animate={{ scale: 1 }}
                                                                        style={{
                                                                            width: '12px',
                                                                            height: '12px',
                                                                            background: 'var(--bg-primary)',
                                                                            borderRadius: '50%',
                                                                        }}
                                                                    />
                                                                ) : stepActive ? (
                                                                    <motion.div
                                                                        animate={{ rotate: 360 }}
                                                                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                                                        style={{
                                                                            width: '16px',
                                                                            height: '16px',
                                                                            border: '2px solid var(--accent-neon)',
                                                                            borderTopColor: 'transparent',
                                                                            borderRadius: '50%',
                                                                        }}
                                                                    />
                                                                ) : null}
                                                            </motion.div>
                                                            <span style={{
                                                                fontSize: '0.75rem',
                                                                color: stepActive ? 'var(--accent-neon)' : 'var(--text-secondary)',
                                                                textTransform: 'uppercase',
                                                                letterSpacing: '0.5px',
                                                            }}>
                                                                {step.name}
                                                            </span>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        {/* Animated Loading Text */}
                                        <motion.div
                                            className="loading-message"
                                            style={{
                                                marginTop: 'var(--space-xl)',
                                                textAlign: 'center',
                                                color: 'var(--text-secondary)',
                                            }}
                                        >
                                            <motion.span
                                                animate={{ opacity: [0.5, 1, 0.5] }}
                                                transition={{ duration: 2, repeat: Infinity }}
                                            >
                                                {runningAgents.length > 0 
                                                    ? `📊 Gathering data from ${runningAgents.map(a => a.platform).join(', ')}...`
                                                    : '🚀 Initializing research agents...'
                                                }
                                            </motion.span>
                                        </motion.div>

                                        {/* Skeleton Content Preview */}
                                        <div className="skeleton-preview" style={{ marginTop: 'var(--space-xl)' }}>
                                            <div className="skeleton skeleton-text" style={{ width: '80%', height: '20px' }} />
                                            <div className="skeleton skeleton-text" style={{ width: '60%', height: '20px', marginTop: 'var(--space-md)' }} />
                                            <div className="skeleton skeleton-text" style={{ width: '90%', height: '20px', marginTop: 'var(--space-md)' }} />
                                            <div className="skeleton skeleton-text" style={{ width: '70%', height: '20px', marginTop: 'var(--space-md)' }} />
                                            <div className="skeleton skeleton-text" style={{ width: '85%', height: '20px', marginTop: 'var(--space-md)' }} />
                                        </div>
                                    </>
                                );
                            })()}
                        </div>
                    </motion.div>
                )}
            </div>
        </main>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Agent Panel Component
// ═══════════════════════════════════════════════════════════════════

interface AgentPanelProps {
    agents: AgentsState;
}

function AgentPanel({ agents }: AgentPanelProps) {
    const agentOrder: (keyof AgentsState)[] = ['search', 'instagram', 'linkedin', 'youtube', 'x', 'web', 'synthesis'];

    return (
        <aside className="agent-panel">
            <div className="agent-panel-header">
                <Activity size={16} color="var(--accent-neon)" />
                <h2>Agent Activity</h2>
            </div>

            <div className="agent-cards">
                {agentOrder.map((agentId, index) => {
                    const agent = agents[agentId];
                    if (!agent) return null;

                    return (
                        <motion.div
                            key={agentId}
                            className={`agent-card ${agent.status}`}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <div className="agent-card-header">
                                <div className="agent-name">
                                    {platformIcons[agentId]}
                                    {platformLabels[agentId]}
                                </div>
                                <div className="agent-status-container">
                                    {agent.status === 'running' && (
                                        <Activity size={14} className="animate-spin" style={{ marginRight: '8px' }} />
                                    )}
                                    <span className={`agent-status-badge ${agent.status}`}>
                                        {agent.status}
                                    </span>
                                </div>
                            </div>
                            {agent.message && (
                                <p className="agent-message">
                                    {agent.status === 'running' ? (
                                        <span className="typing-effect">{agent.message}</span>
                                    ) : (
                                        agent.message
                                    )}
                                </p>
                            )}
                        </motion.div>
                    );
                })}
            </div>
        </aside>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Main App Component
// ═══════════════════════════════════════════════════════════════════

type NavigationState = 'landing' | 'dashboard' | 'privacy' | 'terms';

function App() {
    const [navigation, setNavigation] = useState<NavigationState>('landing');
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isResearching, setIsResearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { agents, result, reset } = useWebSocket(sessionId);

    const handleStartResearch = useCallback(async (query: string) => {
        try {
            setError(null);
            setIsResearching(true);
            reset();

            const response = await startResearch(query);
            setSessionId(response.session_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start research');
            setIsResearching(false);
        }
    }, [reset]);

    // Keep loading state active if agents are still running
    const hasActiveAgents = Object.values(agents).some(
        agent => agent.status === 'running'
    );
    const hasResult = !!result;
    
    // Only stop loading when result arrives AND no agents are running
    if (hasResult && isResearching && !hasActiveAgents) {
        setIsResearching(false);
    }

    // Navigation handler
    const navigateTo = (page: NavigationState) => {
        setNavigation(page);
    };

    // Render based on navigation state
    if (navigation === 'landing') {
        return (
            <AnimatePresence mode="wait">
                <motion.div
                    key="landing"
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <LandingPage 
                        onEnter={() => navigateTo('dashboard')}
                        onNavigate={navigateTo}
                    />
                </motion.div>
            </AnimatePresence>
        );
    }

    if (navigation === 'privacy') {
        return (
            <AnimatePresence mode="wait">
                <motion.div
                    key="privacy"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <PrivacyPolicy onNavigate={navigateTo} />
                </motion.div>
            </AnimatePresence>
        );
    }

    if (navigation === 'terms') {
        return (
            <AnimatePresence mode="wait">
                <motion.div
                    key="terms"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <TermsAndConditions onNavigate={navigateTo} />
                </motion.div>
            </AnimatePresence>
        );
    }

    // Dashboard view
    return (
        <AnimatePresence mode="wait">
            <motion.div
                key="dashboard"
                className="app-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
            >
                <TopBar 
                    isResearching={isResearching} 
                    onBack={() => navigateTo('landing')}
                />
                <Sidebar agents={agents} />
                <CommandCenter
                    onSubmit={handleStartResearch}
                    isLoading={isResearching || hasActiveAgents}
                    result={result}
                    agents={agents}
                />
                <AgentPanel agents={agents} />
                <Footer onNavigate={navigateTo} />

                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{
                            position: 'fixed',
                            bottom: '20px',
                            left: '50%',
                            transform: 'translateX(-50%)',
                            background: 'var(--bg-card)',
                            border: '1px solid var(--status-error)',
                            borderRadius: 'var(--radius-md)',
                            padding: 'var(--space-md) var(--space-lg)',
                            color: 'var(--status-error)',
                            fontSize: '0.875rem',
                        }}
                    >
                        {error}
                    </motion.div>
                )}
            </motion.div>
        </AnimatePresence>
    );
}

export default App;
