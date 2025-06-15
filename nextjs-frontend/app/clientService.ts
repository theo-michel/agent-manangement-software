import "@/lib/clientConfig";
import {
  TaskCard,
  AIResponse,
  AICardSuggestion,
  TaskLabel,
  User,
} from "@/lib/types";

export * from "./openapi-client";

interface TriggerAgentRequest {
  prompt: string;
  context: {
    card: TaskCard;
  };
}

// Mock users for auto-created cards
const mockUsers: User[] = [
  {
    id: "1",
    name: "Alice Johnson",
    initials: "AJ",
    avatar: "/avatars/alice.jpg",
  },
  { id: "2", name: "Bob Smith", initials: "BS", avatar: "/avatars/bob.jpg" },
  {
    id: "3",
    name: "Carol Davis",
    initials: "CD",
    avatar: "/avatars/carol.jpg",
  },
];

// Mock labels for auto-created cards
const mockLabels: TaskLabel[] = [
  { id: "research", name: "Research", color: "bg-blue-500" },
  { id: "design", name: "Design", color: "bg-purple-500" },
  { id: "development", name: "Development", color: "bg-green-500" },
  { id: "testing", name: "Testing", color: "bg-orange-500" },
  { id: "urgent", name: "Urgent", color: "bg-red-500" },
  { id: "meeting", name: "Meeting", color: "bg-yellow-500" },
];

// Function to generate cards based on task type and context
function generateCardsForTask(
  prompt: string,
  originalCardId: string
): AICardSuggestion[] {
  const cards: AICardSuggestion[] = [];
  const promptLower = prompt.toLowerCase();

  if (
    promptLower.includes("market research") ||
    promptLower.includes("research")
  ) {
    // Market research scenario with dependencies
    cards.push({
      title: "Market Research Analysis",
      description:
        "Conduct comprehensive market research to understand target audience, competitors, and market opportunities.",
      labels: [mockLabels[0]], // Research label
      assignees: [mockUsers[0]],
      priority: "high",
      dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week
    });

    cards.push({
      title: "Contact Industry Expert",
      description:
        "Reach out to industry expert for insights and validation of research findings.",
      dependsOn: [originalCardId], // Depends on the original card being done
      labels: [mockLabels[5]], // Meeting label
      assignees: [mockUsers[1]],
      priority: "medium",
      dueDate: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days
    });

    cards.push({
      title: "Compile Research Report",
      description:
        "Create comprehensive report with findings, recommendations, and next steps.",
      dependsOn: [originalCardId], // Also depends on original card
      labels: [mockLabels[0]], // Research label
      assignees: [mockUsers[0]],
      priority: "medium",
      dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 2 weeks
    });
  } else if (promptLower.includes("design") || promptLower.includes("ui")) {
    // Design workflow with dependencies
    cards.push({
      title: "User Research & Personas",
      description:
        "Research target users and create detailed personas to guide design decisions.",
      labels: [mockLabels[0], mockLabels[1]], // Research + Design
      assignees: [mockUsers[2]],
      priority: "high",
    });

    cards.push({
      title: "Wireframes & Prototypes",
      description: "Create low-fidelity wireframes and interactive prototypes.",
      dependsOn: [originalCardId], // Depends on original design task
      labels: [mockLabels[1]], // Design
      assignees: [mockUsers[2]],
      priority: "high",
    });

    cards.push({
      title: "Design System Review",
      description:
        "Review and update design system components based on new requirements.",
      labels: [mockLabels[1]], // Design
      assignees: [mockUsers[1]],
      priority: "medium",
    });
  } else if (
    promptLower.includes("development") ||
    promptLower.includes("code")
  ) {
    // Development workflow
    cards.push({
      title: "Technical Architecture",
      description:
        "Define technical architecture and choose appropriate technologies.",
      labels: [mockLabels[2]], // Development
      assignees: [mockUsers[1]],
      priority: "high",
    });

    cards.push({
      title: "Implementation Phase 1",
      description: "Implement core functionality and basic features.",
      dependsOn: [originalCardId],
      labels: [mockLabels[2]], // Development
      assignees: [mockUsers[1], mockUsers[2]],
      priority: "high",
    });

    cards.push({
      title: "Code Review & Testing",
      description:
        "Conduct thorough code review and implement automated tests.",
      dependsOn: [originalCardId],
      labels: [mockLabels[3]], // Testing
      assignees: [mockUsers[0]],
      priority: "medium",
    });
  } else {
    // Generic task breakdown
    cards.push({
      title: "Planning & Requirements",
      description: "Define detailed requirements and create project plan.",
      labels: [mockLabels[0]], // Research
      assignees: [mockUsers[0]],
      priority: "high",
    });

    cards.push({
      title: "Implementation",
      description: "Execute the main implementation based on requirements.",
      dependsOn: [originalCardId],
      labels: [mockLabels[2]], // Development
      assignees: [mockUsers[1]],
      priority: "high",
    });

    cards.push({
      title: "Review & Validation",
      description: "Review deliverables and validate against requirements.",
      dependsOn: [originalCardId],
      labels: [mockLabels[3]], // Testing
      assignees: [mockUsers[2]],
      priority: "medium",
    });
  }

  return cards;
}

