import NextAuth from "next-auth";
import authConfig from "./auth.config";

/**
 * NextAuth.js v5 Setup
 *
 * Backend-only architecture - all authentication handled by FastAPI.
 * NextAuth manages JWT sessions with tokens from backend.
 */
export const { handlers, signIn, signOut, auth } = NextAuth(authConfig);
