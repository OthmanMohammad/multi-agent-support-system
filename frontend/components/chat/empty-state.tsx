import type { JSX } from "react";
import { MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/lib/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";

/**
 * Empty State Component
 * Shown when no conversation is selected
 */
export function EmptyState(): JSX.Element {
  const { createConversation, isCreating } = useConversations();
  const setCurrentConversation = useChatStore(
    (state) => state.setCurrentConversation
  );

  const handleNewConversation = async (): Promise<void> => {
    try {
      const response = await createConversation("Hello, I need help");
      if (response) {
        setCurrentConversation(response.conversation_id);
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-surface">
        <MessageSquare className="h-10 w-10 text-foreground-secondary" />
      </div>
      <h2 className="mt-6 text-2xl font-semibold">Start a Conversation</h2>
      <p className="mt-2 max-w-md text-foreground-secondary">
        Select a conversation from the sidebar or create a new one to start
        chatting with our AI-powered support agents.
      </p>
      <Button
        onClick={handleNewConversation}
        disabled={isCreating}
        className="mt-6"
      >
        <MessageSquare className="mr-2 h-4 w-4" />
        New Conversation
      </Button>
    </div>
  );
}