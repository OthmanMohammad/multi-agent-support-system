import { useState, useEffect } from "react";

/**
 * OAuth Provider Availability State
 */
export interface OAuthProviders {
  google: boolean;
  github: boolean;
  isLoading: boolean;
  hasAnyOAuth: boolean;
}

/**
 * Custom hook to check which OAuth providers are available
 *
 * Fetches provider availability from the API on mount.
 * Returns loading state and provider flags.
 */
export function useOAuthProviders(): OAuthProviders {
  const [providers, setProviders] = useState<OAuthProviders>({
    google: false,
    github: false,
    isLoading: true,
    hasAnyOAuth: false,
  });

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await fetch("/api/auth/providers");
        if (response.ok) {
          const data = await response.json();
          setProviders({
            google: data.google ?? false,
            github: data.github ?? false,
            isLoading: false,
            hasAnyOAuth: (data.google ?? false) || (data.github ?? false),
          });
        } else {
          // API error - assume no OAuth available
          setProviders({
            google: false,
            github: false,
            isLoading: false,
            hasAnyOAuth: false,
          });
        }
      } catch (error) {
        console.error("Failed to fetch OAuth providers:", error);
        // Network error - assume no OAuth available
        setProviders({
          google: false,
          github: false,
          isLoading: false,
          hasAnyOAuth: false,
        });
      }
    };

    fetchProviders();
  }, []);

  return providers;
}
