/**
 * Conversation Hooks (API Layer)
 *
 * Re-exports conversation hooks from the hooks directory.
 */

import { useConversations as useConversationsHook, useConversation } from '@/lib/hooks/useConversations';

// Re-export from main hooks
export { useConversation };
export { useConversationsHook as useConversations };

// Alias for createConversation action within useConversations
export function useCreateConversation() {
  const { createConversation, isCreating } = useConversationsHook();
  return {
    createConversation,
    isCreating,
    isPending: isCreating,
  };
}
