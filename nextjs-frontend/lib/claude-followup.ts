// import Anthropic from "@anthropic-ai/sdk";
// import { getLatestVapiCalls } from "./vapi";
// import { VapiCall } from "./types";

// const anthropic = new Anthropic({
//   apiKey: process.env.ANTHROPIC_API_KEY,
// });

// /**
//  * Génère un follow-up rapide sur les 2 derniers appels Vapi en utilisant Claude
//  * @returns Promesse contenant une ou deux phrases de follow-up
//  */
// export async function generateCallsFollowup(): Promise<string> {
//   try {
//     // Récupérer les 2 derniers appels
//     const calls = await getLatestVapiCalls(2);
    
//     if (calls.length === 0) {
//       return "Aucun appel récent trouvé.";
//     }

//     // Préparer le contenu des transcripts pour Claude
//     const transcriptsContent = calls.map((call, index) => {
//       const callNumber = index + 1;
//       const transcript = call.transcript || "No transcript available";
//       const startTime = call.startedAt ? new Date(call.startedAt).toLocaleString() : "Unknown time";
//       const customerNumber = call.customer?.number || "Unknown number";
      
//       return `Call ${callNumber} (${startTime}, customer: ${customerNumber}):\n${transcript}`;
//     }).join("\n\n");

//     // Faire l'appel à Claude
//     const msg = await anthropic.messages.create({
//       model: "claude-sonnet-4-20250514",
//       max_tokens: 200,
//       temperature: 0.7,
//       system: "You are an assistant that analyzes phone calls for a manager, regarding their team. Generate a very concise follow-up summary in 1-2 sentences maximum about the key points and actions to remember from the provided calls.",
//       messages: [
//         {
//           role: "user",
//           content: [
//             {
//               type: "text",
//               text: `Here are the transcripts of the 2 latest phone calls. Generate a brief follow-up of 1-2 sentences about the key points and actions to remember:\n\n${transcriptsContent}`
//             }
//           ]
//         }
//       ]
//     });

//     // Extraire le texte de la réponse de Claude
//     const followupText = msg.content
//       .filter((block: any) => block.type === 'text')
//       .map((block: any) => block.text)
//       .join('')
//       .trim();

//     return followupText || "Impossible de générer un follow-up pour ces appels.";

//   } catch (error) {
//     console.error('Erreur lors de la génération du follow-up:', error);
//     throw new Error(`Erreur lors de la génération du follow-up: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
//   }
// } 