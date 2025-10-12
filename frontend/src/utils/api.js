import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:80', // This should be the address of your backend
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getDashboardData(sessionId = null) {
        const params = sessionId ? { session_id: sessionId } : {};
        return apiClient.get('/api/dashboard-data', { params });
    },

    loadGraphs(directory, shapes_file, report_file) {
        return apiClient.post('/api/landing/load-graphs', {
            directory,
            shapes_file,
            report_file,
        });
    },

    // Upload files for validation
    uploadFiles(files) {
        const formData = new FormData();
        formData.append('dataFile', files.dataFile);
        formData.append('shapesFile', files.shapesFile);

        return apiClient.post('/api/upload/files', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Get violations data
    getViolations(sessionId = null) {
        const params = sessionId ? { session_id: sessionId } : {};
        return apiClient.get('/api/violations', { params });
    },

    // PHOENIX AI Configuration
    configureAI(config) {
        return apiClient.post('/api/phoenix/configure', config);
    },

    // PHOENIX Validation
    validateData(data, shapes) {
        return apiClient.post('/api/phoenix/validate', {
            data,
            shapes
        });
    },

    // Get AI explanation for violation
    getExplanation(violation) {
        return apiClient.post('/api/phoenix/explain', violation);
    },

    // Get AI repair suggestion
    getRepairSuggestion(violation) {
        return apiClient.post('/api/phoenix/repair-suggestion', violation);
    },

    // Apply repair
    applyRepair(repair) {
        return apiClient.post('/api/phoenix/apply-repair', repair);
    },

    // Get violation knowledge graph
    getViolationKG() {
        return apiClient.get('/api/phoenix/violation-kg');
    },

    // Configuration endpoints
    getConfig() {
        return apiClient.get('/api/config');
    },

    updateConfig(config) {
        return apiClient.post('/api/config', config);
    },

    // Generic POST method for custom endpoints
    post(endpoint, data) {
        return apiClient.post(endpoint, data);
    },

    // Generic GET method for custom endpoints
    get(endpoint, params = {}) {
        return apiClient.get(endpoint, { params });
    },

    // Explanation and Repair endpoints (newly added)
    postExplanation(violation, sessionId) {
        return apiClient.post('/api/explanation', {
            violation: violation,
            session_id: sessionId
        });
    },

    postRepair(repairQuery, sessionId) {
        return apiClient.post('/api/repair', {
            repair_query: repairQuery,
            session_id: sessionId
        });
    },

    getExplanations(sessionId) {
        return apiClient.get(`/api/explanations/${sessionId}`);
    },
};
