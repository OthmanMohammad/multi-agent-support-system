"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Plus, Search, X, Menu } from "lucide-react";
import { useConversations, useCreateConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ConversationItem } from "./conversation-item";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ConversationItemSkeleton } from "./conversation-skeleton";

/**
 * Conversation Sidebar Component
 * Displays list of conversations with search and filtering
 */
export function ConversationSidebar(): JSX.Element {
  const [searchQuery, setSearchQuery] = useState("");
  const { data: conversations, isLoading } = useConversations();
  const createConversation = useCreateConversation();

  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const setCurrentConversation = useChatStore((state) => state.setCurrentConversation);
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);
  const toggleSidebar = useChatStore((state) => state.toggleSidebar);

  const handleNewConversation = async (): Promise<void> => {
    try {
      const newConversation = await createConversation.mutateAsync({
        title: "New Conversation",
      });
      setCurrentConversation(newConversation.conversation_id);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  const filteredConversations = conversations?.filter((conv) => {
    const title = conv.primary_intent || `Conversation ${conv.conversation_id.slice(0, 8)}`;
    return title.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <>
      {/* Mobile toggle button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={toggleSidebar}
      >
        {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-80 transform border-r border-border bg-background transition-transform duration-300 md:relative md:translate-x-0 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border p-4">
            <h2 className="text-lg font-semibold">Conversations</h2>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleNewConversation}
              disabled={createConversation.isPending}
            >
              <Plus className="h-5 w-5" />
            </Button>
          </div>

          {/* Search */}
          <div className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Conversation List */}
          <ScrollArea className="flex-1">
            {isLoading ? (
              <div className="space-y-2 p-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <ConversationItemSkeleton key={i} />
                ))}
              </div>
            ) : filteredConversations?.length === 0 ? (
              <div className="p-4 text-center text-sm text-foreground-secondary">
                {searchQuery ? "No conversations found" : "No conversations yet"}
              </div>
            ) : (
              <div className="space-y-1 p-2">
                {filteredConversations?.map((conversation) => (
                  <ConversationItem
                    key={conversation.conversation_id}
                    conversation={conversation}
                    isActive={currentConversationId === conversation.conversation_id}
                    onClick={() => setCurrentConversation(conversation.conversation_id)}
                  />
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </aside>
    </>
  );
}