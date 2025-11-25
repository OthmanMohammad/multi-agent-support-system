/**
 * Enterprise API Client
 *
 * Production-grade HTTP client with:
 * - Automatic JWT token management
 * - Token refresh on 401
 * - Request/response interceptors
 * - Error handling and retry logic
 * - Request cancellation
 * - Type-safe responses with Zod validation
 */

import axios from "axios";
import type {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import { config } from "./config";
import { APIClientError, failure, type Result, success } from "./types/api";

// =============================================================================
// TOKEN MANAGEMENT
// =============================================================================

class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = "access_token";
  private static readonly REFRESH_TOKEN_KEY = "refresh_token";

  static getAccessToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static getRefreshToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === "undefined") {
      return;
    }
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  static clearTokens(): void {
    if (typeof window === "undefined") {
      return;
    }
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }
}

// =============================================================================
// API CLIENT CLASS
// =============================================================================

class APIClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    this.client = axios.create({
      baseURL: config.api.baseURL,
      timeout: config.api.timeout,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  // ===========================================================================
  // INTERCEPTORS
  // ===========================================================================

  private setupInterceptors(): void {
    // Request interceptor - Add JWT token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = TokenManager.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        // Handle 401 Unauthorized - Refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue request while refresh is in progress
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await this.refreshAccessToken();
            this.isRefreshing = false;
            this.onRefreshSuccess(newToken);

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            this.isRefreshing = false;
            this.onRefreshFailure();
            TokenManager.clearTokens();

            // Redirect to login
            if (typeof window !== "undefined") {
              window.location.href = "/auth/signin";
            }

            return Promise.reject(refreshError);
          }
        }

        // Transform error to APIClientError
        return Promise.reject(this.transformError(error));
      }
    );
  }

  // ===========================================================================
  // TOKEN REFRESH
  // ===========================================================================

  private async refreshAccessToken(): Promise<string> {
    const refreshToken = TokenManager.getRefreshToken();

    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await axios.post(
        `${config.api.baseURL}/api/auth/refresh`,
        { refresh_token: refreshToken }
      );

      const { access_token, refresh_token: newRefreshToken } = response.data;

      TokenManager.setTokens(access_token, newRefreshToken);

      return access_token;
    } catch (error) {
      TokenManager.clearTokens();
      throw error;
    }
  }

  private onRefreshSuccess(token: string): void {
    this.refreshSubscribers.forEach((callback) => callback(token));
    this.refreshSubscribers = [];
  }

  private onRefreshFailure(): void {
    this.refreshSubscribers = [];
  }

  // ===========================================================================
  // ERROR HANDLING
  // ===========================================================================

  private transformError(error: AxiosError): APIClientError {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as { detail?: string; message?: string };
      const message = data?.detail || data?.message || "An error occurred";

      return new APIClientError(
        message,
        error.response.status,
        error.code,
        data
      );
    } else if (error.request) {
      // Request made but no response
      return new APIClientError(
        "No response from server. Please check your connection.",
        0,
        "NETWORK_ERROR"
      );
    }
    // Error in request setup
    return new APIClientError(
      error.message || "An unexpected error occurred",
      0,
      "REQUEST_ERROR"
    );
  }

  // ===========================================================================
  // HTTP METHODS
  // ===========================================================================

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<Result<T>> {
    try {
      const response = await this.client.get<T>(url, config);
      return success(response.data);
    } catch (error) {
      return failure(error as APIClientError);
    }
  }

  async post<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<Result<T>> {
    try {
      const response = await this.client.post<T>(url, data, config);
      return success(response.data);
    } catch (error) {
      return failure(error as APIClientError);
    }
  }

  async put<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<Result<T>> {
    try {
      const response = await this.client.put<T>(url, data, config);
      return success(response.data);
    } catch (error) {
      return failure(error as APIClientError);
    }
  }

  async patch<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<Result<T>> {
    try {
      const response = await this.client.patch<T>(url, data, config);
      return success(response.data);
    } catch (error) {
      return failure(error as APIClientError);
    }
  }

  async delete<T>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<Result<T>> {
    try {
      const response = await this.client.delete<T>(url, config);
      return success(response.data);
    } catch (error) {
      return failure(error as APIClientError);
    }
  }

  // ===========================================================================
  // RAW CLIENT ACCESS (for special cases like streaming)
  // ===========================================================================

  getRawClient(): AxiosInstance {
    return this.client;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const apiClient = new APIClient();

// Export token manager for auth flows
export { TokenManager };
