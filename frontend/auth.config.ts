/**
 * NextAuth.js v5 Configuration
 *
 * Enterprise authentication with Backend API integration.
 * Supports:
 * - Credentials (email/password) via FastAPI backend
 * - Google OAuth via FastAPI backend (when configured)
 * - GitHub OAuth via FastAPI backend (when configured)
 */

import type { NextAuthConfig } from "next-auth";
import type { Provider } from "next-auth/providers";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// OAuth Provider Configuration Detection
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;

// Check if OAuth providers are properly configured
export const isGoogleConfigured = !!(GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET);
export const isGitHubConfigured = !!(GITHUB_CLIENT_ID && GITHUB_CLIENT_SECRET);

/**
 * Call backend login endpoint
 *
 * This is used by NextAuth's Credentials provider for direct form submissions.
 * Note: When called from auth-context.tsx, the login API has already been called
 * and tokens are stored. This second call is redundant but harmless.
 *
 * If accessToken is provided (from auth-context), we skip the API call
 * and just return the user info to create a NextAuth session.
 */
async function loginWithBackend(
  email: string,
  password: string,
  existingAccessToken?: string,
  existingRefreshToken?: string
) {
  // If tokens are already provided, skip the API call
  // This happens when auth-context.tsx calls signIn() after a successful login
  if (existingAccessToken) {
    // Return minimal user object - the actual user data is already
    // managed by auth-context via localStorage tokens
    return {
      id: "session-user",
      email,
      name: "",
      role: "user",
      accessToken: existingAccessToken,
      refreshToken: existingRefreshToken || "",
    };
  }

  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    // Store JWT tokens in user object (will be saved in session)
    return {
      id: data.user.id,
      email: data.user.email,
      name: data.user.full_name,
      role: data.user.role,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    };
  } catch (error) {
    console.error("Backend login error:", error);
    return null;
  }
}

/**
 * Login or register user via OAuth provider
 * Calls the backend /api/auth/oauth-login endpoint
 */
