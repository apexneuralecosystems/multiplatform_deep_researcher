import { useState, useEffect, useCallback, useRef } from 'react';
import type { WebSocketMessage, AgentsState, AgentStatus } from '../types';

// WebSocket URL configuration
function getWebSocketUrl(sessionId: string): string {
    // 1. Try explicit WebSocket URL
    const wsBaseUrl = import.meta.env.VITE_WS_URL;
    if (wsBaseUrl) {
        console.log('[WS] Using VITE_WS_URL:', wsBaseUrl);
        return `${wsBaseUrl}/ws/research/${sessionId}`;
    }

    // 2. Try falling back to API URL (converting http->ws, https->wss)
    const apiBaseUrl = import.meta.env.VITE_API_URL;
    if (apiBaseUrl) {
        const wsUrl = apiBaseUrl.replace(/^http/, 'ws');
        console.log('[WS] derived from VITE_API_URL:', wsUrl);
        return `${wsUrl}/ws/research/${sessionId}`;
    }

    // 3. Development/Self-host: use same host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/research/${sessionId}`;
    console.log('[WS] Using window location:', wsUrl);
    return wsUrl;
}

const initialAgents: AgentsState = {
    search: { id: 'search', platform: 'search', status: 'waiting' },
    instagram: { id: 'instagram', platform: 'instagram', status: 'waiting' },
    linkedin: { id: 'linkedin', platform: 'linkedin', status: 'waiting' },
    youtube: { id: 'youtube', platform: 'youtube', status: 'waiting' },
    x: { id: 'x', platform: 'x', status: 'waiting' },
    web: { id: 'web', platform: 'web', status: 'waiting' },
    synthesis: { id: 'synthesis', platform: 'synthesis', status: 'waiting' },
};

export function useWebSocket(sessionId: string | null) {
    const [agents, setAgents] = useState<AgentsState>(initialAgents);
    const [result, setResult] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const pingIntervalRef = useRef<number | null>(null);

    const connect = useCallback(() => {
        if (!sessionId || wsRef.current?.readyState === WebSocket.OPEN) return;

        const wsUrl = getWebSocketUrl(sessionId);
        console.log('[WS] Connecting to:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('[WS] Connected');
            setIsConnected(true);
            setError(null);

            // Start ping interval
            pingIntervalRef.current = window.setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 25000);
        };

        ws.onmessage = (event) => {
            try {
                const data: WebSocketMessage = JSON.parse(event.data);
                console.log('[WS] Message:', data);

                switch (data.type) {
                    case 'initial_state':
                        if (data.agents) {
                            setAgents(prev => {
                                const updated = { ...prev };
                                Object.entries(data.agents!).forEach(([key, value]) => {
                                    if (key in updated) {
                                        updated[key as keyof AgentsState] = {
                                            id: key,
                                            platform: value.platform,
                                            status: value.status as AgentStatus,
                                            message: value.message,
                                        };
                                    }
                                });
                                return updated;
                            });
                        }
                        break;

                    case 'agent_update':
                        if (data.agent_id && data.status) {
                            setAgents(prev => ({
                                ...prev,
                                [data.agent_id!]: {
                                    ...prev[data.agent_id! as keyof AgentsState],
                                    status: data.status as AgentStatus,
                                    message: data.message,
                                },
                            }));
                        }
                        break;

                    case 'research_complete':
                        if (data.result) {
                            setResult(data.result);
                        }
                        break;

                    case 'error':
                        setError(data.message || 'An error occurred');
                        break;

                    case 'heartbeat':
                        // Keep alive, no action needed
                        break;
                }
            } catch (e) {
                // Not JSON (probably pong response)
                if (event.data !== 'pong') {
                    console.log('[WS] Non-JSON message:', event.data);
                }
            }
        };

        ws.onerror = (event) => {
            console.error('[WS] Error:', event);
            setError('WebSocket connection error');
        };

        ws.onclose = () => {
            console.log('[WS] Disconnected');
            setIsConnected(false);
            if (pingIntervalRef.current) {
                clearInterval(pingIntervalRef.current);
            }
        };

        wsRef.current = ws;
    }, [sessionId]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }
    }, []);

    const reset = useCallback(() => {
        setAgents(initialAgents);
        setResult(null);
        setError(null);
    }, []);

    useEffect(() => {
        if (sessionId) {
            connect();
        }
        return () => {
            disconnect();
        };
    }, [sessionId, connect, disconnect]);

    return {
        agents,
        result,
        isConnected,
        error,
        reset,
    };
}
