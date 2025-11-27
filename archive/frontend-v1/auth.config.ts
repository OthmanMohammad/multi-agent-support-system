/**
 * NextAuth.js v5 Configuration
 *
 * Clean architecture: NextAuth handles ONLY OAuth (Google/GitHub).
 * Email/password authentication is handled directly by auth-context.tsx
 * via the FastAPI backend, without involving NextAuth.
 *
 * This separation provides:
 * - Clear responsibility: NextAuth = OAuth, Backend API = credentials
 * - No double API calls
 * - Simpler debugging
 * - Industry standard pattern for custom backends
 */

import type { NextAuthConfig } from "next-auth";
import type { Provider } from "next-auth/providers";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";

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
=======
>>>>>>> 5663ce9 (refactor: clean auth architecture - NextAuth for OAuth only)
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
        full_name: name || email.split("@")[0],
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

// Build providers array - OAuth only, no Credentials
const buildProviders = (): Provider[] => {
  const providers: Provider[] = [];

  // Google OAuth (only if configured)
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

  // GitHub OAuth (only if configured)
  if (isGitHubConfigured) {
    providers.push(
      GitHub({
        clientId: GITHUB_CLIENT_ID as string,
        clientSecret: GITHUB_CLIENT_SECRET as string,
      })
    );
  }
  return providers;
};

export default {
  providers: buildProviders(),

  callbacks: {
    /**
     * JWT Callback - Add backend tokens to JWT for OAuth users
     */
    async jwt({ token, user, account }) {
      // OAuth sign in - call backend to create/login user
      if (
        account &&
        (account.provider === "google" || account.provider === "github") &&
        user
      ) {
        const email = user.email || (token.email as string);
        const name = user.name || (token.name as string);
        const providerAccountId = account.providerAccountId;

        if (email && providerAccountId) {
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
     * Session Callback - Expose data to client
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

        session.accessToken = token.accessToken as string;
        session.refreshToken = token.refreshToken as string;
        session.isNewUser = (token.isNewUser as boolean | undefined) ?? false;
      }

      return session;
    },

    /**
     * Redirect Callback - Control post-auth redirect
     */
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) {
        return `${baseUrl}${url}`;
      }
      if (new URL(url).origin === baseUrl) {
        return url;
      }
      return baseUrl;
    },
  },

  pages: {
    signIn: "/auth/signin",
    signOut: "/auth/signout",
    error: "/auth/error",
    newUser: "/dashboard",
  },

  events: {
    async signOut(params) {
      const token = "token" in params ? params.token : null;

      // Call backend logout for OAuth users
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

  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  debug: process.env.NODE_ENV === "development",
} satisfies NextAuthConfig;
