import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import type { components } from "@/types/api";

/**
 * Advanced Export Utilities
 * Export data to PDF, Excel, CSV with beautiful formatting
 * Enterprise-grade document generation
 */

type Conversation = components["schemas"]["Conversation"];
type Message = components["schemas"]["Message"];
type Customer = components["schemas"]["Customer"];

// ========================================
// PDF Export with Beautiful Formatting
// ========================================

export async function exportConversationToPDF(
  conversation: Conversation,
  messages: Message[]
): Promise<void> {
  const doc = new jsPDF();

  // Header
  doc.setFontSize(20);
  doc.setTextColor(41, 128, 185);
  doc.text(conversation.title, 20, 20);

  doc.setFontSize(10);
  doc.setTextColor(127, 140, 141);
  doc.text(`Created: ${new Date(conversation.createdAt).toLocaleDateString()}`, 20, 28);
  doc.text(`Conversation ID: ${conversation.id}`, 20, 33);

  // Line separator
  doc.setDrawColor(189, 195, 199);
  doc.line(20, 38, 190, 38);

  // Messages
  let yPosition = 48;

  for (const message of messages) {
    // Check if we need a new page
    if (yPosition > 270) {
      doc.addPage();
      yPosition = 20;
    }

    // Role badge
    const isUser = message.role === "USER";
    doc.setFillColor(isUser ? 52 : 46, isUser ? 152 : 204, isUser ? 219 : 113);
    doc.roundedRect(20, yPosition - 5, 25, 7, 2, 2, "F");
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.text(message.role, 22, yPosition);

    // Timestamp
    doc.setFontSize(8);
    doc.setTextColor(149, 165, 166);
    const timestamp = new Date(message.createdAt).toLocaleString();
    doc.text(timestamp, 50, yPosition);

    yPosition += 8;

    // Message content
    doc.setFontSize(10);
    doc.setTextColor(44, 62, 80);
    const splitContent = doc.splitTextToSize(message.content, 170);
    doc.text(splitContent, 20, yPosition);
    yPosition += splitContent.length * 5 + 10;
  }

  // Footer on last page
  const totalPages = (doc as any).internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(149, 165, 166);
    doc.text(
      `Page ${i} of ${totalPages}`,
      doc.internal.pageSize.getWidth() / 2,
      doc.internal.pageSize.getHeight() - 10,
      { align: "center" }
    );
  }

  doc.save(`conversation-${conversation.id}.pdf`);
}

export async function exportCustomersToPDF(customers: Customer[]): Promise<void> {
  const doc = new jsPDF();

  // Title
  doc.setFontSize(18);
  doc.setTextColor(41, 128, 185);
  doc.text("Customer Report", 20, 20);

  doc.setFontSize(10);
  doc.setTextColor(127, 140, 141);
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 20, 28);
  doc.text(`Total Customers: ${customers.length}`, 20, 33);

  // Table
  autoTable(doc, {
    startY: 40,
    head: [["Name", "Email", "Company", "Total Interactions", "Last Activity"]],
    body: customers.map((customer) => [
      customer.name,
      customer.email,
      customer.company || "N/A",
      customer.totalInteractions.toString(),
      customer.lastInteraction
        ? new Date(customer.lastInteraction).toLocaleDateString()
        : "Never",
    ]),
    theme: "grid",
    headStyles: {
      fillColor: [41, 128, 185],
      textColor: [255, 255, 255],
      fontStyle: "bold",
    },
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
    alternateRowStyles: {
      fillColor: [245, 245, 245],
    },
  });

  doc.save(`customers-report-${new Date().toISOString().split("T")[0]}.pdf`);
}

// ========================================
// Excel Export with Formatting
// ========================================

export function exportConversationsToExcel(conversations: Conversation[]): void {
  const worksheet = XLSX.utils.json_to_sheet(
    conversations.map((conv) => ({
      ID: conv.id,
      Title: conv.title,
      "User ID": conv.userId,
      "Created At": new Date(conv.createdAt).toLocaleString(),
      "Updated At": new Date(conv.updatedAt).toLocaleString(),
    }))
  );

  // Set column widths
  worksheet["!cols"] = [
    { wch: 30 }, // ID
    { wch: 50 }, // Title
    { wch: 30 }, // User ID
    { wch: 20 }, // Created At
    { wch: 20 }, // Updated At
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Conversations");

  XLSX.writeFile(
    workbook,
    `conversations-${new Date().toISOString().split("T")[0]}.xlsx`
  );
}

export function exportCustomersToExcel(customers: Customer[]): void {
  const worksheet = XLSX.utils.json_to_sheet(
    customers.map((customer) => ({
      ID: customer.id,
      Name: customer.name,
      Email: customer.email,
      Company: customer.company || "",
      Phone: customer.phone || "",
      "Total Interactions": customer.totalInteractions,
      "Created At": new Date(customer.createdAt).toLocaleString(),
      "Last Activity": customer.lastInteraction
        ? new Date(customer.lastInteraction).toLocaleString()
        : "Never",
    }))
  );

  // Set column widths
  worksheet["!cols"] = [
    { wch: 30 }, // ID
    { wch: 25 }, // Name
    { wch: 30 }, // Email
    { wch: 25 }, // Company
    { wch: 15 }, // Phone
    { wch: 15 }, // Total Interactions
    { wch: 20 }, // Created At
    { wch: 20 }, // Last Activity
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Customers");

  XLSX.writeFile(
    workbook,
    `customers-${new Date().toISOString().split("T")[0]}.xlsx`
  );
}

export function exportAnalyticsToExcel(data: {
  overview: any;
  conversations: any;
  agents: any;
}): void {
  const workbook = XLSX.utils.book_new();

  // Overview sheet
  const overviewWS = XLSX.utils.json_to_sheet([
    {
      Metric: "Total Conversations",
      Value: data.overview.totalConversations,
    },
    {
      Metric: "Total Messages",
      Value: data.overview.totalMessages,
    },
    {
      Metric: "Total Customers",
      Value: data.overview.totalCustomers,
    },
    {
      Metric: "Avg Response Time (s)",
      Value: data.overview.avgResponseTime,
    },
    {
      Metric: "Satisfaction Score",
      Value: data.overview.satisfactionScore,
    },
    {
      Metric: "Active Agents",
      Value: data.overview.activeAgents,
    },
  ]);
  XLSX.utils.book_append_sheet(workbook, overviewWS, "Overview");

  // Conversations by day
  const convsWS = XLSX.utils.json_to_sheet(
    data.conversations.conversationsByDay.map((d: any) => ({
      Date: d.date,
      Conversations: d.count,
    }))
  );
  XLSX.utils.book_append_sheet(workbook, convsWS, "Conversations by Day");

  // Agent performance
  const agentsWS = XLSX.utils.json_to_sheet(
    data.agents.agents.map((a: any) => ({
      Agent: a.agentName,
      Conversations: a.totalConversations,
      Messages: a.totalMessages,
      "Avg Response Time": a.avgResponseTime,
      "Satisfaction Score": a.satisfactionScore,
      "Cost (USD)": a.costUsd,
    }))
  );
  XLSX.utils.book_append_sheet(workbook, agentsWS, "Agent Performance");

  XLSX.writeFile(
    workbook,
    `analytics-report-${new Date().toISOString().split("T")[0]}.xlsx`
  );
}

// ========================================
// CSV Export
// ========================================

export function exportToCSV(
  data: Record<string, any>[],
  filename: string
): void {
  const worksheet = XLSX.utils.json_to_sheet(data);
  const csv = XLSX.utils.sheet_to_csv(worksheet);

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
