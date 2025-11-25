import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/**
 * MSW Server Setup
 * Intercepts API requests in Node.js for testing
 */

export const server = setupServer(...handlers);
