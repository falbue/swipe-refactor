// API Client for communication with backend

class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    // Auth endpoints
    async getMe() {
        return this.request('/api/auth/me');
    }

    async githubCallback(code, state) {
        return this.request('/api/auth/github/callback', {
            method: 'POST',
            body: JSON.stringify({ code, state }),
        });
    }

    // Session endpoints
    async createSession(repoFullName) {
        return this.request('/api/session/', {
            method: 'POST',
            body: JSON.stringify({ repo_full_name: repoFullName }),
        });
    }

    async getSession(sessionId) {
        return this.request(`/api/session/${sessionId}`);
    }

    async getRandomCard(sessionId) {
        return this.request(`/api/session/${sessionId}/cards/random`);
    }

    async createPullRequest(sessionId) {
        return this.request(`/api/session/${sessionId}/create-pr`, {
            method: 'POST',
        });
    }

    // Card endpoints
    async approveCard(cardId) {
        return this.request(`/api/cards/${cardId}/approve`, {
            method: 'POST',
        });
    }

    async editCard(cardId, editedContent) {
        return this.request(`/api/cards/${cardId}/edit`, {
            method: 'POST',
            body: JSON.stringify({ edited_content: editedContent }),
        });
    }

    async skipCard(cardId) {
        return this.request(`/api/cards/${cardId}/skip`, {
            method: 'POST',
        });
    }

    async publishGist(cardHash) {
        return this.request(`/api/cards/${cardHash}/publish-as-gist`, {
            method: 'POST',
        });
    }

    async likeCard(cardHash) {
        return this.request(`/api/cards/${cardHash}/like`, {
            method: 'POST',
        });
    }

    // Recommendations
    async getRecommendations() {
        return this.request('/api/recommendations');
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }
}

// Global API client instance
const apiClient = new APIClient();
