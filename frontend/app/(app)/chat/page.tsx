'use client';

import { Send, Plus, MoreHorizontal } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

import { Button, Input, Avatar, AvatarFallback, Card, ScrollArea, Skeleton } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentName?: string;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

// Mock data
const mockConversations: Conversation[] = [
  {
    id: '1',
    title: 'Billing question',
    lastMessage: 'I can help you with that invoice...',
    timestamp: new Date(),
  },
  {
    id: '2',
    title: 'Technical support',
    lastMessage: 'Have you tried restarting the service?',
    timestamp: new Date(Date.now() - 3600000),
  },
  {
    id: '3',
    title: 'Feature request',
    lastMessage: "Thanks for the suggestion! I'll forward...",
    timestamp: new Date(Date.now() - 86400000),
  },
];

export default function ChatPage() {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm your AI support assistant. How can I help you today? I can assist with billing, technical issues, account management, and more.",
      timestamp: new Date(),
      agentName: 'Support Agent',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<string>('1');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          "Thank you for your message! I'm processing your request. Our team of specialized AI agents is working on finding the best solution for you. Is there anything specific you'd like me to focus on?",
        timestamp: new Date(),
        agentName: 'Support Agent',
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const userInitials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <div className="flex h-full gap-6">
      {/* Conversations List */}
      <Card className="w-80 flex flex-col shrink-0">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="font-semibold text-text-primary">Conversations</h2>
          <Button variant="ghost" size="icon-sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2">
            {mockConversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedConversation(conv.id)}
                className={cn(
                  'w-full text-left p-3 rounded-lg transition-colors',
                  selectedConversation === conv.id
                    ? 'bg-brand-orange/10'
                    : 'hover:bg-background-secondary'
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm text-text-primary truncate">
                    {conv.title}
                  </span>
                  <span className="text-xs text-text-tertiary">
                    {conv.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="text-xs text-text-secondary truncate">{conv.lastMessage}</p>
              </button>
            ))}
          </div>
        </ScrollArea>
      </Card>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-text-primary">Support Chat</h2>
            <p className="text-sm text-text-secondary">AI-powered assistance</p>
          </div>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-5 w-5" />
          </Button>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3',
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback
                    className={cn(
                      message.role === 'user'
                        ? 'bg-brand-orange text-white'
                        : 'bg-background-secondary text-text-secondary'
                    )}
                  >
                    {message.role === 'user' ? userInitials : 'AI'}
                  </AvatarFallback>
                </Avatar>
                <div
                  className={cn(
                    'rounded-lg px-4 py-2 max-w-[70%]',
                    message.role === 'user'
                      ? 'bg-brand-orange text-white'
                      : 'bg-background-secondary text-text-primary'
                  )}
                >
                  {message.agentName && (
                    <p className="text-xs font-medium mb-1 opacity-70">{message.agentName}</p>
                  )}
                  <div className="prose prose-sm">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback className="bg-background-secondary text-text-secondary">
                    AI
                  </AvatarFallback>
                </Avatar>
                <div className="bg-background-secondary rounded-lg px-4 py-3 space-y-2">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <Input
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={!input.trim() || isLoading}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
