// ═══════════════════════════════════════════════════════════════════
// Type Definitions for Multiplatform Deep Researcher
// ═══════════════════════════════════════════════════════════════════

export type Platform = 'instagram' | 'linkedin' | 'youtube' | 'x' | 'web';

export type AgentStatus = 'waiting' | 'running' | 'done' | 'error';

export interface Agent {
    id: string;
    platform: string;
    status: AgentStatus;
    message?: string;
}

export interface AgentsState {
    search: Agent;
    instagram: Agent;
    linkedin: Agent;
    youtube: Agent;
    x: Agent;
    web: Agent;
    synthesis: Agent;
}

export interface ResearchSession {
    sessionId: string;
    query: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    agents: AgentsState;
    result?: string;
}

export interface WebSocketMessage {
    type: 'initial_state' | 'agent_update' | 'flow_started' | 'research_complete' | 'error' | 'heartbeat';
    agent_id?: string;
    status?: AgentStatus;
    message?: string;
    result?: string;
    agents?: Record<string, { status: AgentStatus; platform: string; message?: string }>;
}

export interface ResearchRequest {
    query: string;
    brightdata_api_key?: string;
}

export interface ResearchResponse {
    session_id: string;
    status: string;
    message: string;
}
