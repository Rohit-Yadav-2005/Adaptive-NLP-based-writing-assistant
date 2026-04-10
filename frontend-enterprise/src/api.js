import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('enterprise_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  register: (data) => api.post('/api/v2/auth/register', data),
  login: (formData) => api.post('/api/v2/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
};

export const documentApi = {
  listWorkspaces: () => api.get('/api/v2/workspaces'),
  listFolders: (orgId) => api.get(`/api/v2/folders?org_id=${orgId}`),
  getActivity: (orgId) => api.get(`/api/v2/workspaces/activity?org_id=${orgId}`),
  inviteMember: (orgId, email) => api.post(`/api/v2/workspaces/${orgId}/invite`, { email }),
  listDocuments: (orgId) => api.get(`/api/v2/documents?org_id=${orgId}`),
  createFolder: (data) => api.post('/api/v2/folders', data),
  createDocument: (data) => api.post('/api/v2/documents', data),
  updateDocument: (id, data) => api.put(`/api/v2/documents/${id}`, data),
  getHistory: (id) => api.get(`/api/v2/documents/${id}/history`),
  analyze: (text, style) => api.post('/api/v2/analyze', { text, target_style: style }),
  
  // Vault
  uploadVaultFile: (orgId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v2/vault/upload?org_id=${orgId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  listVault: (orgId) => api.get(`/api/v2/vault?org_id=${orgId}`),
  
  // Analytics
  getAnalytics: (orgId) => api.get(`/api/v2/analytics?org_id=${orgId}`),
  
  // Comments
  listComments: (docId) => api.get(`/api/v2/documents/${docId}/comments`),
  addComment: (data) => api.post('/api/v2/comments', data),
};

export default api;
