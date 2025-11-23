import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import prisma from "@/lib/prisma";

/**
 * PATCH /api/conversations/[id]/messages/[messageId]
 * Update a message
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string; messageId: string } }
): Promise<NextResponse> {
  try {
    const session = await auth();

    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: conversationId, messageId } = params;
    const body = await request.json();

    // Validate input
    if (!body.content || typeof body.content !== "string") {
      return NextResponse.json(
        { error: "Content is required" },
        { status: 400 }
      );
    }

    // Verify message exists and belongs to user
    const message = await prisma.message.findFirst({
      where: {
        id: messageId,
        conversationId,
        userId: session.user.id,
      },
    });

    if (!message) {
      return NextResponse.json({ error: "Message not found" }, { status: 404 });
    }

    // Only allow editing user messages
    if (message.role !== "USER") {
      return NextResponse.json(
        { error: "Cannot edit non-user messages" },
        { status: 403 }
      );
    }

    // Update message
    const updatedMessage = await prisma.message.update({
      where: { id: messageId },
      data: { content: body.content },
    });

    return NextResponse.json(updatedMessage);
  } catch (error) {
    console.error("Error updating message:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/conversations/[id]/messages/[messageId]
 * Delete a message
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string; messageId: string } }
): Promise<NextResponse> {
  try {
    const session = await auth();

    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: conversationId, messageId } = params;

    // Verify message exists and belongs to user
    const message = await prisma.message.findFirst({
      where: {
        id: messageId,
        conversationId,
        userId: session.user.id,
      },
    });

    if (!message) {
      return NextResponse.json({ error: "Message not found" }, { status: 404 });
    }

    // Delete message
    await prisma.message.delete({
      where: { id: messageId },
    });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Error deleting message:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
