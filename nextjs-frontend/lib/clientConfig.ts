import { createClient, createConfig } from "@hey-api/client-axios";

// Create a properly configured client instance
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const client = createClient(createConfig({
  baseURL: baseURL,
}));

console.log('API Client configured with baseURL:', baseURL);