async function loginWithOAuth(
  email: string,
  name: string,
  provider: string,
  providerAccountId: string
) {
  try {
    const response = await fetch(`${API_URL}/api/auth/oauth-login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        full_name: name || email.split("@")[0], // Fallback to email prefix if no name
        provider,
        provider_user_id: providerAccountId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("OAuth login failed:", response.status, errorData);
      return null;
    }

    const data = await response.json();

    return {
      id: data.user.id,
      email: data.user.email,
      name: data.user.full_name,
      role: data.user.role,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isNewUser: data.is_new_user ?? false,
    };
  } catch (error) {
    console.error(`${provider} OAuth error:`, error);
    return null;
  }
}

// Build providers array dynamically based on configuration
const buildProviders = (): Provider[] => {
  const providers: Provider[] = [];

  // ==========================================================================
  // GOOGLE OAUTH (only if configured)
  // ==========================================================================
  if (isGoogleConfigured) {
    providers.push(
      Google({
        clientId: GOOGLE_CLIENT_ID as string,
        clientSecret: GOOGLE_CLIENT_SECRET as string,
        authorization: {
          params: {
            prompt: "consent",
            access_type: "offline",
            response_type: "code",
          },
        },
      })
    );
  }

  // ==========================================================================
  // GITHUB OAUTH (only if configured)
  // ==========================================================================
  if (isGitHubConfigured) {
    providers.push(
      GitHub({
        clientId: GITHUB_CLIENT_ID as string,
        clientSecret: GITHUB_CLIENT_SECRET as string,
      })
    );
  }

  // ==========================================================================
  // CREDENTIALS (Email/Password) - Always available
  // ==========================================================================
  providers.push(
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        // Optional tokens - when provided, skip backend API call
        // This is used when auth-context has already authenticated
        accessToken: { label: "Access Token", type: "text" },
        refreshToken: { label: "Refresh Token", type: "text" },
      },
      async authorize(credentials) {
        // Check if we have pre-authenticated tokens (from auth-context)
        const existingAccessToken = credentials?.accessToken as
          | string
          | undefined;
        const existingRefreshToken = credentials?.refreshToken as
          | string
          | undefined;

        // Validate input
        const validatedFields = loginSchema.safeParse(credentials);

        if (!validatedFields.success) {
          return null;
        }

        const { email, password } = validatedFields.data;

        // Call backend API (or skip if tokens already exist)
        const user = await loginWithBackend(
          email,
          password,
          existingAccessToken,
          existingRefreshToken
        );

        if (!user) {
          return null;
        }

        // Return user object - tokens will be saved in JWT callback
        return user;
      },
    })
  );

  return providers;
};

export default {
  providers: buildProviders(),

  // ===========================================================================
  // CALLBACKS
  // ===========================================================================
  callbacks: {
    /**
     * JWT Callback - Runs when JWT is created or updated
     * Add backend tokens to JWT
     */
    // eslint-disable-next-line complexity -- Complex auth flow handling multiple providers
    async jwt({ token, user, account }) {
      // Initial sign in
      if (user) {
        token.id = user.id;
        token.email = user.email ?? "";
        token.name = user.name ?? "";
        token.role = (user as { role?: string }).role ?? "USER";
        token.accessToken =
          (user as { accessToken?: string }).accessToken ?? "";
        token.refreshToken =
          (user as { refreshToken?: string }).refreshToken ?? "";
      }

      // OAuth sign in - get user info and call backend to create/login user
      if (
        account &&
        (account.provider === "google" || account.provider === "github") &&
        user
      ) {
        // Extract user info from OAuth profile
        const email = user.email || (token.email as string);
        const name = user.name || (token.name as string);
        const providerAccountId = account.providerAccountId;

        if (email && providerAccountId) {
          // Call backend to create/login OAuth user
          const backendUser = await loginWithOAuth(
            email,
            name,
            account.provider,
            providerAccountId
          );

          if (backendUser) {
            token.id = backendUser.id;
            token.email = backendUser.email;
            token.name = backendUser.name;
            token.role = backendUser.role;
            token.accessToken = backendUser.accessToken;
            token.refreshToken = backendUser.refreshToken;
            token.isNewUser = backendUser.isNewUser;
          } else {
            console.error("Failed to create/login OAuth user in backend");
          }
        }
      }

      return token;
    },

    /**
     * Session Callback - Runs when session is checked
     * Expose necessary data to client
     */
    async session({ session, token }) {
      if (token) {
        session.user = {
          ...session.user,
          id: token.id as string,
          email: token.email as string,
          name: token.name as string,
          role: token.role as string,
        };

        // Add tokens to session (available client-side)
        session.accessToken = token.accessToken as string;
        session.refreshToken = token.refreshToken as string;
        session.isNewUser = (token.isNewUser as boolean | undefined) ?? false;
      }

      return session;
    },

    /**
     * Redirect Callback - Control where to redirect after auth
     */
    async redirect({ url, baseUrl }) {
      // Allows relative callback URLs
      if (url.startsWith("/")) {
        return `${baseUrl}${url}`;
      }

      // Allows callback URLs on the same origin
      if (new URL(url).origin === baseUrl) {
        return url;
      }

      return baseUrl;
    },
  },

  // ===========================================================================
  // PAGES
  // ===========================================================================
  pages: {
    signIn: "/auth/signin",
    signOut: "/auth/signout",
    error: "/auth/error",
    verifyRequest: "/auth/verify",
    newUser: "/dashboard", // Redirect new users to dashboard
  },

  // ===========================================================================
  // EVENTS
  // ===========================================================================
  events: {
    async signIn({ user, account }) {
      console.log("User signed in:", {
        userId: user.id,
        provider: account?.provider,
      });
    },
    async signOut(params) {
      const token = "token" in params ? params.token : null;
      console.log("User signed out:", { userId: token?.id });

      // Call backend logout
      try {
        if (token?.accessToken) {
          await fetch(`${API_URL}/api/auth/logout`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token.accessToken}`,
            },
          });
        }
      } catch (error) {
        console.error("Backend logout error:", error);
      }
    },
  },

  // ===========================================================================
  // SESSION
  // ===========================================================================
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  // ===========================================================================
  // DEBUG
  // ===========================================================================
  debug: process.env.NODE_ENV === "development",
} satisfies NextAuthConfig;
