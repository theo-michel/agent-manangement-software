import { VapiCall } from './types';

const VAPI_API_URL = 'https://api.vapi.ai';
const VAPI_API_KEY = '2736c2ef-5818-4900-bb28-e93d55c63e99';

/**
 * Récupère les derniers appels Vapi
 * @param limit - Nombre d'appels à récupérer (par défaut: 1)
 * @returns Promesse contenant un tableau des derniers appels ou un tableau vide si aucun appel trouvé
 */
export async function getLatestVapiCalls(limit: number = 1): Promise<VapiCall[]> {
  try {
    const response = await fetch(`${VAPI_API_URL}/call?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${VAPI_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Erreur API Vapi: ${response.status} ${response.statusText}`);
    }

    const data: VapiCall[] = await response.json();
    
    if (!data || data.length === 0) {
      return [];
    }

    // Retourner uniquement les données demandées pour chaque appel
    return data.map(call => ({
      id: call.id,
      customerNumber: call.customer?.number,
      assistantId: call.assistantId,
      startedAt: call.startedAt,
      endedAt: call.endedAt,
      endedReason: call.endedReason,
      transcript: call.transcript,
      messages: call.messages,
    }));
  } catch (error) {
    console.error('Erreur lors de la récupération des derniers appels Vapi:', error);
    throw error;
  }
} 