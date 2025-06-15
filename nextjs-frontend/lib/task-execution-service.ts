import { TaskCard, TaskExecution } from "./types";

export class TaskExecutionService {
  private static instance: TaskExecutionService;
  private executingTasks = new Map<string, TaskExecution>();
  private listeners = new Set<(tasks: Map<string, TaskExecution>) => void>();

  private constructor() {}

  static getInstance(): TaskExecutionService {
    if (!TaskExecutionService.instance) {
      TaskExecutionService.instance = new TaskExecutionService();
    }
    return TaskExecutionService.instance;
  }

  // Subscribe to execution state changes
  subscribe(listener: (tasks: Map<string, TaskExecution>) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    this.listeners.forEach((listener) =>
      listener(new Map(this.executingTasks))
    );
  }

  // Start task execution
  startExecution(
    taskId: string,
    executionType: TaskExecution["executionType"],
    agentId?: string
  ): string {
    const executionId = `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const execution: TaskExecution = {
      id: executionId,
      taskId,
      status: "executing",
      startedAt: new Date(),
      agentId,
      executionType,
    };

    this.executingTasks.set(taskId, execution);
    this.notifyListeners();

    console.log(`🚀 Started execution for task ${taskId} (${executionType})`);
    return executionId;
  }

  // Complete task execution
  completeExecution(taskId: string, result?: any): void {
    const execution = this.executingTasks.get(taskId);
    if (execution) {
      execution.status = "completed";
      execution.completedAt = new Date();

      this.executingTasks.delete(taskId);
      this.notifyListeners();

      console.log(`✅ Completed execution for task ${taskId}`);
    }
  }

  // Fail task execution
  failExecution(taskId: string, error: string): void {
    const execution = this.executingTasks.get(taskId);
    if (execution) {
      execution.status = "failed";
      execution.completedAt = new Date();
      execution.error = error;

      this.executingTasks.delete(taskId);
      this.notifyListeners();

      console.log(`❌ Failed execution for task ${taskId}: ${error}`);
    }
  }

  // Get current execution state
  getExecution(taskId: string): TaskExecution | undefined {
    return this.executingTasks.get(taskId);
  }

  // Get all executing tasks
  getExecutingTasks(): Map<string, TaskExecution> {
    return new Map(this.executingTasks);
  }

  // Check if task is currently executing
  isExecuting(taskId: string): boolean {
    return this.executingTasks.has(taskId);
  }

  // Get execution statistics
  getExecutionStats() {
    const tasks = Array.from(this.executingTasks.values());
    return {
      total: tasks.length,
      byType: tasks.reduce(
        (acc, task) => {
          acc[task.executionType] = (acc[task.executionType] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      ),
      longestRunning: tasks.reduce(
        (longest, task) => {
          if (!task.startedAt) return longest;
          const duration = Date.now() - task.startedAt.getTime();
          return duration > longest.duration
            ? { taskId: task.taskId, duration }
            : longest;
        },
        { taskId: "", duration: 0 }
      ),
    };
  }
}

// Singleton instance
export const taskExecutionService = TaskExecutionService.getInstance();
