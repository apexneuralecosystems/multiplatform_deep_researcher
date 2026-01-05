import { motion } from 'framer-motion';

interface FooterProps {
    onNavigate: (page: 'landing' | 'dashboard' | 'privacy' | 'terms') => void;
}

export default function Footer({ onNavigate }: FooterProps) {
    return (
        <footer className="app-footer">
            <div className="footer-divider"></div>
            <div className="footer-content-wrapper">
                <div className="footer-links">
                    <motion.button
                        onClick={() => onNavigate('privacy')}
                        className="footer-link"
                        whileHover={{ color: 'var(--accent-neon)' }}
                        transition={{ duration: 0.2 }}
                    >
                        Privacy Policy
                    </motion.button>
                    <span className="footer-separator">|</span>
                    <motion.button
                        onClick={() => onNavigate('terms')}
                        className="footer-link"
                        whileHover={{ color: 'var(--accent-neon)' }}
                        transition={{ duration: 0.2 }}
                    >
                        Terms & Conditions
                    </motion.button>
                </div>
                <p className="footer-copyright">© 2025 ApexNeural. All rights reserved.</p>
            </div>
        </footer>
    );
}

