import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap,
    Instagram,
    Linkedin,
    Youtube,
    Globe,
    ChevronRight,
    Sparkles,
    Brain,
    Layers,
    Shield,
    Clock,
    ArrowRight,
    Play,
    Star
} from 'lucide-react';
import Footer from './Footer';

// Custom X/Twitter Icon
function XIcon({ size = 24 }: { size?: number }) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Animated Background Component
// ═══════════════════════════════════════════════════════════════════

function AnimatedBackground() {
    return (
        <div className="landing-bg">
            {/* Animated gradient orbs */}
            <div className="orb orb-1" />
            <div className="orb orb-2" />
            <div className="orb orb-3" />

            {/* Grid overlay */}
            <div className="grid-overlay" />

            {/* Floating particles */}
            {Array.from({ length: 30 }).map((_, i) => (
                <motion.div
                    key={i}
                    className="particle"
                    initial={{
                        x: Math.random() * window.innerWidth,
                        y: Math.random() * window.innerHeight,
                        opacity: 0
                    }}
                    animate={{
                        y: [null, Math.random() * -200 - 100],
                        opacity: [0, 0.6, 0]
                    }}
                    transition={{
                        duration: 4 + Math.random() * 4,
                        repeat: Infinity,
                        delay: Math.random() * 5
                    }}
                    style={{
                        left: `${Math.random() * 100}%`,
                        width: `${2 + Math.random() * 4}px`,
                        height: `${2 + Math.random() * 4}px`,
                    }}
                />
            ))}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Platform Card Component
// ═══════════════════════════════════════════════════════════════════

interface PlatformCardProps {
    icon: React.ReactNode;
    name: string;
    description: string;
    color: string;
    delay: number;
}

function PlatformCard({ icon, name, description, color, delay }: PlatformCardProps) {
    return (
        <motion.div
            className="platform-card"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay }}
            whileHover={{ scale: 1.05, y: -5 }}
            style={{ '--glow-color': color } as React.CSSProperties}
        >
            <div className="platform-card-icon" style={{ color }}>
                {icon}
            </div>
            <h3 className="platform-card-name">{name}</h3>
            <p className="platform-card-desc">{description}</p>
        </motion.div>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Feature Card Component
// ═══════════════════════════════════════════════════════════════════

interface FeatureCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    delay: number;
}

function FeatureCard({ icon, title, description, delay }: FeatureCardProps) {
    return (
        <motion.div
            className="feature-card"
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay }}
        >
            <div className="feature-icon">{icon}</div>
            <div className="feature-content">
                <h3>{title}</h3>
                <p>{description}</p>
            </div>
        </motion.div>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Stats Counter Component
// ═══════════════════════════════════════════════════════════════════

function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const duration = 2000;
        const steps = 60;
        const increment = value / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                setCount(value);
                clearInterval(timer);
            } else {
                setCount(Math.floor(current));
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [value]);

    return <span>{count.toLocaleString()}{suffix}</span>;
}

// ═══════════════════════════════════════════════════════════════════
// Terminal Demo Component
// ═══════════════════════════════════════════════════════════════════

