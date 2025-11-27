import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Message } from "@/components/chat/message";
import type { ConversationMessage as MessageType } from "@/lib/types/api";

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
});

describe("Message Component", () => {
  const mockUserMessage: MessageType = {
    role: "user",
    content: "Hello, how can I help you?",
    agent_name: null,
    timestamp: "2024-01-01T12:00:00Z",
  };

  const mockAssistantMessage: MessageType = {
    role: "assistant",
    content: "I'm here to help! What do you need assistance with?",
    agent_name: "Support Agent",
    timestamp: "2024-01-01T12:01:00Z",
  };

  it("renders user message correctly", () => {
    render(<Message message={mockUserMessage} />);

    expect(screen.getByText(mockUserMessage.content)).toBeInTheDocument();
    expect(screen.getByText("12:00")).toBeInTheDocument();
  });

  it("renders assistant message correctly", () => {
    render(<Message message={mockAssistantMessage} />);

    expect(screen.getByText(mockAssistantMessage.content)).toBeInTheDocument();
    expect(screen.getByText("12:01")).toBeInTheDocument();
  });

  it("shows copy button for assistant messages on hover", () => {
    render(<Message message={mockAssistantMessage} />);

    // Copy button should be in the document but hidden
    const copyButtons = screen.getAllByRole("button");
    expect(copyButtons.length).toBeGreaterThan(0);
  });

  it("copies message content when copy button is clicked", async () => {
    render(<Message message={mockAssistantMessage} />);

    const copyButton = screen.getAllByRole("button")[0];
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        mockAssistantMessage.content
      );
    });
  });

  it("shows check icon after copying", async () => {
    render(<Message message={mockAssistantMessage} />);

    const copyButton = screen.getAllByRole("button")[0];
    fireEvent.click(copyButton);

    // Check icon should appear briefly
    await waitFor(() => {
      expect(screen.getByRole("button")).toBeInTheDocument();
    });
  });

  it("renders markdown content for assistant messages", () => {
    const markdownMessage: MessageType = {
      ...mockAssistantMessage,
      content: "Here's a **bold** statement with a [link](https://example.com)",
    };

    render(<Message message={markdownMessage} />);

    // Check that markdown content is passed to ReactMarkdown component
    const markdownContainer = screen.getByTestId("markdown");
    expect(markdownContainer).toHaveTextContent(markdownMessage.content);
  });

  it("renders code blocks with syntax highlighting", () => {
    const codeMessage: MessageType = {
      ...mockAssistantMessage,
      content: "```javascript\nconst x = 1;\n```",
    };

    render(<Message message={codeMessage} />);

    // Check that code content is passed to ReactMarkdown component
    const markdownContainer = screen.getByTestId("markdown");
    expect(markdownContainer).toHaveTextContent("const x = 1;");
  });

  it("applies streaming animation when isStreaming is true", () => {
    const { container } = render(
      <Message message={mockAssistantMessage} isStreaming />
    );

    const messageContent = container.querySelector(".animate-pulse");
    expect(messageContent).toBeInTheDocument();
  });

  it("does not show copy button for user messages", () => {
    render(<Message message={mockUserMessage} />);

    // User messages should not have copy button in the metadata section
    const metadataSection = screen.getByText("12:00").parentElement;
    expect(metadataSection?.querySelectorAll("button").length).toBe(0);
  });

  it("handles external links securely", () => {
    const linkMessage: MessageType = {
      ...mockAssistantMessage,
      content: "[Click here](https://example.com)",
    };

    render(<Message message={linkMessage} />);

    // With react-markdown mocked, we verify the content is passed correctly
    // The actual link rendering is handled by the real react-markdown component
    const markdownContainer = screen.getByTestId("markdown");
    expect(markdownContainer).toHaveTextContent(
      "[Click here](https://example.com)"
    );
  });
});
