import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MessageInput } from "@/components/chat/message-input";
import { useSendMessage } from "@/lib/api/hooks/useMessages";
import { useChatStore } from "@/stores/chat-store";

// Mock dependencies
jest.mock("@/lib/api/hooks/useMessages");
jest.mock("@/lib/api/hooks/useStreamResponse", () => ({
  useStreamResponse: () => ({
    startStream: jest.fn(),
    stopStream: jest.fn(),
    isStreaming: false,
  }),
}));
jest.mock("@/stores/chat-store");

const mockSendMessage = useSendMessage as jest.MockedFunction<
  typeof useSendMessage
>;
const mockUseChatStore = useChatStore as unknown as jest.MockedFunction<
  () => {
    isStreaming: boolean;
    addMessage: jest.Mock;
    setIsStreaming: jest.Mock;
  }
>;

describe("MessageInput Component", () => {
  const conversationId = "conv-1";

  beforeEach(() => {
    mockSendMessage.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({
        id: "msg-1",
        content: "Test message",
      }),
      isPending: false,
    } as any);

    mockUseChatStore.mockReturnValue({
      isStreaming: false,
      addMessage: jest.fn(),
      setIsStreaming: jest.fn(),
    });
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
    const mutateAsync = jest.fn().mockResolvedValue({ id: "msg-1" });
    mockSendMessage.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as any);

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    await user.type(textarea, "Test message");

    const sendButton = screen.getAllByRole("button").pop()!;
    await user.click(sendButton);

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        conversationId,
        content: "Test message",
        role: "USER",
        metadata: undefined,
      });
    });
  });

  it("sends message when Enter is pressed", async () => {
    const user = userEvent.setup();
    const mutateAsync = jest.fn().mockResolvedValue({ id: "msg-1" });
    mockSendMessage.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as any);

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    await user.type(textarea, "Test message{Enter}");

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalled();
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
    const mutateAsync = jest.fn().mockResolvedValue({ id: "msg-1" });
    mockSendMessage.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as any);

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(
      /Type a message/i
    ) as HTMLTextAreaElement;
    await user.type(textarea, "Test message");

    const sendButton = screen.getAllByRole("button").pop()!;
    await user.click(sendButton);

    await waitFor(() => {
      expect(textarea.value).toBe("");
    });
  });

  it("disables input when streaming", () => {
    mockUseChatStore.mockReturnValue({
      isStreaming: true,
      addMessage: jest.fn(),
      setIsStreaming: jest.fn(),
    });

    render(<MessageInput conversationId={conversationId} />);

    const textarea = screen.getByPlaceholderText(
      /AI is typing/i
    ) as HTMLTextAreaElement;
    expect(textarea).toBeDisabled();
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
    const mutateAsync = jest.fn();
    mockSendMessage.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as any);

    render(<MessageInput conversationId={conversationId} />);

    const sendButton = screen.getAllByRole("button").pop()!;
    await user.click(sendButton);

    expect(mutateAsync).not.toHaveBeenCalled();
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

    expect(screen.getByText(/Press/)).toBeInTheDocument();
    expect(screen.getByText(/Enter/)).toBeInTheDocument();
    expect(screen.getByText(/Shift\+Enter/)).toBeInTheDocument();
  });
});
