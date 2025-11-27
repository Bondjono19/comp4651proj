const AUTH_URL = import.meta.env.VITE_AUTH_URL || '';

export interface AuthResponse {
  access_token: string;
  username: string;
  message?: string;
}

export interface ErrorResponse {
  error: string;
  details?: string;
}

class AuthService {
  private token: string | null = null;
  private username: string | null = null;

  constructor() {
    // Load from localStorage on init
    this.token = localStorage.getItem('auth_token');
    this.username = localStorage.getItem('username');
  }

  async register(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${AUTH_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Registration failed');
    }

    this.token = data.access_token;
    this.username = data.username;
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('username', data.username);

    return data;
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${AUTH_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }

    this.token = data.access_token;
    this.username = data.username;
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('username', data.username);

    return data;
  }

  async verify(): Promise<boolean> {
    if (!this.token) return false;

    try {
      const response = await fetch(`${AUTH_URL}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: this.token }),
      });

      if (!response.ok) {
        this.logout();
        return false;
      }

      const data = await response.json();
      this.username = data.username;
      return data.valid;
    } catch (error) {
      console.error('Token verification failed:', error);
      this.logout();
      return false;
    }
  }

  logout() {
    this.token = null;
    this.username = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('username');
  }

  getToken(): string | null {
    return this.token;
  }

  getUsername(): string | null {
    return this.username;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }
}

export default new AuthService();
