import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import type { Message } from "@prisma/client";

/**
 * Zustand store for chat state management
 * High-performance, type-safe state management with persistence
 */

interface ChatState {
  // Current conversation
  currentConversationId: string | null;
  setCurrentConversation: (id: string | null) => void;

  // Messages
  messages: Message[];
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;

  // Streaming state
  isStreaming: boolean;
  streamingMessage: string;
  setIsStreaming: (isStreaming: boolean) => void;
  appendToStreamingMessage: (chunk: string) => void;
  clearStreamingMessage: () => void;

  // UI state
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (isOpen: boolean) => void;

  // Input state
  inputValue: string;
  setInputValue: (value: string) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        // Current conversation
        currentConversationId: null,
        setCurrentConversation: (id) => set({ currentConversationId: id }),

        // Messages
        messages: [],
        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
          })),
        setMessages: (messages) => set({ messages }),
        clearMessages: () => set({ messages: [] }),

        // Streaming state
        isStreaming: false,
        streamingMessage: "",
        setIsStreaming: (isStreaming) => set({ isStreaming }),
        appendToStreamingMessage: (chunk) =>
          set((state) => ({
            streamingMessage: state.streamingMessage + chunk,
          })),
        clearStreamingMessage: () => set({ streamingMessage: "" }),

        // UI state
        isSidebarOpen: true,
        toggleSidebar: () =>
          set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
        setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

        // Input state
        inputValue: "",
        setInputValue: (value) => set({ inputValue: value }),
      }),
      {
        name: "chat-storage",
        partialize: (state) => ({
          isSidebarOpen: state.isSidebarOpen,
          currentConversationId: state.currentConversationId,
        }),
      }
    ),
    {
      name: "ChatStore",
      enabled: process.env.NODE_ENV === "development",
    }
  )
);
