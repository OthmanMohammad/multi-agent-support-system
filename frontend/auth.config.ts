/**
 * NextAuth.js v5 Configuration
 *
 * Enterprise authentication with Backend API integration.
 * Supports:
 * - Credentials (email/password) via FastAPI backend
 * - Google OAuth via FastAPI backend
 * - GitHub OAuth via FastAPI backend
 */

import type { NextAuthConfig } from "next-auth";
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

/**
 * Call backend login endpoint
 */
async function loginWithBackend(email: string, password: string) {
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
 * Handle OAuth callback from backend
 */
async function handleOAuthCallback(
  provider: string,
  code: string,
  state: string
) {
  try {
    const response = await fetch(
      `${API_URL}/api/oauth/${provider}/callback?code=${code}&state=${state}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
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
    };
  } catch (error) {
    console.error(`${provider} OAuth error:`, error);
    return null;
  }
}

export default {
  providers: [
    // ==========================================================================
    // GOOGLE OAUTH
    // ==========================================================================
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),

    // ==========================================================================
    // GITHUB OAUTH
    // ==========================================================================
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID ?? "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
    }),

    // ==========================================================================
    // CREDENTIALS (Email/Password)
    // ==========================================================================
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // Validate input
        const validatedFields = loginSchema.safeParse(credentials);

        if (!validatedFields.success) {
          return null;
        }

        const { email, password } = validatedFields.data;

        // Call backend API
        const user = await loginWithBackend(email, password);

        if (!user) {
          return null;
        }

        // Store tokens in localStorage (client-side)
        // Note: This runs on server, so we'll pass tokens via session
        return user;
      },
    }),
  ],

  // ===========================================================================
  // CALLBACKS
  // ===========================================================================
  callbacks: {
    /**
     * JWT Callback - Runs when JWT is created or updated
     * Add backend tokens to JWT
     */
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

      // OAuth sign in
      if (
        account &&
        (account.provider === "google" || account.provider === "github")
      ) {
        // Exchange OAuth code for backend tokens
        const backendUser = await handleOAuthCallback(
          account.provider,
          account.access_token || "",
          "" // State will be validated by backend
        );

        if (backendUser) {
          token.id = backendUser.id;
          token.email = backendUser.email;
          token.name = backendUser.name;
          token.role = backendUser.role;
          token.accessToken = backendUser.accessToken;
          token.refreshToken = backendUser.refreshToken;
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
