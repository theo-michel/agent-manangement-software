import { client } from "@/app/openapi-client/sdk.gen";

const configureClient = () => {
    // Use NEXT_PUBLIC prefix for client-side access
    const baseURL = "http://localhost:8000";

    client.setConfig({
        baseURL: baseURL,
    });
};

configureClient();
