const API_BASE = '/api';

function getToken(): string | null {
  return localStorage.getItem('opencognit_token');
}

export async function request<T>(path: string, options?: RequestInit & { showToast?: boolean }): Promise<T> {
  const token = getToken();
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
      ...options,
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new ApiError(res.status, errorBody.error || `HTTP ${res.status}`, errorBody);
    }

    return res.json();
  } catch (error) {
    // Re-throw for components to handle
    throw error;
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: any,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
