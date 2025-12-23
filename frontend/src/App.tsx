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
    Activity
} from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import type { AgentsState, ResearchResponse } from './types';
import LandingPage from './components/LandingPage';
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
}

function TopBar({ isResearching }: TopBarProps) {
    return (
        <header className="top-bar">
            <div className="logo">
                <div className="logo-icon">
                    <Zap size={22} color="#FAFAFA" />
                </div>
                <h1 className="logo-text">
                    DEEP<span>RESEARCHER</span>
                </h1>
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
}

function CommandCenter({ onSubmit, isLoading, result }: CommandCenterProps) {
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

                {isLoading && !result && (
                    <div className="results-section">
                        <div className="results-content">
                            <div className="skeleton skeleton-text" style={{ width: '80%' }} />
                            <div className="skeleton skeleton-text" style={{ width: '60%' }} />
                            <div className="skeleton skeleton-text" style={{ width: '90%' }} />
                            <div className="skeleton skeleton-text" style={{ width: '70%' }} />
                        </div>
                    </div>
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
                                <span className={`agent-status-badge ${agent.status}`}>
                                    {agent.status}
                                </span>
                            </div>
                            {agent.message && (
                                <p className="agent-message">{agent.message}</p>
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

function App() {
    const [showLanding, setShowLanding] = useState(true);
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

    // Stop loading when result arrives
    const hasResult = !!result;
    if (hasResult && isResearching) {
        setIsResearching(false);
    }

    // Show landing page first
    if (showLanding) {
        return (
            <AnimatePresence mode="wait">
                <motion.div
                    key="landing"
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <LandingPage onEnter={() => setShowLanding(false)} />
                </motion.div>
            </AnimatePresence>
        );
    }

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key="dashboard"
                className="app-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
            >
                <TopBar isResearching={isResearching} />
                <Sidebar agents={agents} />
                <CommandCenter
                    onSubmit={handleStartResearch}
                    isLoading={isResearching}
                    result={result}
                />
                <AgentPanel agents={agents} />

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
