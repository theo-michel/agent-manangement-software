"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { 
  DndContext, 
  DragEndEvent, 
  DragOverlay, 
  DragStartEvent, 
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors
} from '@dnd-kit/core';
import { DroppableColumn } from './droppable-column';
import { DraggableCard } from './draggable-card';
import { CardDetailModal } from './card-detail-modal';
import { Button } from '@/components/ui/button';
import { Plus, Users, Star, Shield, Zap, Phone, Search } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Column, TaskCard, TaskExecution } from '@/lib/types';
import { createNewCardFromPrompt, NewCardAgentResponse } from '@/app/clientService';
import { taskExecutionService } from '@/lib/task-execution-service';
import { performDeepSearch, triggerOutboundCall, triggerAgent } from '@/app/clientService';

// Initialize with empty columns
const initialColumns: Column[] = [
  { id: 'todo', title: 'To do', cards: [] },
  { id: 'doing', title: 'Doing', cards: [] },
  { id: 'done', title: 'Done', cards: [] },
];

export function TrelloBoard() {
  const [columns, setColumns] = useState<Column[]>(initialColumns);
  const [activeCard, setActiveCard] = useState<TaskCard | null>(null);
  const [selectedCard, setSelectedCard] = useState<TaskCard | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [phoneCallsEnabled, setPhoneCallsEnabled] = useState(true);
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const [executingTasks, setExecutingTasks] = useState<Map<string, TaskExecution>>(new Map());
  const [callCount, setCallCount] = useState(0); // Track number of calls made
  
  // Subscribe to execution service updates
  useEffect(() => {
    const unsubscribe = taskExecutionService.subscribe((tasks) => {
      setExecutingTasks(tasks);
    });
    return unsubscribe;
  }, []);

  // Get the appropriate phone number based on call count
  const getPhoneNumber = useCallback(() => {
    if (callCount === 0) {
      return '+33643451397'; // Théo's number for first call
    } else {
      return '+33651540270'; // Yoan's number for subsequent calls
    }
  }, [callCount]);

  // Get the appropriate name based on call count
  const getContactName = useCallback(() => {
    if (callCount === 0) {
      return 'Théo'; // First call to Théo
    } else {
      return 'Yoan'; // Subsequent calls to Yoan
    }
  }, [callCount]);

  // Automated card movement functions
  const moveCardToColumn = useCallback((cardId: string, targetColumn: 'todo' | 'doing' | 'done') => {
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Find the card in any column
      let sourceColumnIndex = -1;
      let cardIndex = -1;
      let card: TaskCard | null = null;
      
      for (let i = 0; i < newColumns.length; i++) {
        cardIndex = newColumns[i].cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          sourceColumnIndex = i;
          card = newColumns[i].cards[cardIndex];
          break;
        }
      }
      
      if (!card || sourceColumnIndex === -1) return prevColumns;
      
      // Remove card from source column
      newColumns[sourceColumnIndex].cards.splice(cardIndex, 1);
      
      // Add card to target column
      const targetColumnIndex = newColumns.findIndex(col => col.id === targetColumn);
      if (targetColumnIndex !== -1) {
        const updatedCard = {
          ...card,
          status: targetColumn,
          containerId: targetColumn,
          updatedAt: new Date(),
        };
        newColumns[targetColumnIndex].cards.push(updatedCard);
      }
      
      return newColumns;
    });
  }, []);

  const startTaskExecution = useCallback((cardId: string, executionType: TaskExecution['executionType']) => {
    // Start execution tracking
    const executionId = taskExecutionService.startExecution(cardId, executionType);
    
    // Move card to Doing column and update execution state
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Find the card in any column
      let sourceColumnIndex = -1;
      let cardIndex = -1;
      let card: TaskCard | null = null;
      
      for (let i = 0; i < newColumns.length; i++) {
        cardIndex = newColumns[i].cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          sourceColumnIndex = i;
          card = newColumns[i].cards[cardIndex];
          break;
        }
      }
      
      if (!card || sourceColumnIndex === -1) return prevColumns;
      
      // Remove card from source column
      newColumns[sourceColumnIndex].cards.splice(cardIndex, 1);
      
      // Add card to Doing column with execution state
      const doingColumnIndex = newColumns.findIndex(col => col.id === 'doing');
      if (doingColumnIndex !== -1) {
        const updatedCard = {
          ...card,
          status: 'doing' as const,
          containerId: 'doing',
          execution: {
            id: executionId,
            taskId: cardId,
            status: 'executing' as const,
            startedAt: new Date(),
            executionType,
          },
          updatedAt: new Date(),
        };
        newColumns[doingColumnIndex].cards.push(updatedCard);
      }
      
      return newColumns;
    });
    
    console.log(`🚀 Started ${executionType} execution for task ${cardId}`);
    return executionId;
  }, []);

  // Check if all sub-tasks of a parent are completed and update parent accordingly
  const checkParentTaskCompletion = useCallback((parentTaskId: string) => {
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      let parentCard: TaskCard | null = null;
      let parentColumnIndex = -1;
      let parentCardIndex = -1;

      // Find the parent task
      for (let colIndex = 0; colIndex < newColumns.length; colIndex++) {
        const cardIndex = newColumns[colIndex].cards.findIndex(card => card.id === parentTaskId);
        if (cardIndex !== -1) {
          parentCard = newColumns[colIndex].cards[cardIndex];
          parentColumnIndex = colIndex;
          parentCardIndex = cardIndex;
          break;
        }
      }

      if (!parentCard || !parentCard.subTaskIds || parentCard.subTaskIds.length === 0) {
        return prevColumns;
      }

      // Count completed sub-tasks
      let completedSubTasks = 0;
      const totalSubTasks = parentCard.subTaskIds.length;
      
      // Check each sub-task status across all columns
      for (const subTaskId of parentCard.subTaskIds) {
        for (const column of newColumns) {
          const subTask = column.cards.find(card => card.id === subTaskId);
          if (subTask && subTask.status === 'done') {
            completedSubTasks++;
            break;
          }
        }
      }

      // Update parent task
      const updatedParentCard = {
        ...parentCard,
        updatedAt: new Date(),
      };

      // If all sub-tasks are completed, move parent to Done
      if (completedSubTasks === totalSubTasks && parentCard.status !== 'done') {
        // Remove from current column
        newColumns[parentColumnIndex].cards.splice(parentCardIndex, 1);
        
        // Add to Done column
        const doneColumnIndex = newColumns.findIndex(col => col.id === 'done');
        if (doneColumnIndex !== -1) {
          updatedParentCard.status = 'done';
          updatedParentCard.containerId = 'done';
          updatedParentCard.aiResponse = `All ${totalSubTasks} sub-tasks completed! 🎉`;
          newColumns[doneColumnIndex].cards.push(updatedParentCard);
          
          console.log(`🎉 Parent task "${parentCard.title}" completed - all sub-tasks done!`);
        }
      } else {
        // Update parent task in current column
        newColumns[parentColumnIndex].cards[parentCardIndex] = updatedParentCard;
      }

            return newColumns;
    });
  }, []);

  const completeTaskExecution = useCallback((cardId: string, result?: any) => {
    // Complete execution tracking
    taskExecutionService.completeExecution(cardId, result);
    
    // Move card to Done column and update execution state
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Find the card in any column
      let sourceColumnIndex = -1;
      let cardIndex = -1;
      let card: TaskCard | null = null;
      
      for (let i = 0; i < newColumns.length; i++) {
        cardIndex = newColumns[i].cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          sourceColumnIndex = i;
          card = newColumns[i].cards[cardIndex];
          break;
        }
      }
      
      if (!card || sourceColumnIndex === -1) return prevColumns;
      
      // Remove card from source column
      newColumns[sourceColumnIndex].cards.splice(cardIndex, 1);
      
      // Add card to Done column with completed execution state
      const doneColumnIndex = newColumns.findIndex(col => col.id === 'done');
      if (doneColumnIndex !== -1) {
        const updatedCard = {
          ...card,
          status: 'done' as const,
          containerId: 'done',
          execution: card.execution ? {
            ...card.execution,
            status: 'completed' as const,
            completedAt: new Date(),
          } : undefined,
          updatedAt: new Date(),
        };
        newColumns[doneColumnIndex].cards.push(updatedCard);
        
        // Check if this is a sub-task and update parent if needed
        if (card.isSubTask && card.parentTaskId) {
          // Trigger parent completion check after state update
          setTimeout(() => checkParentTaskCompletion(card.parentTaskId!), 0);
        }
      }
      
      return newColumns;
    });
    
    console.log(`✅ Completed execution for task ${cardId}`);
  }, [checkParentTaskCompletion]);

  const failTaskExecution = useCallback((cardId: string, error: string) => {
    // Mark execution as failed
    taskExecutionService.failExecution(cardId, error);
    
    // Move card back to Todo column and update execution state
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Find the card in any column
      let sourceColumnIndex = -1;
      let cardIndex = -1;
      let card: TaskCard | null = null;
      
      for (let i = 0; i < newColumns.length; i++) {
        cardIndex = newColumns[i].cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          sourceColumnIndex = i;
          card = newColumns[i].cards[cardIndex];
          break;
        }
      }
      
      if (!card || sourceColumnIndex === -1) return prevColumns;
      
      // Remove card from source column
      newColumns[sourceColumnIndex].cards.splice(cardIndex, 1);
      
      // Add card back to Todo column with failed execution state
      const todoColumnIndex = newColumns.findIndex(col => col.id === 'todo');
      if (todoColumnIndex !== -1) {
        const updatedCard = {
          ...card,
          status: 'todo' as const,
          containerId: 'todo',
          execution: card.execution ? {
            ...card.execution,
            status: 'failed' as const,
            completedAt: new Date(),
            error,
          } : undefined,
          aiResponse: `Error: ${error}`,
          isLoading: false,
          updatedAt: new Date(),
        };
        newColumns[todoColumnIndex].cards.push(updatedCard);
      }
      
      return newColumns;
    });
    
    console.log(`❌ Failed execution for task ${cardId}: ${error}`);
  }, []);

  // Sort tasks by dependency order (tasks with no dependencies first)
  const sortTasksByDependencyOrder = useCallback((taskIds: string[]): string[] => {
    const getTaskDependencies = (taskId: string): string[] => {
      for (const column of columns) {
        const task = column.cards.find(card => card.id === taskId);
        if (task) {
          return [...(task.dependsOn || []), ...(task.blockedBy || [])];
        }
      }
      return [];
    };

    // Create dependency graph
    const dependencyMap = new Map<string, string[]>();
    taskIds.forEach(taskId => {
      dependencyMap.set(taskId, getTaskDependencies(taskId));
    });

    // Topological sort
    const sorted: string[] = [];
    const visiting = new Set<string>();
    const visited = new Set<string>();

    const visit = (taskId: string) => {
      if (visited.has(taskId)) return;
      if (visiting.has(taskId)) {
        // Circular dependency detected, continue anyway
        console.warn(`Circular dependency detected involving task ${taskId}`);
        return;
      }

      visiting.add(taskId);
      const dependencies = dependencyMap.get(taskId) || [];
      
      // Only consider dependencies that are within our task list
      const relevantDependencies = dependencies.filter(depId => taskIds.includes(depId));
      
      for (const depId of relevantDependencies) {
        visit(depId);
      }

      visiting.delete(taskId);
      visited.add(taskId);
      sorted.push(taskId);
    };

    taskIds.forEach(taskId => visit(taskId));
    
    console.log(`📊 Dependency order: ${sorted.map(id => {
      const task = columns.flatMap(col => col.cards).find(card => card.id === id);
      return task ? `"${task.title}"` : id;
    }).join(' → ')}`);
    
    return sorted;
  }, [columns]);

  // Execute sub-tasks sequentially based on dependency order
  const executeSubTasksSequentially = useCallback(async (subTaskIds: string[]) => {
    console.log(`🚀 Starting sequential execution of ${subTaskIds.length} sub-tasks`);
    
    // Sort tasks by dependency order
    const sortedTaskIds = sortTasksByDependencyOrder(subTaskIds);
    
    for (let i = 0; i < sortedTaskIds.length; i++) {
      const subTaskId = sortedTaskIds[i];
      
      try {
        // Find the sub-task in current state
        let subTask: TaskCard | undefined;
        
        // Use callback to get fresh state
        await new Promise<void>((resolve) => {
          setColumns(prevColumns => {
            for (const column of prevColumns) {
              const foundTask = column.cards.find(card => card.id === subTaskId);
              if (foundTask) {
                subTask = foundTask;
                break;
              }
            }
            return prevColumns; // No state change, just reading
          });
          resolve();
        });

        if (!subTask) {
          console.error(`Sub-task ${subTaskId} not found`);
          continue;
        }

        console.log(`⚡ Executing sub-task ${i + 1}/${sortedTaskIds.length}: "${subTask.title}" (Type: ${subTask.aiMetadata?.taskType || 'unknown'})`);
        
        // Determine execution type based on task type
        const taskType = subTask.aiMetadata?.taskType;
        let executionType: TaskExecution['executionType'];
        let apiResponse: any;

                 if (taskType === 'research_task') {
           executionType = 'web_search';
           
           // Check if web search is enabled
           if (!webSearchEnabled) {
             throw new Error('Web search is disabled');
           }
           
           // Start execution tracking and move to Doing
           startTaskExecution(subTaskId, executionType);
           
           // Create prompt for deep search
           const searchPrompt = `${subTask.title}${subTask.description ? ` - ${subTask.description}` : ''}`;
           
           console.log(`🔍 Performing deep search for: "${searchPrompt}"`);
           
           // Call deep search API using SDK
           const response = await performDeepSearch({
             body: {
               prompt: searchPrompt,
             },
           });

           apiResponse = response.data;
           console.log(`✅ Deep search completed for "${subTask.title}":`, apiResponse);
           
         } else if (taskType === 'phone_task') {
           executionType = 'phone_call';
           
           // Check if phone calls are enabled
           if (!phoneCallsEnabled) {
             throw new Error('Phone calls are disabled');
           }
           
           // Start execution tracking and move to Doing
           startTaskExecution(subTaskId, executionType);
           
           // Extract phone call parameters from task
           const taskDescription = subTask.description || '';
           const taskTitle = subTask.title;
           
           // Get the appropriate phone number and name based on call count
           const targetNumber = getPhoneNumber();
           const contactName = getContactName();
           
           console.log(`📞 Making outbound call #${callCount + 1} to ${contactName} (${targetNumber}) for: "${taskTitle}"`);
           
           // Call outbound call API using SDK with task-specific parameters
           const response = await triggerOutboundCall({
             body: {
               target_number: targetNumber,
               market_overview: taskDescription,
               name: contactName,
               action_to_take: taskTitle,
             },
           });

           // Increment call count after successful call initiation
           setCallCount(prev => prev + 1);

           apiResponse = response.data;
           console.log(`✅ Outbound call completed for "${subTask.title}":`, apiResponse);
           
         } else {
           // Unknown task type, treat as general AI processing
           executionType = 'ai_processing';
           
           startTaskExecution(subTaskId, executionType);
           
           // Create generic prompt
           const prompt = `Title: ${subTask.title}${subTask.description ? `\nDescription: ${subTask.description}` : ''}`;
           
           console.log(`🤖 Processing with AI: "${prompt}"`);
           
           // Call generic AI API using SDK
           const response = await triggerAgent({
             body: {
               prompt,
             },
           });

           apiResponse = response.data;
           console.log(`✅ AI processing completed for "${subTask.title}":`, apiResponse);
         }
        
        // Complete the sub-task execution with the API response
        completeTaskExecution(subTaskId, apiResponse);
        
        // Update the task with the API response
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          const doneColumnIndex = newColumns.findIndex(col => col.id === 'done');
          
          if (doneColumnIndex !== -1) {
            const taskIndex = newColumns[doneColumnIndex].cards.findIndex(card => card.id === subTaskId);
            if (taskIndex !== -1) {
              newColumns[doneColumnIndex].cards[taskIndex] = {
                ...newColumns[doneColumnIndex].cards[taskIndex],
                aiResponse: apiResponse.response || apiResponse.message || 'Task completed successfully',
                aiMetadata: {
                  ...newColumns[doneColumnIndex].cards[taskIndex].aiMetadata,
                  executionTime: apiResponse.execution_time,
                  agentId: apiResponse.agent_id || apiResponse.call_id,
                },
                updatedAt: new Date(),
              };
            }
          }
          
          return newColumns;
        });
        
        // Add delay between executions for better UX
        if (i < sortedTaskIds.length - 1) {
          console.log(`⏳ Waiting 3 seconds before next task...`);
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to execute sub-task';
        console.error(`❌ Sub-task "${subTaskId}" failed:`, errorMessage);
        
        // Fail the sub-task execution
        failTaskExecution(subTaskId, errorMessage);
        
        // Update task with error message
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          
          // Find task in any column and update it
          for (let colIndex = 0; colIndex < newColumns.length; colIndex++) {
            const taskIndex = newColumns[colIndex].cards.findIndex(card => card.id === subTaskId);
            if (taskIndex !== -1) {
              newColumns[colIndex].cards[taskIndex] = {
                ...newColumns[colIndex].cards[taskIndex],
                aiResponse: `Error: ${errorMessage}`,
                isLoading: false,
                updatedAt: new Date(),
              };
              break;
            }
          }
          
          return newColumns;
        });
      }
    }
    
    console.log(`🎉 Completed sequential execution of all ${sortedTaskIds.length} sub-tasks`);
  }, [columns, sortTasksByDependencyOrder, startTaskExecution, completeTaskExecution, failTaskExecution, phoneCallsEnabled, webSearchEnabled, callCount, getPhoneNumber, getContactName]);
   
  // Configure sensors with activation constraints
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        delay: 250,
        tolerance: 5,
      },
    })
  );



  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;
    const card = active.data.current?.card as TaskCard;
    setActiveCard(card);
  }, []);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCard(null);

    if (!over) return;

    const activeCardId = active.id as string;
    const overId = over.id as string;

    // Find the active card and its current container
    let activeCard: TaskCard | null = null;
    let activeContainer: string | null = null;

    for (const column of columns) {
      const card = column.cards.find(c => c.id === activeCardId);
      if (card) {
        activeCard = card;
        activeContainer = column.id;
        break;
      }
    }

    if (!activeCard || !activeContainer) return;

    // Determine the target container
    const targetContainer = overId;

    // If dropping in the same container, no action needed for now
    // (we could implement reordering within the same container later)
    if (activeContainer === targetContainer) return;

    // Move the card to the new container
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Remove card from source container
      const sourceColumnIndex = newColumns.findIndex(col => col.id === activeContainer);
      const sourceColumn = { ...newColumns[sourceColumnIndex] };
      sourceColumn.cards = sourceColumn.cards.filter(card => card.id !== activeCardId);
      
      // Add card to target container
      const targetColumnIndex = newColumns.findIndex(col => col.id === targetContainer);
      const targetColumn = { ...newColumns[targetColumnIndex] };
      
      // Update card's status and containerId
      const updatedCard = {
        ...activeCard!,
        status: targetContainer as 'todo' | 'doing' | 'done',
        containerId: targetContainer,
      };
      
      targetColumn.cards = [...targetColumn.cards, updatedCard];
      
      // Update the columns array
      newColumns[sourceColumnIndex] = sourceColumn;
      newColumns[targetColumnIndex] = targetColumn;
      
      // If card moved to "done", trigger dependent cards and check parent completion
      if (targetContainer === 'done') {
        const todoColumnIndex = newColumns.findIndex(col => col.id === 'todo');
        if (todoColumnIndex !== -1) {
          // Find all cards that depend on this card
          const dependentCards = newColumns[todoColumnIndex].cards.filter(card => 
            card.dependsOn?.includes(activeCardId) || card.blockedBy?.includes(activeCardId)
          );
          
          // Remove dependencies and move dependent cards to TODO if they have no other blockers
          dependentCards.forEach(dependentCard => {
            const cardIndex = newColumns[todoColumnIndex].cards.findIndex(c => c.id === dependentCard.id);
            if (cardIndex !== -1) {
              const updatedDependentCard = {
                ...dependentCard,
                dependsOn: dependentCard.dependsOn?.filter(id => id !== activeCardId) || [],
                blockedBy: dependentCard.blockedBy?.filter(id => id !== activeCardId) || [],
              };
              
              // If no more dependencies, the card is ready to work on
              if (updatedDependentCard.dependsOn.length === 0 && updatedDependentCard.blockedBy.length === 0) {
                // You could add visual indication here that the card is now ready
                console.log(`Card "${dependentCard.title}" is now ready to work on!`);
              }
              
              newColumns[todoColumnIndex].cards[cardIndex] = updatedDependentCard;
            }
          });
        }

        // If this is a sub-task that was completed, check parent task completion
        if (activeCard.isSubTask && activeCard.parentTaskId) {
          // We need to trigger this after the state update, so we'll do it in a setTimeout
          setTimeout(() => checkParentTaskCompletion(activeCard.parentTaskId!), 0);
        }
      }
      
      return newColumns;
    });
  }, [columns]);

  const handleCardClick = useCallback((card: TaskCard) => {
    setSelectedCard(card);
    setIsModalOpen(true);
  }, []);

  const handleAddCard = useCallback((columnId: string) => {
    // Only allow adding cards to the TODO column
    if (columnId !== 'todo') {
      console.warn('Cards can only be added to the TODO column');
      return;
    }
    
    const newCard: TaskCard = {
      id: `card-${Date.now()}`,
      title: '',
      description: '',
      status: 'todo', // Always set to 'todo' since we only allow adding to TODO
      containerId: 'todo', // Always set to 'todo'
      assignees: [],
      labels: [],
    };
    setSelectedCard(newCard);
    setIsModalOpen(true);
  }, []);

  const handleSaveCard = useCallback(async (updatedCard: TaskCard) => {
    // First, save the card to state
    setColumns(prevColumns => {
      const newColumns = [...prevColumns];
      
      // Check if this is a new card (no existing card with this ID)
      const existingCardFound = newColumns.some(col => 
        col.cards.some(card => card.id === updatedCard.id)
      );

      if (!existingCardFound) {
        // Add new card
        const targetColumnIndex = newColumns.findIndex(col => col.id === updatedCard.containerId);
        if (targetColumnIndex !== -1) {
          newColumns[targetColumnIndex] = {
            ...newColumns[targetColumnIndex],
            cards: [...newColumns[targetColumnIndex].cards, updatedCard]
          };
        }
      } else {
        // Update existing card
        for (let i = 0; i < newColumns.length; i++) {
          const cardIndex = newColumns[i].cards.findIndex(card => card.id === updatedCard.id);
          if (cardIndex !== -1) {
            newColumns[i] = {
              ...newColumns[i],
              cards: [
                ...newColumns[i].cards.slice(0, cardIndex),
                updatedCard,
                ...newColumns[i].cards.slice(cardIndex + 1)
              ]
            };
            break;
          }
        }
      }
      
      return newColumns;
    });

    setIsModalOpen(false);
    setSelectedCard(null);

    // If this is a new card with content, process it with AI
    const isNewCard = !columns.some(col => 
      col.cards.some(card => card.id === updatedCard.id)
    );

    if (isNewCard && updatedCard.title.trim()) {
      // Create prompt from card content
      const prompt = `Title: ${updatedCard.title}${updatedCard.description ? `\nDescription: ${updatedCard.description}` : ''}`;
      
      // Start AI execution and move parent task to Doing
      const executionId = startTaskExecution(updatedCard.id, 'ai_processing');
      
      // Update parent task in Doing column with execution metadata
      setColumns(prevColumns => {
        const newColumns = [...prevColumns];
        const doingColumnIndex = newColumns.findIndex(col => col.id === 'doing');
        if (doingColumnIndex !== -1) {
          const cardIndex = newColumns[doingColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
          if (cardIndex !== -1) {
            newColumns[doingColumnIndex].cards[cardIndex] = {
              ...newColumns[doingColumnIndex].cards[cardIndex],
              isLoading: true,
              isParentTask: true, // Mark as parent task
              execution: {
                id: executionId,
                taskId: updatedCard.id,
                status: 'executing',
                startedAt: new Date(),
                executionType: 'ai_processing'
              }
            };
          }
        }
        return newColumns;
      });

      try {
        // Call AI endpoint
        const axiosResponse = await createNewCardFromPrompt({
          body: {
            prompt: prompt,
            context: {
              card: updatedCard
            }
          }
        });
        
        if (!axiosResponse.data) {
          throw new Error('No data received from AI service');
        }
        
        const response: NewCardAgentResponse = axiosResponse.data;
        console.log("AI Response:", response);
        
        // Update parent task and create sub-tasks
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          const todoColumnIndex = newColumns.findIndex(col => col.id === 'todo');
          const doingColumnIndex = newColumns.findIndex(col => col.id === 'doing');
          
          if (todoColumnIndex !== -1 && doingColumnIndex !== -1 && response.card_data && Array.isArray(response.card_data)) {
            // Create sub-tasks from AI response
            const subTaskIds: string[] = [];
            const newCards: TaskCard[] = response.card_data.map((cardData: any, index: number) => {
              const subTaskId = `card-${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${index}`;
              subTaskIds.push(subTaskId);
              
              return {
                id: subTaskId,
                title: cardData.title || 'AI Generated Task',
                description: cardData.description || 'Generated by AI',
                status: 'todo' as const,
                containerId: 'todo',
                assignees: [],
                labels: cardData.task_type ? [cardData.task_type] : [],
                autoCreated: true,
                createdAt: new Date(),
                isSubTask: true,
                parentTaskId: updatedCard.id,
                aiMetadata: {
                  taskType: cardData.task_type,
                  parameters: cardData.parameters,
                  agentId: response.agent_id,
                  executionTime: response.execution_time
                }
              };
            });

            // Update parent task with sub-task references (stays in Doing)
            const parentCardIndex = newColumns[doingColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
            if (parentCardIndex !== -1) {
              const cardCount = subTaskIds.length;
              newColumns[doingColumnIndex].cards[parentCardIndex] = {
                ...newColumns[doingColumnIndex].cards[parentCardIndex],
                isLoading: false,
                subTaskIds,
                aiResponse: `AI created ${cardCount} sub-tasks - executing them now...`,

                execution: {
                  ...newColumns[doingColumnIndex].cards[parentCardIndex].execution!,
                  status: 'executing' // Still executing (waiting for sub-tasks)
                }
              };
            }
            
            // Add sub-tasks to Todo column
            newColumns[todoColumnIndex] = {
              ...newColumns[todoColumnIndex],
              cards: [...newColumns[todoColumnIndex].cards, ...newCards]
            };

            // Start automatic execution of sub-tasks
            setTimeout(() => {
              executeSubTasksSequentially(subTaskIds);
            }, 1000); // Small delay to let UI update
          }
          
          return newColumns;
        });
      } catch (error) {
        // Handle AI processing error - move parent task back to Todo
        const errorMessage = error instanceof Error ? error.message : 'Failed to process with AI';
        
        // Fail the execution and move back to Todo
        failTaskExecution(updatedCard.id, errorMessage);
        
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          const todoColumnIndex = newColumns.findIndex(col => col.id === 'todo');
          if (todoColumnIndex !== -1) {
            const cardIndex = newColumns[todoColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
            if (cardIndex !== -1) {
              newColumns[todoColumnIndex].cards[cardIndex] = {
                ...newColumns[todoColumnIndex].cards[cardIndex],
                isLoading: false,
                aiResponse: `Error: ${errorMessage}`,
              };
            }
          }
          return newColumns;
        });
      }
    }
  }, [columns]);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedCard(null);
  }, []);

  const handleNewTask = useCallback(() => {
    const newCard: TaskCard = {
      id: `card-${Date.now()}`,
      title: '',
      description: '',
      status: 'todo',
      containerId: 'todo',
      assignees: [],
      labels: [],
    };
    setSelectedCard(newCard);
    setIsModalOpen(true);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-red-400">
      {/* Header */}
      <header className="bg-black/10 backdrop-blur-sm border-b border-white/10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-white font-bold text-lg flex items-center gap-2">
                <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                  <span className="text-purple-600 font-bold text-sm">A</span>
                </div>
                Project Team Spirit
              </h1>
              <Star className="w-5 h-5 text-yellow-300 fill-current" />
              <Shield className="w-5 h-5 text-white/70" />
              <span className="text-white/90 text-sm">Acme, Inc.</span>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Feature Toggles */}
              <div className="flex items-center space-x-4 mr-4">
                <div className="flex items-center space-x-2">
                  <Phone className="w-4 h-4 text-white/70" />
                  <Label htmlFor="phone-toggle" className="text-white/90 text-sm cursor-pointer">
                    Phone Calls
                  </Label>
                  <Switch
                    id="phone-toggle"
                    checked={phoneCallsEnabled}
                    onCheckedChange={setPhoneCallsEnabled}
                    className="data-[state=checked]:bg-green-500"
                  />
                  {phoneCallsEnabled && (
                    <div className="flex items-center space-x-1">
                      <span className="text-white/70 text-xs bg-white/10 px-2 py-1 rounded">
                        Next: {getContactName()}
                      </span>
                      {callCount > 0 && (
                        <button
                          onClick={() => setCallCount(0)}
                          className="text-white/50 hover:text-white/80 text-xs bg-white/10 hover:bg-white/20 px-1 py-1 rounded"
                          title="Reset to call Théo first"
                        >
                          ↻
                        </button>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <Search className="w-4 h-4 text-white/70" />
                  <Label htmlFor="search-toggle" className="text-white/90 text-sm cursor-pointer">
                    Web Search
                  </Label>
                  <Switch
                    id="search-toggle"
                    checked={webSearchEnabled}
                    onCheckedChange={setWebSearchEnabled}
                    className="data-[state=checked]:bg-blue-500"
                  />
                </div>
              </div>

              {/* New Task Button */}
              <Button
                onClick={handleNewTask}
                className="bg-green-500 hover:bg-green-600 text-white font-medium px-4 py-2"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Task
              </Button>

              <Button className="bg-white/20 hover:bg-white/30 text-white border-white/30 px-3 py-2">
                <Users className="w-4 h-4 mr-2" />
                Invite
              </Button>

              <Button className="bg-white/10 hover:bg-white/20 text-white border-white/20 px-3 py-2">
                <Zap className="w-4 h-4 mr-2" />
                +12
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Board Content */}
      <main className="p-6">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-6 overflow-x-auto pb-4">
            {columns.map((column) => (
              <DroppableColumn 
                key={column.id} 
                column={column}
                onCardClick={handleCardClick}
                onAddCard={handleAddCard}
              />
            ))}
            
            {/* Add Another List Button */}
            <div className="flex-shrink-0">
              <Button
                className="w-80 h-12 bg-white/10 hover:bg-white/20 text-white border border-white/20 justify-start"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add another list
              </Button>
            </div>
          </div>

          {/* Drag Overlay for smooth animation */}
          <DragOverlay>
            {activeCard ? (
              <div className="rotate-3 scale-110 opacity-90 shadow-2xl">
                <DraggableCard card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>

      {/* Card Detail Modal */}
      <CardDetailModal
        card={selectedCard}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveCard}
        availableUsers={[]}
        phoneCallsEnabled={phoneCallsEnabled}
        webSearchEnabled={webSearchEnabled}
      />
    </div>
  );
} 