function TerminalDemo() {
    const [currentLine, setCurrentLine] = useState(0);
    const lines = [
        { type: 'command', text: '$ deep-research "Latest AI developments 2024"' },
        { type: 'info', text: '🔍 Scanning Instagram, LinkedIn, YouTube, X, Web...' },
        { type: 'success', text: '✓ Found 47 relevant sources' },
        { type: 'info', text: '🧠 Synthesizing with GPT-4o...' },
        { type: 'success', text: '✓ Research complete! Generated comprehensive report' },
    ];

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentLine(prev => (prev + 1) % (lines.length + 2));
        }, 1500);
        return () => clearInterval(timer);
    }, []);

    return (
        <motion.div
            className="terminal-demo"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
        >
            <div className="terminal-header">
                <div className="terminal-dots">
                    <span className="dot red" />
                    <span className="dot yellow" />
                    <span className="dot green" />
                </div>
                <span className="terminal-title">Deep Researcher Terminal</span>
            </div>
            <div className="terminal-body">
                <AnimatePresence mode="popLayout">
                    {lines.slice(0, currentLine + 1).map((line, i) => (
                        <motion.div
                            key={i}
                            className={`terminal-line ${line.type}`}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            {line.text}
                        </motion.div>
                    ))}
                </AnimatePresence>
                <motion.span
                    className="cursor"
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                >
                    █
                </motion.span>
            </div>
        </motion.div>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Main Landing Page Component
// ═══════════════════════════════════════════════════════════════════

interface LandingPageProps {
    onEnter: () => void;
    onNavigate: (page: 'landing' | 'dashboard' | 'privacy' | 'terms') => void;
}

export default function LandingPage({ onEnter, onNavigate }: LandingPageProps) {
    const [isHovering, setIsHovering] = useState(false);

    const platforms = [
        { icon: <Instagram size={32} />, name: 'Instagram', description: 'Trends, influencers & visual content', color: '#E1306C' },
        { icon: <Linkedin size={32} />, name: 'LinkedIn', description: 'Professional insights & industry news', color: '#0A66C2' },
        { icon: <Youtube size={32} />, name: 'YouTube', description: 'Videos, tutorials & discussions', color: '#FF0000' },
        { icon: <XIcon size={32} />, name: 'X / Twitter', description: 'Real-time conversations & news', color: '#ffffff' },
        { icon: <Globe size={32} />, name: 'Web', description: 'Articles, blogs & documentation', color: '#00ffaa' },
    ];

    const features = [
        { icon: <Brain size={24} />, title: 'AI-Powered Analysis', description: 'GPT-4o and Gemini 2.0 synthesize findings into comprehensive reports' },
        { icon: <Layers size={24} />, title: 'Multi-Platform Fusion', description: 'Aggregate data from 5+ platforms in a single query' },
        { icon: <Shield size={24} />, title: 'Enterprise Security', description: 'Your queries and data remain private and secure' },
        { icon: <Clock size={24} />, title: 'Real-Time Updates', description: 'Watch agents work live with WebSocket streaming' },
    ];

    return (
        <div className="landing-page">
            <AnimatedBackground />

            {/* ─────────────────────────────────────────────────────── */}
            {/* Navigation */}
            {/* ─────────────────────────────────────────────────────── */}
            <nav className="landing-nav">
                <motion.div
                    className="nav-logo"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <Zap size={28} className="logo-icon" />
                    <span>DEEP RESEARCHER</span>
                </motion.div>
                <motion.div
                    className="nav-links"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <a href="#features">Features</a>
                    <a href="#platforms">Platforms</a>
                    <a href="#demo">Demo</a>
                    <button className="nav-cta" onClick={onEnter}>
                        Launch App <ChevronRight size={16} />
                    </button>
                </motion.div>
            </nav>

            {/* ─────────────────────────────────────────────────────── */}
            {/* Hero Section */}
            {/* ─────────────────────────────────────────────────────── */}
            <section className="hero-section">
                <motion.div
                    className="hero-badge"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                >
                    <Sparkles size={14} />
                    <span>Powered by GPT-4o & Bright Data MCP</span>
                </motion.div>

                <motion.h1
                    className="hero-title"
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                >
                    <span className="gradient-text">Deep Research</span>
                    <br />
                    Across Every Platform
                </motion.h1>

                <motion.p
                    className="hero-subtitle"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                >
                    Harness the power of AI agents to explore Instagram, LinkedIn, YouTube, X,
                    and the open web simultaneously. Get comprehensive insights in seconds.
                </motion.p>

                <motion.div
                    className="hero-actions"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.7 }}
                >
                    <motion.button
                        className="primary-btn"
                        onClick={onEnter}
                        onMouseEnter={() => setIsHovering(true)}
                        onMouseLeave={() => setIsHovering(false)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        <span>Start Researching</span>
                        <motion.span
                            animate={{ x: isHovering ? 5 : 0 }}
                            transition={{ duration: 0.2 }}
                        >
                            <ArrowRight size={20} />
                        </motion.span>
                    </motion.button>
                    <motion.button
                        className="secondary-btn"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        <Play size={18} />
                        <span>Watch Demo</span>
                    </motion.button>
                </motion.div>

                {/* Stats */}
                <motion.div
                    className="hero-stats"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8, delay: 1 }}
                >
                    <div className="stat">
                        <span className="stat-value"><AnimatedCounter value={5} />+</span>
                        <span className="stat-label">Platforms</span>
                    </div>
                    <div className="stat-divider" />
                    <div className="stat">
                        <span className="stat-value"><AnimatedCounter value={1000} suffix="+" /></span>
                        <span className="stat-label">Sources Analyzed</span>
                    </div>
                    <div className="stat-divider" />
                    <div className="stat">
                        <span className="stat-value"><AnimatedCounter value={100} suffix="%" /></span>
                        <span className="stat-label">AI Powered</span>
                    </div>
                </motion.div>
            </section>

            {/* ─────────────────────────────────────────────────────── */}
            {/* Platforms Section */}
            {/* ─────────────────────────────────────────────────────── */}
            <section id="platforms" className="platforms-section">
                <motion.div
                    className="section-header"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2>Research <span className="gradient-text">Everywhere</span></h2>
                    <p>One query. Multiple platforms. Unified insights.</p>
                </motion.div>

                <div className="platforms-grid">
                    {platforms.map((platform, i) => (
                        <PlatformCard
                            key={platform.name}
                            {...platform}
                            delay={i * 0.1}
                        />
                    ))}
                </div>
            </section>

            {/* ─────────────────────────────────────────────────────── */}
            {/* Features Section */}
            {/* ─────────────────────────────────────────────────────── */}
            <section id="features" className="features-section">
                <div className="features-content">
                    <motion.div
                        className="features-text"
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <h2>Built for <span className="gradient-text">Intelligence</span></h2>
                        <p>
                            Deep Researcher combines cutting-edge AI models with real-time
                            web scraping to deliver research that would take hours in seconds.
                        </p>
                        <div className="features-list">
                            {features.map((feature, i) => (
                                <FeatureCard key={feature.title} {...feature} delay={i * 0.1} />
                            ))}
                        </div>
                    </motion.div>
                    <div className="features-demo" id="demo">
                        <TerminalDemo />
                    </div>
                </div>
            </section>

            {/* ─────────────────────────────────────────────────────── */}
            {/* CTA Section */}
            {/* ─────────────────────────────────────────────────────── */}
            <section className="cta-section">
                <motion.div
                    className="cta-content"
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <div className="cta-stars">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <Star key={i} size={24} fill="#ffd700" color="#ffd700" />
                        ))}
                    </div>
                    <h2>Ready to Transform Your Research?</h2>
                    <p>Join the future of AI-powered intelligence gathering</p>
                    <motion.button
                        className="cta-btn"
                        onClick={onEnter}
                        whileHover={{ scale: 1.05, boxShadow: '0 0 40px rgba(255, 0, 128, 0.5)' }}
                        whileTap={{ scale: 0.98 }}
                    >
                        <Zap size={20} />
                        Launch Deep Researcher
                    </motion.button>
                </motion.div>
            </section>

            {/* ─────────────────────────────────────────────────────── */}
            {/* Footer */}
            {/* ─────────────────────────────────────────────────────── */}
            <Footer onNavigate={onNavigate} />
        </div>
    );
}
