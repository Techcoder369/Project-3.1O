/**
 * API Service for Intelligence DCET Quiz Generator
 * Handles all API calls to the backend
 */

const API_BASE = ''; // same-origin (Flask)

/* ===============================
   AUTH HEADER
================================ */
function getAuthHeader() {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/* ===============================
   CORE REQUEST HANDLER
================================ */
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
        ...(options.headers || {})
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        // 🔒 Handle empty response safely
        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            data = { success: false, message: "Invalid server response" };
        }

        // 🔥 Auto logout on token expiry / invalid token
        if (response.status === 401 || response.status === 403) {
            console.warn("Auth failed. Logging out.");
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
            return;
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

/* ===============================
   AUTH API
================================ */
const AuthAPI = {
    requestOTP: (mobile_number, dcet_reg_number, college_name) =>
        apiRequest('/auth/request-otp', {
            method: 'POST',
            body: JSON.stringify({ mobile_number, dcet_reg_number, college_name })
        }),

    verifyOTP: (mobile_number, otp) =>
        apiRequest('/auth/verify-otp', {
            method: 'POST',
            body: JSON.stringify({ mobile_number, otp })
        }),

    adminLogin: (username, password) =>
        apiRequest('/auth/admin-login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        }),

    verifyToken: () =>
        apiRequest('/auth/verify-token', { method: 'GET' })
};

/* ===============================
   STUDENT API
================================ */
const StudentAPI = {
    getProfile: () =>
        apiRequest('/students/profile', { method: 'GET' }),

    updateProfile: (data) =>
        apiRequest('/students/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    getDailyStats: () =>
        apiRequest('/students/stats/daily', { method: 'GET' }),

    getStatsBySubject: () =>
        apiRequest('/students/stats/subjects', { method: 'GET' })
};

/* ===============================
   SUBJECT API
================================ */
const SubjectAPI = {
    getAll: () =>
        apiRequest('/subjects', { method: 'GET' }),

    getById: (id) =>
        apiRequest(`/subjects/${id}`, { method: 'GET' }),

    getUnits: (subjectId) =>
        apiRequest(`/subjects/${subjectId}/units`, { method: 'GET' })
};

/* ===============================
   QUIZ API
================================ */
const QuizAPI = {
    generate: (subject_id, unit_id, difficulty, mode) =>
        apiRequest('/quiz/generate', {
            method: 'POST',
            body: JSON.stringify({ subject_id, unit_id, difficulty, mode })
        }),

    submit: (attempt_id, answers, time_spent_seconds) =>
        apiRequest('/quiz/submit', {
            method: 'POST',
            body: JSON.stringify({ attempt_id, answers, time_spent_seconds })
        }),

    completeFlashcard: (session_id, cards_known, cards_unknown, time_spent_seconds) =>
        apiRequest('/quiz/flashcard/complete', {
            method: 'POST',
            body: JSON.stringify({
                session_id,
                cards_known,
                cards_unknown,
                time_spent_seconds
            })
        }),

    getHistory: () =>
        apiRequest('/quiz/history', { method: 'GET' })
};

/* ===============================
   ADMIN API
================================ */
const AdminAPI = {
    getAnalytics: () =>
        apiRequest('/admin/analytics', { method: 'GET' }),

    getSubjects: () =>
        apiRequest('/admin/subjects', { method: 'GET' }),

    createSubject: (data) =>
        apiRequest('/admin/subjects', {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    updateSubject: (id, data) =>
        apiRequest(`/admin/subjects/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    uploadDocument: async (formData) => {
        const token = localStorage.getItem('token');

        const response = await fetch(`${API_BASE}/admin/upload`, {
            method: 'POST',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            body: formData
        });

        return response.json();
    },

    getDocuments: () =>
        apiRequest('/admin/documents', { method: 'GET' }),

    deleteDocument: (id) =>
        apiRequest(`/admin/documents/${id}`, { method: 'DELETE' })
};

/* ===============================
   AUTH HELPERS
================================ */
function isLoggedIn() {
    return !!localStorage.getItem('token');
}

function getUser() {
    const user = localStorage.getItem('user');

    // ✅ Prevent JSON.parse crash
    if (!user || user === "undefined" || user === "null") {
        localStorage.removeItem('user');
        return null;
    }

    try {
        return JSON.parse(user);
    } catch (err) {
        console.error("Invalid user JSON in localStorage:", user);
        localStorage.removeItem('user');
        return null;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = '/';
        return false;
    }
    return true;
}

function requireAdmin() {
    const user = getUser();
    if (!user || user.role !== 'admin') {
        window.location.href = '/admin-login';
        return false;
    }
    return true;
}

/* ===============================
   PASSWORD RESET API
================================ */
const PasswordAPI = {
    forgot: (email) =>
        apiRequest('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        }),

    reset: (token, password) =>
        apiRequest(`/auth/reset-password/${token}`, {
            method: 'POST',
            body: JSON.stringify({ password })
        })
};
