import { NextRequest } from "next/server";
import { auth } from "@/auth";
import prisma from "@/lib/prisma";

/**
 * GET /api/conversations/[id]/messages/[messageId]/stream
 * Server-Sent Events (SSE) endpoint for streaming AI responses
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string; messageId: string } }
): Promise<Response> {
  try {
    const session = await auth();

    if (!session?.user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const { id: conversationId, messageId } = params;

    // Verify conversation belongs to user
    const conversation = await prisma.conversation.findFirst({
      where: {
        id: conversationId,
        userId: session.user.id,
      },
    });

    if (!conversation) {
      return new Response(JSON.stringify({ error: "Conversation not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Get the user message that triggered this response
    const userMessage = await prisma.message.findFirst({
      where: {
        id: messageId,
        conversationId,
      },
    });

    if (!userMessage) {
      return new Response(JSON.stringify({ error: "Message not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Create ReadableStream for SSE
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Helper function to send SSE data
          const sendEvent = (data: unknown): void => {
            const eventData = `data: ${JSON.stringify(data)}\n\n`;
            controller.enqueue(encoder.encode(eventData));
          };

          // TODO: Connect to your backend multi-agent system
          // For now, simulate streaming response
          const simulateStream = async (): Promise<void> => {
            const fullResponse =
              "This is a simulated AI response. In production, this will connect to your Oracle Cloud backend multi-agent system via HTTP/SSE to stream real-time responses from your AI agents.";

            // Split into chunks for realistic streaming
            const words = fullResponse.split(" ");
            let currentChunk = "";

            for (let i = 0; i < words.length; i++) {
              currentChunk = words.slice(0, i + 1).join(" ");

              sendEvent({
                type: "content",
                chunk: words[i] + (i < words.length - 1 ? " " : ""),
              });

              // Simulate network delay
              await new Promise((resolve) => setTimeout(resolve, 50));
            }

            // Save the complete message to database
            const assistantMessage = await prisma.message.create({
              data: {
                conversationId,
                userId: "assistant",
                role: "ASSISTANT",
                content: fullResponse,
                metadata: {
                  parentMessageId: messageId,
                  model: "multi-agent-system",
                  streamingEnabled: true,
                },
              },
            });

            // Update conversation timestamp
            await prisma.conversation.update({
              where: { id: conversationId },
              data: { updatedAt: new Date() },
            });

            // Send completion event
            sendEvent({
              type: "done",
              messageId: assistantMessage.id,
              timestamp: assistantMessage.createdAt.toISOString(),
              metadata: assistantMessage.metadata,
            });

            controller.close();
          };

          // TODO: Replace with actual backend integration
          /*
          // Example integration with your backend:
          const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
          const response = await fetch(`${backendUrl}/api/chat/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              conversationId,
              message: userMessage.content,
            }),
          });

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error('No response body');
          }

          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process SSE data from backend
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                sendEvent(data);
              }
            }
          }
          */

          await simulateStream();
        } catch (error) {
          console.error("Stream error:", error);
          const errorData = {
            type: "error",
            message:
              error instanceof Error ? error.message : "Stream error occurred",
          };
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(errorData)}\n\n`)
          );
          controller.close();
        }
      },
    });

    // Return SSE response
    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no", // Disable nginx buffering
      },
    });
  } catch (error) {
    console.error("Error setting up stream:", error);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
