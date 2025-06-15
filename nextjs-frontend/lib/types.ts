export interface User {
  id: string;
  name: string;
  avatar?: string;
  initials: string;
}

export interface AIMetadata {
  taskType?: string;
  parameters?: {
    topics?: string[];
    scope?: string;
    [key: string]: any;
  };
  agentId?: string;
  executionTime?: number;
}

export interface TaskExecution {
  id: string;
  taskId: string;
  status: "pending" | "executing" | "completed" | "failed";
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  agentId?: string;
  executionType: "ai_processing" | "web_search" | "phone_call";
}

export interface TaskCard {
  id: string;
  title: string;
  description?: string;
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
  subTaskIds?: string[]; // Array of sub-task IDs if this is a parent task
  autoCreated?: boolean; // Whether this card was auto-created by AI
  aiMetadata?: AIMetadata; // Metadata from AI processing
  execution?: TaskExecution; // Current execution state
  executionHistory?: TaskExecution[]; // History of all executions
  createdAt?: Date;
  updatedAt?: Date;
  isParentTask?: boolean; // Whether this task has sub-tasks
  coverImage?: string; // Will store the Base64 image string
  isGeneratingImage?: boolean; // To show a loading state
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

export interface VapiCall {
  id: string;
  customer?: {
    number?: string;
  };
  assistantId?: string;
  startedAt: string;
  endedAt?: string;
  endedReason?: string;
  transcript?: string;
  messages?: VapiMessage[];
}

export interface VapiMessage {
  id: string;
  role: string;
  content: string;
  timestamp: string;
}
