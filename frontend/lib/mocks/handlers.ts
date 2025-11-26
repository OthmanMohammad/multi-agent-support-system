import { delay, http, HttpResponse } from "msw";
import type { components } from "@/types/api";

/**
 * MSW Request Handlers
 * Mock API responses for development and testing
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Type definitions
type Conversation = components["schemas"]["Conversation"];
type Message = components["schemas"]["Message"];
type Customer = components["schemas"]["Customer"];
type Agent = components["schemas"]["Agent"];

// Mock data
const mockConversations: Conversation[] = [
  {
    id: "conv-1",
    userId: "user-1",
    title: "How to implement authentication",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 3600000).toISOString(),
    metadata: null,
  },
  {
    id: "conv-2",
    userId: "user-1",
    title: "Database performance optimization",
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    updatedAt: new Date(Date.now() - 7200000).toISOString(),
    metadata: null,
  },
];

const mockMessages: Message[] = [
  {
    id: "msg-1",
    conversationId: "conv-1",
    userId: "user-1",
    role: "USER",
    content: "How do I implement authentication in Next.js?",
    metadata: null,
    createdAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "msg-2",
    conversationId: "conv-1",
    userId: "assistant",
    role: "ASSISTANT",
    content:
      "To implement authentication in Next.js, you can use NextAuth.js. Here's a step-by-step guide:\n\n1. Install NextAuth.js\n```bash\npnpm add next-auth\n```\n\n2. Create an auth configuration file...",
    metadata: null,
    createdAt: new Date(Date.now() - 3500000).toISOString(),
  },
];

const mockCustomers: Customer[] = [
  {
    id: "customer-1",
    name: "John Doe",
    email: "john@example.com",
    company: "Acme Corp",
    phone: "+1234567890",
    createdAt: new Date(Date.now() - 2592000000).toISOString(),
    lastInteraction: new Date(Date.now() - 86400000).toISOString(),
    totalInteractions: 15,
    metadata: null,
  },
  {
    id: "customer-2",
    name: "Jane Smith",
    email: "jane@example.com",
    company: "Tech Solutions Inc",
    phone: "+1987654321",
    createdAt: new Date(Date.now() - 5184000000).toISOString(),
    lastInteraction: new Date(Date.now() - 172800000).toISOString(),
    totalInteractions: 23,
    metadata: null,
  },
];

const mockAgents: Agent[] = [
  {
    id: "agent-1",
    name: "General Support Agent",
    description: "Handles general customer inquiries",
    model: "gpt-4-turbo-preview",
    provider: "openai",
    systemPrompt: "You are a helpful customer support assistant.",
    temperature: 0.7,
    maxTokens: 2048,
    isActive: true,
    createdAt: new Date(Date.now() - 7776000000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "agent-2",
    name: "Technical Support Agent",
    description: "Handles technical questions and troubleshooting",
    model: "claude-3-5-sonnet-20241022",
    provider: "anthropic",
    systemPrompt: "You are a technical support specialist.",
    temperature: 0.5,
    maxTokens: 4096,
    isActive: true,
    createdAt: new Date(Date.now() - 6048000000).toISOString(),
    updatedAt: new Date(Date.now() - 172800000).toISOString(),
  },
];

export const handlers = [
  // ========================================
  // Conversations
  // ========================================
  http.get(`${API_BASE_URL}/api/conversations`, async () => {
    await delay(300); // Simulate network delay
    return HttpResponse.json({
      conversations: mockConversations,
      total: mockConversations.length,
    });
  }),

  http.get(`${API_BASE_URL}/api/conversations/:id`, async ({ params }) => {
    await delay(200);
    const conversation = mockConversations.find((c) => c.id === params.id);
    if (!conversation) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(conversation);
  }),

  http.post(`${API_BASE_URL}/api/conversations`, async ({ request }) => {
    await delay(400);
    const body = await request.json();
    const newConversation: Conversation = {
      id: `conv-${Date.now()}`,
      userId: "user-1",
      title: (body as { title?: string }).title || "New Conversation",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      metadata: null,
    };
    mockConversations.unshift(newConversation);
    return HttpResponse.json(newConversation, { status: 201 });
  }),

  http.patch(
    `${API_BASE_URL}/api/conversations/:id`,
    async ({ params, request }) => {
      await delay(300);
      const body = await request.json();
      const conversation = mockConversations.find((c) => c.id === params.id);
      if (!conversation) {
        return new HttpResponse(null, { status: 404 });
      }
      Object.assign(conversation, body, {
        updatedAt: new Date().toISOString(),
      });
      return HttpResponse.json(conversation);
    }
  ),

  http.delete(`${API_BASE_URL}/api/conversations/:id`, async ({ params }) => {
    await delay(200);
    const index = mockConversations.findIndex((c) => c.id === params.id);
    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }
    mockConversations.splice(index, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  // ========================================
  // Messages
  // ========================================
  http.get(
    `${API_BASE_URL}/api/conversations/:conversationId/messages`,
    async ({ params }) => {
      await delay(200);
      const messages = mockMessages.filter(
        (m) => m.conversationId === params.conversationId
      );
      return HttpResponse.json({
        messages,
        hasMore: false,
        nextCursor: null,
      });
    }
  ),

  http.post(
    `${API_BASE_URL}/api/conversations/:conversationId/messages`,
    async ({ params, request }) => {
      await delay(500);
      const body = await request.json();
      const newMessage: Message = {
        id: `msg-${Date.now()}`,
        conversationId: params.conversationId as string,
        userId: "user-1",
        role: (body as { role: Message["role"] }).role,
        content: (body as { content: string }).content,
        metadata: null,
        createdAt: new Date().toISOString(),
      };
      mockMessages.push(newMessage);
      return HttpResponse.json(newMessage, { status: 201 });
    }
  ),

  // ========================================
  // Analytics
  // ========================================
  http.get(`${API_BASE_URL}/api/analytics/overview`, async () => {
    await delay(300);
    return HttpResponse.json({
      totalConversations: 247,
      totalMessages: 1893,
      totalCustomers: 89,
      avgResponseTime: 2.3,
      satisfactionScore: 4.6,
      activeAgents: 4,
      period: "7d",
    });
  }),

  http.get(`${API_BASE_URL}/api/analytics/conversations`, async () => {
    await delay(300);
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return {
        date: date.toISOString().split("T")[0],
        count: Math.floor(Math.random() * 50) + 20,
      };
    });

    return HttpResponse.json({
      period: "7d",
      conversationsByDay: last7Days,
      messagesByDay: last7Days.map((d) => ({
        ...d,
        count: d.count * 7,
      })),
      avgMessagesPerConversation: 7.6,
      avgConversationDuration: 342,
    });
  }),

  http.get(`${API_BASE_URL}/api/analytics/agents`, async () => {
    await delay(300);
    return HttpResponse.json({
      period: "7d",
      agents: [
        {
          agentId: "agent-1",
          agentName: "General Support Agent",
          totalConversations: 132,
          totalMessages: 1024,
          avgResponseTime: 2.1,
          satisfactionScore: 4.7,
          costUsd: 12.34,
        },
        {
          agentId: "agent-2",
          agentName: "Technical Support Agent",
          totalConversations: 115,
          totalMessages: 869,
          avgResponseTime: 2.5,
          satisfactionScore: 4.5,
          costUsd: 18.92,
        },
      ],
    });
  }),

  // ========================================
  // Customers
  // ========================================
  http.get(`${API_BASE_URL}/api/customers`, async () => {
    await delay(200);
    return HttpResponse.json({
      customers: mockCustomers,
      total: mockCustomers.length,
    });
  }),

  http.get(`${API_BASE_URL}/api/customers/:id`, async ({ params }) => {
    await delay(200);
    const customer = mockCustomers.find((c) => c.id === params.id);
    if (!customer) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(customer);
  }),

  http.get(
    `${API_BASE_URL}/api/customers/:id/interactions`,
    async ({ params }) => {
      await delay(300);
      return HttpResponse.json({
        customerId: params.id,
        conversations: mockConversations,
        totalInteractions: 15,
        avgResponseTime: 2.3,
        satisfactionScore: 4.6,
      });
    }
  ),

  // ========================================
  // Agents
  // ========================================
  http.get(`${API_BASE_URL}/api/agents`, async () => {
    await delay(200);
    return HttpResponse.json({
      agents: mockAgents,
    });
  }),

  http.get(`${API_BASE_URL}/api/agents/:id`, async ({ params }) => {
    await delay(200);
    const agent = mockAgents.find((a) => a.id === params.id);
    if (!agent) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(agent);
  }),

  http.post(`${API_BASE_URL}/api/agents`, async ({ request }) => {
    await delay(400);
    const body = await request.json();
    const newAgent: Agent = {
      ...(body as Omit<Agent, "id" | "createdAt" | "updatedAt" | "isActive">),
      id: `agent-${Date.now()}`,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    mockAgents.push(newAgent);
    return HttpResponse.json(newAgent, { status: 201 });
  }),

  // ========================================
  // Admin
  // ========================================
  http.get(`${API_BASE_URL}/api/admin/health`, async () => {
    await delay(100);
    return HttpResponse.json({
      status: "healthy",
      timestamp: new Date().toISOString(),
      version: "1.0.0",
      database: {
        status: "connected",
        latency: 12,
      },
      aiProviders: {
        openai: {
          status: "operational",
          latency: 234,
        },
        anthropic: {
          status: "operational",
          latency: 198,
        },
      },
    });
  }),

  http.get(`${API_BASE_URL}/api/admin/costs`, async () => {
    await delay(300);
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      return {
        date: date.toISOString().split("T")[0],
        cost: Math.random() * 5 + 1,
      };
    });

    return HttpResponse.json({
      period: "30d",
      totalCostUsd: 124.56,
      costByProvider: {
        openai: 67.89,
        anthropic: 56.67,
      },
      costByDay: last30Days,
      tokenUsage: {
        input: 1234567,
        output: 567890,
        total: 1802457,
      },
    });
  }),
];