export async function triggerAgent(
  request: TriggerAgentRequest
): Promise<AIResponse> {
  // Simulate network delay (1-3 seconds)
  const delay = Math.random() * 2000 + 1000;
  await new Promise((resolve) => setTimeout(resolve, delay));

  // Simulate occasional failures (5% chance)
  if (Math.random() < 0.05) {
    return {
      textualResponse: "",
      cardsToCreate: [],
      success: false,
      error: "Service temporarily unavailable. Please try again.",
    };
  }

  const prompt = request.prompt.toLowerCase();
  const originalCardId = request.context.card.id;

  // Generate contextual textual response
  let textualResponse: string;

  if (prompt.includes("market research")) {
    textualResponse =
      "J'ai analysé votre demande de market research. Voici mon plan d'action :\n\n• **Market Research Analysis** : Une analyse complète du marché pour comprendre votre audience cible\n• **Contact Industry Expert** : Cette tâche sera déclenchée automatiquement quand le market research sera terminé\n• **Compile Research Report** : Compilation finale des résultats\n\nLe système créera automatiquement la tâche 'Contact Industry Expert' dans la colonne TODO quand vous marquerez le market research comme terminé. C'est un workflow intelligent avec dépendances !";
  } else if (prompt.includes("design")) {
    textualResponse =
      "Pour ce projet design, j'ai structuré un workflow complet :\n\n• **User Research** : Recherche utilisateur pour guider les décisions\n• **Wireframes & Prototypes** : Sera déclenché quand le design principal sera fini\n• **Design System Review** : Mise à jour du système de design\n\nLes tâches avec dépendances seront automatiquement activées selon votre progression !";
  } else if (prompt.includes("development")) {
    textualResponse =
      "J'ai créé un plan de développement structuré :\n\n• **Technical Architecture** : Définition de l'architecture technique\n• **Implementation Phase 1** : Développement principal (dépend de votre tâche)\n• **Code Review & Testing** : Tests et validation (dépend aussi de votre tâche)\n\nLe système gérera automatiquement les dépendances entre les tâches !";
  } else {
    textualResponse =
      "J'ai analysé votre tâche et créé un plan structuré :\n\n• **Planning & Requirements** : Définition des besoins\n• **Implementation** : Exécution principale (sera déclenchée quand votre tâche sera terminée)\n• **Review & Validation** : Validation finale\n\nLes tâches dépendantes seront automatiquement créées dans TODO quand les tâches parentes seront marquées comme terminées !";
  }

  // Generate cards to create
  const cardsToCreate = generateCardsForTask(request.prompt, originalCardId);

  return {
    textualResponse,
    cardsToCreate,
    success: true,
  };
}
