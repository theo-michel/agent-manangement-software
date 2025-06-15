export interface User {
  id: string;
  name: string;
  avatar?: string;
  initials: string;
}

export interface TaskCard {
  id: string;
  title: string;
  description?: string;
  progress?: number;
  dueDate?: string;
  attachments?: number;
  comments?: number;
  assignees: User[];
  labels: TaskLabel[];
  status: "todo" | "doing" | "done";
  containerId: string;
  isLoading?: boolean;
  aiResponse?: string;
  dependsOn?: string[]; // Array of task IDs this task depends on
  blockedBy?: string[]; // Array of task IDs that are blocking this task
  isSubTask?: boolean; // Whether this is a sub-task (dependent task)
  parentTaskId?: string; // ID of the parent task if this is a sub-task
  autoCreated?: boolean; // Whether this card was auto-created by AI
}

export interface TaskLabel {
  id: string;
  name: string;
  color: string;
}

export interface Column {
  id: string;
  title: string;
  cards: TaskCard[];
}

export interface DragEndEvent {
  active: {
    id: string;
    data?: {
      current?: {
        containerId?: string;
        index?: number;
      };
    };
  };
  over?: {
    id: string;
    data?: {
      current?: {
        containerId?: string;
        accepts?: string[];
        items?: string[];
      };
    };
  };
}

export interface AICardSuggestion {
  title: string;
  description: string;
  dependsOn?: string[]; // IDs of cards this depends on
  blockedBy?: string[]; // IDs of cards that block this
  isSubTask?: boolean;
  parentTaskId?: string;
  labels?: TaskLabel[];
  assignees?: User[];
  dueDate?: string;
  priority?: "low" | "medium" | "high";
}

export interface AIResponse {
  textualResponse: string; // Explanation from AI
  cardsToCreate: AICardSuggestion[]; // Cards to auto-create
  success: boolean;
  error?: string;
}
