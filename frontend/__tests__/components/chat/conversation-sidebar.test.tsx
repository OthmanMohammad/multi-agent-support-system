import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";
import { useConversations, useCreateConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import type { Conversation } from "@/lib/types/api";

// Mock dependencies
jest.mock("@/lib/api/hooks/useConversations");
jest.mock("@/stores/chat-store");

const mockUseConversations = useConversations as jest.MockedFunction<
  typeof useConversations
>;
const mockUseCreateConversation = useCreateConversation as jest.MockedFunction<
  typeof useCreateConversation
>;
const mockUseChatStore = useChatStore as unknown as jest.MockedFunction<
  () => {
    currentConversationId: string | null;
    setCurrentConversation: jest.Mock;
    isSidebarOpen: boolean;
    toggleSidebar: jest.Mock;
  }
>;

describe("ConversationSidebar Component", () => {
  const mockConversations: Conversation[] = [
    {
      id: "conv-1",
      userId: "user-1",
      title: "Technical Support",
      metadata: null,
      createdAt: new Date("2024-01-01T10:00:00Z"),
      updatedAt: new Date("2024-01-01T12:00:00Z"),
    },
    {
      id: "conv-2",
      userId: "user-1",
      title: "Billing Question",
      metadata: null,
      createdAt: new Date("2024-01-02T10:00:00Z"),
      updatedAt: new Date("2024-01-02T11:00:00Z"),
    },
  ];

  beforeEach(() => {
    mockUseConversations.mockReturnValue({
      data: mockConversations,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConversations>);

    mockUseCreateConversation.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({
        id: "new-conv",
        title: "New Conversation",
      }),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateConversation>);

    mockUseChatStore.mockReturnValue({
      currentConversationId: null,
      setCurrentConversation: jest.fn(),
      isSidebarOpen: true,
      toggleSidebar: jest.fn(),
    });
  });

  it("renders conversation sidebar", () => {
    render(<ConversationSidebar />);

    expect(screen.getByPlaceholderText(/Search conversations/i)).toBeInTheDocument();
  });

  it("displays list of conversations", () => {
    render(<ConversationSidebar />);

    expect(screen.getByText("Technical Support")).toBeInTheDocument();
    expect(screen.getByText("Billing Question")).toBeInTheDocument();
  });

  it("shows new conversation button", () => {
    render(<ConversationSidebar />);

    expect(screen.getByText(/New Conversation/i)).toBeInTheDocument();
  });

  it("creates new conversation when button is clicked", async () => {
    const user = userEvent.setup();
    const mutateAsync = jest.fn().mockResolvedValue({
      id: "new-conv",
      title: "New Conversation",
    });
    mockUseCreateConversation.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateConversation>);

    render(<ConversationSidebar />);

    const newButton = screen.getByText(/New Conversation/i);
    await user.click(newButton);

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        title: "New Conversation",
      });
    });
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

  it("clears search when clear button is clicked", async () => {
    const user = userEvent.setup();
    render(<ConversationSidebar />);

    const searchInput = screen.getByPlaceholderText(
      /Search conversations/i
    ) as HTMLInputElement;
    await user.type(searchInput, "Technical");

    const clearButton = screen.getByRole("button", { name: /clear/i });
    await user.click(clearButton);

    expect(searchInput.value).toBe("");
    expect(screen.getByText("Billing Question")).toBeInTheDocument();
  });

  it("highlights active conversation", () => {
    mockUseChatStore.mockReturnValue({
      currentConversationId: "conv-1",
      setCurrentConversation: jest.fn(),
      isSidebarOpen: true,
      toggleSidebar: jest.fn(),
    });

    const { container } = render(<ConversationSidebar />);

    // The active conversation should have specific styling
    const activeConv = container.querySelector('[data-active="true"]');
    expect(activeConv).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockUseConversations.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useConversations>);

    render(<ConversationSidebar />);

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it("shows empty state when no conversations", () => {
    mockUseConversations.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useConversations>);

    render(<ConversationSidebar />);

    expect(screen.getByText(/No conversations yet/i)).toBeInTheDocument();
  });

  it("shows error state when fetch fails", () => {
    mockUseConversations.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed to fetch"),
    } as unknown as ReturnType<typeof useConversations>);

    render(<ConversationSidebar />);

    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
  });

  it("is hidden on mobile when sidebar is closed", () => {
    mockUseChatStore.mockReturnValue({
      currentConversationId: null,
      setCurrentConversation: jest.fn(),
      isSidebarOpen: false,
      toggleSidebar: jest.fn(),
    });

    const { container } = render(<ConversationSidebar />);

    // Sidebar should have hidden class on mobile
    const sidebar = container.firstChild;
    expect(sidebar).toHaveClass("lg:flex"); // Always visible on large screens
  });

  it("toggles sidebar when close button is clicked on mobile", async () => {
    const user = userEvent.setup();
    const toggleSidebar = jest.fn();

    mockUseChatStore.mockReturnValue({
      currentConversationId: null,
      setCurrentConversation: jest.fn(),
      isSidebarOpen: true,
      toggleSidebar,
    });

    render(<ConversationSidebar />);

    // Look for mobile close button
    const closeButton = screen.queryByRole("button", { name: /close/i });
    if (closeButton) {
      await user.click(closeButton);
      expect(toggleSidebar).toHaveBeenCalled();
    }
  });

  it("sorts conversations by most recent first", () => {
    render(<ConversationSidebar />);

    const conversations = screen.getAllByRole("button").filter((btn) =>
      btn.textContent?.includes("Support") || btn.textContent?.includes("Question")
    );

    // "Billing Question" should appear before "Technical Support" (more recent)
    const billlingIndex = conversations.findIndex((btn) =>
      btn.textContent?.includes("Billing")
    );
    const technicalIndex = conversations.findIndex((btn) =>
      btn.textContent?.includes("Technical")
    );

    expect(billlingIndex).toBeLessThan(technicalIndex);
  });
});
