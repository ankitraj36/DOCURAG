/**
 * DocuRAG - API Service
 * Centralized API client for all backend communication.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min for processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('docurag_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Something went wrong';
    console.error('API Error:', message);
    return Promise.reject({ message, status: error.response?.status });
  }
);

// ─── Documents ────────────────────────────────────────────────────────────────

export const uploadDocument = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
  });
};

export const getDocuments = (params = {}) =>
  api.get('/documents', { params });

export const getDocument = (id) =>
  api.get(`/documents/${id}`);

export const deleteDocument = (id) =>
  api.delete(`/documents/${id}`);

export const reprocessDocument = (id) =>
  api.post(`/documents/${id}/process`);

export const summarizeDocument = (data) =>
  api.post('/documents/summarize', data);

export const compareDocuments = (data) =>
  api.post('/documents/compare', data);

export const explainPage = (data) =>
  api.post('/documents/explain-page', data);

// ─── Search ───────────────────────────────────────────────────────────────────

export const searchDocuments = (data) =>
  api.post('/search', data);

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const sendChatMessage = (data) =>
  api.post('/chat', data);

export const getConversations = () =>
  api.get('/chat/conversations');

export const getConversationMessages = (id) =>
  api.get(`/chat/conversations/${id}`);

export const deleteConversation = (id) =>
  api.delete(`/chat/conversations/${id}`);

// ─── Image Analysis ──────────────────────────────────────────────────────────

export const analyzeImage = (file, query) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('query', query || 'Describe this image in detail.');
  return api.post('/image/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// ─── Evaluation & Analytics ──────────────────────────────────────────────────

export const getEvaluation = () =>
  api.get('/evaluation');

export const getAnalytics = () =>
  api.get('/analytics');

export const getHealth = () =>
  api.get('/health');

export default api;
