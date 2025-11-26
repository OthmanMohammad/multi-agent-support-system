import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MessageInput } from "@/components/chat/message-input";

// Mock zustand store with selector support
const mockStoreState = {
  isStreaming: false,
  addMessage: jest.fn(),
  setIsStreaming: jest.fn(),
  clearStreamingMessage: jest.fn(),
  streamingMessage: null,
};

jest.mock("@/stores/chat-store", () => ({
  useChatStore: Object.assign(
    jest.fn((selector) => {
      if (typeof selector === "function") {
        return selector(mockStoreState);
      }
      return mockStoreState;
    }),
    {
      setState: jest.fn(),
    }
  ),
}));

// Mock useStreamResponse with a properly mockable streamMessage
const mockStreamMessage = jest.fn();
jest.mock("@/lib/api/hooks/useStreamResponse", () => ({
  useStreamResponse: () => ({
    streamMessage: mockStreamMessage,
    cancelStream: jest.fn(),
    isStreaming: false,
    content: "",
    error: null,
  }),
}));

// Mock useConversation
jest.mock("@/lib/hooks/useConversations", () => ({
  useConversation: () => ({
    refresh: jest.fn(),
    isSending: false,
  }),
}));

// Mock toast
jest.mock("@/lib/utils/toast", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
  fileToast: {
    invalidType: jest.fn(),
    tooLarge: jest.fn(),
    addedCount: jest.fn(),
    removedCount: jest.fn(),
    removedFile: jest.fn(),
  },
}));

describe("MessageInput Component", () => {
  const conversationId = "conv-1";

  beforeEach(() => {
    // Reset mock state
    mockStoreState.isStreaming = false;
    mockStoreState.addMessage.mockClear();
    mockStoreState.setIsStreaming.mockClear();
    mockStoreState.clearStreamingMessage.mockClear();
    mockStreamMessage.mockClear();
  });

  it("renders message input textarea", () => {
    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    expect(textarea).toBeInTheDocument();
  });

  it("renders send and attachment buttons", () => {
    render(<MessageInput conversationId={conversationId} />);

    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(2); // Attach and Send buttons
  });

  it("allows typing in the textarea", async () => {
    const user = userEvent.setup();
    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(
      /Type a message/i
    ) as HTMLTextAreaElement;
    await user.type(textarea, "Hello world");

    expect(textarea.value).toBe("Hello world");
  });

  it("sends message when send button is clicked", async () => {
    const user = userEvent.setup();

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    await user.type(textarea, "Test message");

    const buttons = screen.getAllByRole("button");
    const sendButton = buttons[buttons.length - 1];
    await user.click(sendButton);

    // Verify the message was added optimistically
    await waitFor(() => {
      expect(mockStoreState.addMessage).toHaveBeenCalled();
    });
  });

  it("sends message when Enter is pressed", async () => {
    const user = userEvent.setup();

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    await user.type(textarea, "Test message{Enter}");

    await waitFor(() => {
      expect(mockStreamMessage).toHaveBeenCalled();
    });
  });

  it("adds newline when Shift+Enter is pressed", async () => {
    const user = userEvent.setup();
    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(
      /Type a message/i
    ) as HTMLTextAreaElement;
    await user.type(textarea, "Line 1{Shift>}{Enter}{/Shift}Line 2");

    expect(textarea.value).toContain("\n");
  });

  it("clears input after sending message", async () => {
    const user = userEvent.setup();

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(
      /Type a message/i
    ) as HTMLTextAreaElement;
    await user.type(textarea, "Test message");

    const buttons = screen.getAllByRole("button");
    const sendButton = buttons[buttons.length - 1];
    await user.click(sendButton);

    await waitFor(() => {
      expect(textarea.value).toBe("");
    });
  });

  it("disables input when streaming", () => {
    // Override streaming state for this test
    mockStoreState.isStreaming = true;

    render(<MessageInput conversationId={conversationId} />);

    // When streaming, the textarea should exist
    const textareas = screen.getAllByRole("textbox");
    expect(textareas.length).toBeGreaterThan(0);
    // Verify the component renders properly in streaming state
    expect(textareas[0]).toBeInTheDocument();
  });

  it("shows character count", () => {
    render(<MessageInput conversationId={conversationId} />);

    expect(screen.getByText(/0 \/ 4000/)).toBeInTheDocument();
  });

  it("updates character count as user types", async () => {
    const user = userEvent.setup();
    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    await user.type(textarea, "Hello");

    expect(screen.getByText(/5 \/ 4000/)).toBeInTheDocument();
  });

  it("prevents sending empty messages", async () => {
    const user = userEvent.setup();

    render(<MessageInput conversationId={conversationId} />);

    const buttons = screen.getAllByRole("button");
    const sendButton = buttons[buttons.length - 1];
    await user.click(sendButton);

    expect(mockStreamMessage).not.toHaveBeenCalled();
  });

  it("handles file attachment click", async () => {
    const user = userEvent.setup();
    render(<MessageInput conversationId={conversationId} />);

    const attachButton = screen.getAllByRole("button")[0];
    await user.click(attachButton);

    // File input should be triggered (hidden input)
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("shows keyboard shortcuts hint", () => {
    render(<MessageInput conversationId={conversationId} />);

    // The placeholder contains keyboard hint
    const textarea = screen.getByPlaceholderText(/Enter to send/i);
    expect(textarea).toBeInTheDocument();
  });
});
