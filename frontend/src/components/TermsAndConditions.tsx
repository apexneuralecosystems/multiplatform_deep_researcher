import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft } from 'lucide-react';
import Footer from './Footer';
import './PrivacyPolicy.css'; // Reuse styles

interface TermsAndConditionsProps {
    onNavigate: (page: 'landing' | 'dashboard' | 'privacy' | 'terms') => void;
}

export default function TermsAndConditions({ onNavigate }: TermsAndConditionsProps) {
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/TERMS_AND_CONDITIONS.md')
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch');
                return res.text();
            })
            .then(text => {
                setContent(text);
                setLoading(false);
            })
            .catch(() => {
                setContent('# Terms and Conditions\n\n*Content will be loaded from TERMS_AND_CONDITIONS.md*');
                setLoading(false);
            });
    }, []);

    return (
        <div className="legal-page">
            <motion.button
                onClick={() => onNavigate('landing')}
                className="back-button-legal"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
            >
                <ArrowLeft size={16} />
                Back to Home
            </motion.button>
            <motion.div
                className="legal-content"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                {loading ? (
                    <div className="loading">Loading...</div>
                ) : (
                    <ReactMarkdown>{content}</ReactMarkdown>
                )}
            </motion.div>
            <Footer onNavigate={onNavigate} />
        </div>
    );
}

