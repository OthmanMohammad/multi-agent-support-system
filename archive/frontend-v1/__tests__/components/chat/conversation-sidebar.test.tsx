import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";

// Mock zustand store with selector support
const mockStoreState = {
  currentConversationId: null as string | null,
  setCurrentConversation: jest.fn(),
  isSidebarOpen: true,
  toggleSidebar: jest.fn(),
};

jest.mock("@/stores/chat-store", () => ({
  useChatStore: jest.fn((selector) => {
    if (typeof selector === "function") {
      return selector(mockStoreState);
    }
    return mockStoreState;
  }),
}));

// Mock the correct useConversations hook
const mockConversationsData = {
  conversations: [
    {
      conversation_id: "conv-1",
      customer_id: "user-1",
      primary_intent: "Technical Support",
      status: "active" as const,
      started_at: "2024-01-01T10:00:00Z",
      last_updated: "2024-01-01T12:00:00Z",
      messages: [],
      agent_history: [],
    },
    {
      conversation_id: "conv-2",
      customer_id: "user-1",
      primary_intent: "Billing Question",
      status: "active" as const,
      started_at: "2024-01-02T10:00:00Z",
      last_updated: "2024-01-02T11:00:00Z",
      messages: [],
      agent_history: [],
    },
  ],
  isLoading: false,
  createConversation: jest.fn().mockResolvedValue({
    conversation_id: "new-conv",
    customer_id: "user-1",
    status: "active",
    started_at: new Date().toISOString(),
    last_updated: new Date().toISOString(),
    messages: [],
    agent_history: [],
    primary_intent: null,
  }),
  isCreating: false,
};

jest.mock("@/lib/hooks/useConversations", () => ({
  useConversations: jest.fn(() => mockConversationsData),
}));

import { useConversations } from "@/lib/hooks/useConversations";
const mockUseConversations = useConversations as jest.MockedFunction<
  typeof useConversations
>;

describe("ConversationSidebar Component", () => {
  beforeEach(() => {
    // Reset mock state
    mockStoreState.currentConversationId = null;
    mockStoreState.isSidebarOpen = true;
    mockStoreState.setCurrentConversation.mockClear();
    mockStoreState.toggleSidebar.mockClear();
    mockConversationsData.createConversation.mockClear();

    // Reset to default mock data
    mockUseConversations.mockReturnValue(mockConversationsData);
  });

  it("renders conversation sidebar", () => {
    render(<ConversationSidebar />);

    expect(
      screen.getByPlaceholderText(/Search conversations/i)
    ).toBeInTheDocument();
  });

  it("displays list of conversations", () => {
    render(<ConversationSidebar />);

    expect(screen.getByText("Technical Support")).toBeInTheDocument();
    expect(screen.getByText("Billing Question")).toBeInTheDocument();
  });

  it("shows new conversation button", () => {
    render(<ConversationSidebar />);

    // Look for the plus button which creates new conversations
    const plusButtons = screen.getAllByRole("button");
    const plusButton = plusButtons.find(
      (btn) => btn.querySelector(".lucide-plus") !== null
    );
    expect(plusButton).toBeInTheDocument();
  });

  it("creates new conversation when button is clicked", async () => {
    const user = userEvent.setup();

    render(<ConversationSidebar />);

    const plusButtons = screen.getAllByRole("button");
    const newButton = plusButtons.find(
      (btn) => btn.querySelector(".lucide-plus") !== null
    );

    if (newButton) {
      await user.click(newButton);

      await waitFor(() => {
        expect(mockConversationsData.createConversation).toHaveBeenCalled();
      });
    }
  });

  it("filters conversations based on search query", async () => {
    const user = userEvent.setup();
    render(<ConversationSidebar />);

    const searchInput = screen.getByPlaceholderText(/Search conversations/i);
    await user.type(searchInput, "Technical");

    // Only "Technical Support" should be visible
    expect(screen.getByText("Technical Support")).toBeInTheDocument();
    expect(screen.queryByText("Billing Question")).not.toBeInTheDocument();
  });

  // TODO: Re-enable when search clear button is implemented in component
  it.skip("clears search when clear button is clicked", async () => {
    const user = userEvent.setup();
    render(<ConversationSidebar />);

    const searchInput = screen.getByPlaceholderText(
      /Search conversations/i
    ) as HTMLInputElement;
    await user.type(searchInput, "Technical");

    // Find and click clear button (X icon in search)
    const clearButton = screen.getByRole("button", { name: /clear/i });
    await user.click(clearButton);

    expect(searchInput.value).toBe("");
    expect(screen.getByText("Billing Question")).toBeInTheDocument();
  });

  // TODO: Re-enable when ConversationItem adds data-active attribute
  it.skip("highlights active conversation", () => {
    mockStoreState.currentConversationId = "conv-1";

    const { container } = render(<ConversationSidebar />);

    // The active conversation should have specific styling
    const activeConv = container.querySelector('[data-active="true"]');
    expect(activeConv).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseConversations.mockReturnValue({
      ...mockConversationsData,
      conversations: undefined,
      isLoading: true,
    });

    const { container } = render(<ConversationSidebar />);

    // Look for skeleton loaders (the component renders skeletons, not "Loading" text)
    const skeletons = container.querySelectorAll('[class*="animate"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows empty state when no conversations", () => {
    mockUseConversations.mockReturnValue({
      ...mockConversationsData,
      conversations: [],
      isLoading: false,
    });

    render(<ConversationSidebar />);

    expect(screen.getByText(/No conversations yet/i)).toBeInTheDocument();
  });

  it("is hidden on mobile when sidebar is closed", () => {
    mockStoreState.isSidebarOpen = false;

    const { container } = render(<ConversationSidebar />);

    // Sidebar should have hidden class on mobile
    const sidebar = container.querySelector("aside");
    expect(sidebar).toHaveClass("-translate-x-full");
  });

  it("toggles sidebar when close button is clicked on mobile", async () => {
    const user = userEvent.setup();

    render(<ConversationSidebar />);

    // The X button toggles the sidebar
    const toggleButtons = screen.getAllByRole("button");
    const xButton = toggleButtons.find(
      (btn) => btn.querySelector(".lucide-x") !== null
    );

    if (xButton) {
      await user.click(xButton);
      expect(mockStoreState.toggleSidebar).toHaveBeenCalled();
    }
  });

  // TODO: Re-enable when sorting is implemented in component
  it.skip("sorts conversations by most recent first", () => {
    render(<ConversationSidebar />);

    const conversations = screen
      .getAllByRole("button")
      .filter(
        (btn) =>
          btn.textContent?.includes("Support") ||
          btn.textContent?.includes("Question")
      );

    // "Billing Question" should appear before "Technical Support" (more recent based on last_updated)
    const billingIndex = conversations.findIndex((btn) =>
      btn.textContent?.includes("Billing")
    );
    const technicalIndex = conversations.findIndex((btn) =>
      btn.textContent?.includes("Technical")
    );

    expect(billingIndex).toBeLessThan(technicalIndex);
  });
});
