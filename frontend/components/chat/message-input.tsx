"use client";

import type { JSX } from "react";
import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from "react";
import { Send, Paperclip, X, File, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSendMessage } from "@/lib/api/hooks/useMessages";
import { useCreateConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { cn } from "@/lib/utils";
import { toast, fileToast } from "@/lib/utils/toast";

interface MessageInputProps {
  conversationId: string | null;
}

interface Attachment {
  file: File;
  preview?: string;
  type: "image" | "file";
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_MESSAGE_LENGTH = 4000;
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "text/plain",
  "application/json",
  "text/csv",
];

/**
 * Message Input Component
 * Textarea with file upload, auto-resize, and keyboard shortcuts
 * Handles both creating new conversations and adding messages to existing ones
 */
export function MessageInput({ conversationId }: MessageInputProps): JSX.Element {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sendMessage = useSendMessage();
  const createConversation = useCreateConversation();
  const isStreaming = useChatStore((state) => state.isStreaming);
  const addMessage = useChatStore((state) => state.addMessage);
  const setCurrentConversation = useChatStore((state) => state.setCurrentConversation);
  const setIsStreaming = useChatStore((state) => state.setIsStreaming);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [message]);

  // Focus textarea on mount and when conversationId changes
  useEffect(() => {
    textareaRef.current?.focus();
  }, [conversationId]);

  const handleSend = async (): Promise<void> => {
    if (!message.trim() && attachments.length === 0) return;
    if (isStreaming || isSending) return;

    const content = message.trim();
    const messageAttachments = attachments;

    // Clear input immediately for better UX
    setMessage("");
    setAttachments([]);
    setIsSending(true);
    setIsStreaming(true);

    // Add optimistic user message to UI
    const optimisticUserMessage = {
      id: `temp-user-${Date.now()}`,
      conversationId: conversationId || "new",
      userId: "current-user",
      role: "USER" as const,
      content,
      metadata: messageAttachments.length > 0
        ? { attachments: messageAttachments.map((a) => a.file.name) }
        : null,
      createdAt: new Date(),
    };

    addMessage(optimisticUserMessage);

    try {
      if (!conversationId) {
        // Create a new conversation with the first message
        const response = await createConversation.mutateAsync({
          message: content,
        });

        // Set the new conversation as current
        setCurrentConversation(response.conversation_id);

        // Add AI response to UI
        const aiMessage = {
          id: `response-${Date.now()}`,
          conversationId: response.conversation_id,
          userId: "assistant",
          role: "ASSISTANT" as const,
          content: response.message,
          metadata: response.agent_name ? { agent: response.agent_name } : null,
          createdAt: new Date(),
        };
        addMessage(aiMessage);

        toast.success("Conversation started");
      } else {
        // Add message to existing conversation
        const response = await sendMessage.mutateAsync({
          conversationId,
          content,
        });

        // Add AI response to UI
        const aiMessage = {
          id: `response-${Date.now()}`,
          conversationId,
          userId: "assistant",
          role: "ASSISTANT" as const,
          content: response.message,
          metadata: response.agent_name ? { agent: response.agent_name } : null,
          createdAt: new Date(),
        };
        addMessage(aiMessage);
      }
    } catch (error) {
      console.error("Failed to send message:", error);

      // Show error toast
      const errorMessage = error instanceof Error ? error.message : "Please try again.";
      toast.error("Failed to send message", {
        description: errorMessage,
        action: {
          label: "Retry",
          onClick: () => {
            setMessage(content);
            setAttachments(messageAttachments);
          },
        },
      });
    } finally {
      setIsSending(false);
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    // Send on Cmd/Ctrl + Enter
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      void handleSend();
      return;
    }

    // Add newline on Shift + Enter (default behavior)
    if (e.shiftKey && e.key === "Enter") {
      return;
    }

    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const files = Array.from(e.target.files || []);
    processFiles(files);
  };

  const processFiles = (files: File[]): void => {
    const newAttachments: Attachment[] = [];

    files.forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        fileToast.sizeLimit("10MB");
        return;
      }

      const isImage = ALLOWED_IMAGE_TYPES.includes(file.type);
      const isAllowedFile = ALLOWED_FILE_TYPES.includes(file.type);

      if (!isImage && !isAllowedFile) {
        fileToast.typeError([...ALLOWED_IMAGE_TYPES, ...ALLOWED_FILE_TYPES]);
        return;
      }

      const attachment: Attachment = {
        file,
        type: isImage ? "image" : "file",
      };

      if (isImage) {
        const reader = new FileReader();
        reader.onload = (e) => {
          attachment.preview = e.target?.result as string;
          setAttachments((prev) => [...prev, attachment]);
        };
        reader.readAsDataURL(file);
      } else {
        newAttachments.push(attachment);
      }
    });

    if (newAttachments.length > 0) {
      setAttachments((prev) => [...prev, ...newAttachments]);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (index: number): void => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDragEnter = (e: React.DragEvent): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent): void => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    processFiles(Array.from(e.dataTransfer.files));
  };

  const characterCount = message.length;
  const isOverLimit = characterCount > MAX_MESSAGE_LENGTH;
  const canSend = (message.trim() || attachments.length > 0) && !isStreaming && !isSending && !isOverLimit;

  return (
    <div className="border-t border-border p-4">
      <div className="mx-auto max-w-3xl">
        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((attachment, index) => (
              <div
                key={index}
                className="group relative flex items-center gap-2 rounded-lg border border-border bg-surface p-2"
              >
                {attachment.type === "image" && attachment.preview ? (
                  <div className="relative h-12 w-12 overflow-hidden rounded">
                    <img
                      src={attachment.preview}
                      alt={attachment.file.name}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded bg-surface">
                    <File className="h-6 w-6 text-foreground-secondary" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium">{attachment.file.name}</p>
                  <p className="text-xs text-foreground-secondary">
                    {(attachment.file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-6 w-6"
                  onClick={() => removeAttachment(index)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div
          className={cn(
            "relative rounded-lg border border-border bg-background transition-colors",
            isDragging && "border-accent bg-accent/10",
            isOverLimit && "border-destructive"
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isSending
                ? "AI is thinking..."
                : conversationId
                ? "Type a message... (Enter to send)"
                : "Start a new conversation... (Enter to send)"
            }
            disabled={isSending || isStreaming}
            className={cn(
              "w-full resize-none rounded-lg bg-transparent px-4 py-3 pr-24 text-sm outline-none placeholder:text-foreground-secondary disabled:cursor-not-allowed disabled:opacity-50",
              "min-h-[52px] max-h-[200px]"
            )}
            rows={1}
          />

          {/* Action Buttons */}
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={[...ALLOWED_IMAGE_TYPES, ...ALLOWED_FILE_TYPES].join(",")}
              onChange={handleFileChange}
              className="hidden"
            />

            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8"
              onClick={() => fileInputRef.current?.click()}
              disabled={isSending || isStreaming}
              title="Attach file"
            >
              <Paperclip className="h-4 w-4" />
            </Button>

            <Button
              size="icon"
              className="h-8 w-8"
              onClick={handleSend}
              disabled={!canSend}
              title="Send message (Enter)"
            >
              {isSending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Drag Overlay */}
          {isDragging && (
            <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-accent/20 backdrop-blur-sm">
              <div className="flex flex-col items-center gap-2 text-accent-foreground">
                <Paperclip className="h-8 w-8" />
                <p className="text-sm font-medium">Drop files here</p>
              </div>
            </div>
          )}
        </div>

        {/* Character Counter */}
        <div className="mt-2 flex items-center justify-between px-1 text-xs text-foreground-secondary">
          <div className="flex items-center gap-4">
            <span>
              Press <kbd className="rounded border border-border px-1">Enter</kbd> to send,{" "}
              <kbd className="rounded border border-border px-1">Shift+Enter</kbd> for new line
            </span>
          </div>
          <span
            className={cn(
              characterCount > MAX_MESSAGE_LENGTH * 0.9 && "text-warning",
              isOverLimit && "font-medium text-destructive"
            )}
          >
            {characterCount} / {MAX_MESSAGE_LENGTH}
          </span>
        </div>
      </div>
    </div>
  );
}
