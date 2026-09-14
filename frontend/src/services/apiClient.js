/**
 * Centralized API Client Service for SecureChain DMS
 * Supports JWT bearer token injection, automatic request formatting,
 * FormData upload handling, and unified error management.
 */

const BASE_URL = '/api/v1';
const TOKEN_KEY = 'securechain_access_token';
const USER_KEY = 'securechain_user';

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (_) {
    return null;
  }
};

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_) {
    return null;
  }
};

export const setStoredAuth = (accessToken, user) => {
  try {
    if (accessToken) {
      localStorage.setItem(TOKEN_KEY, accessToken);
    }
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  } catch (err) {
    console.error('Failed to save auth credentials to storage:', err);
  }
};

export const clearStoredAuth = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch (_) {}
};

/**
 * Base fetch wrapper for /api/v1 HTTP requests
 */
async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});

  // Automatically attach Bearer token if present
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Handle body & Content-Type header
  let body = options.body;
  if (
    body &&
    typeof body === 'object' &&
    !(body instanceof FormData) &&
    !(body instanceof Blob)
  ) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(body);
  }

  // Build full endpoint URL
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${BASE_URL}${cleanEndpoint}`;

  const config = {
    ...options,
    headers,
    body,
  };

  try {
    const response = await fetch(url, config);

    // Handle 401 Unauthorized (Session Expired / Invalid Token)
    if (response.status === 401) {
      clearStoredAuth();
      let errorDetail = 'Session expired or invalid credentials. Please log in again.';
      try {
        const errorData = await response.json();
        if (errorData.detail) errorDetail = errorData.detail;
        else if (errorData.error) errorDetail = errorData.error;
      } catch (_) {}
      const err = new Error(errorDetail);
      err.status = 401;
      throw err;
    }

    // Handle other non-2xx HTTP errors
    if (!response.ok) {
      let errorDetail = `Request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (typeof errorData.detail === 'string') {
          errorDetail = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
        } else if (errorData.error) {
          errorDetail = errorData.error;
        }
      } catch (_) {}
      const err = new Error(errorDetail);
      err.status = response.status;
      throw err;
    }

    // Handle Blob response if responseType is 'blob'
    if (options.responseType === 'blob') {
      const blob = await response.blob();
      const contentDisposition = response.headers.get('content-disposition');
      let filename = null;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=['"]?(?:UTF-8'')?([^"';]+)['"]?/i);
        if (match && match[1]) {
          filename = decodeURIComponent(match[1].trim());
        }
      }
      return { blob, filename, headers: response.headers };
    }

    // Parse JSON response if Content-Type is application/json
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    return response;
  } catch (err) {
    throw err;
  }
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  getBlob: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET', responseType: 'blob' }),
  post: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'POST', body }),
  postFormData: (endpoint, formData, options = {}) => request(endpoint, { ...options, method: 'POST', body: formData }),
  put: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PUT', body }),
  patch: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PATCH', body }),
  delete: (endpoint, options = {}) => request(endpoint, { ...options, method: 'DELETE' }),
};

export default apiClient;
