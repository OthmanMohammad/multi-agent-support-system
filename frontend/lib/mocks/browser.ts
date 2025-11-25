import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

/**
 * MSW Browser Setup
 * Intercepts API requests in the browser for development
 */

export const worker = setupWorker(...handlers);
