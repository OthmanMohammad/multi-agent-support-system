/**
 * API Hooks Index
 *
 * Central export for all API hooks.
 */

// Conversation hooks
export {
  useConversations,
  useConversation,
  useCreateConversation,
} from "./useConversations";

// Message hooks
export { useSendMessage, useCreateMessage } from "./useMessages";

// Streaming hooks
export { useStreamResponse } from "./useStreamResponse";

// Customer hooks
export {
  useCustomers,
  useCustomer,
  useCustomerInteractions,
  useCreateCustomer,
} from "./useCustomers";

// Analytics hooks
export {
  useAnalyticsOverview,
  useAgentPerformance,
  useConversationAnalytics,
} from "./useAnalytics";

// Admin hooks
export {
  useHealthCheck,
  useAgents,
  useCostTracking,
  useSwitchBackend,
} from "./useAdmin";
