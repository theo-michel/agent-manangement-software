"use client";

import React, { useState, useCallback } from 'react';
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
import { Plus, Users, Star, Shield, Zap } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Column, TaskCard } from '@/lib/types';
import { createNewCardFromPrompt, NewCardAgentResponse } from '@/app/clientService';

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
  
  // Configure sensors with activation constraints
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        delay: 250,
        tolerance: 5,
      },
    })
  );

  const teamMembers = [
    { name: 'Alice', initials: 'AJ', color: 'bg-blue-500' },
    { name: 'Bob', initials: 'BS', color: 'bg-green-500' },
    { name: 'Carol', initials: 'CD', color: 'bg-purple-500' },
    { name: 'David', initials: 'DW', color: 'bg-orange-500' },
  ];

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
      
      // If card moved to "done", trigger dependent cards
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
      }
      
      return newColumns;
    });
  }, [columns]);

  const handleCardClick = useCallback((card: TaskCard) => {
    setSelectedCard(card);
    setIsModalOpen(true);
  }, []);

  const handleAddCard = useCallback((columnId: string) => {
    const newCard: TaskCard = {
      id: `card-${Date.now()}`,
      title: '',
      description: '',
      status: columnId as 'todo' | 'doing' | 'done',
      containerId: columnId,
      assignees: [],
      labels: [],
      progress: 0,
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
      
      // Set loading state
      setColumns(prevColumns => {
        const newColumns = [...prevColumns];
        const targetColumnIndex = newColumns.findIndex(col => col.id === updatedCard.containerId);
        if (targetColumnIndex !== -1) {
          const cardIndex = newColumns[targetColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
          if (cardIndex !== -1) {
            newColumns[targetColumnIndex].cards[cardIndex] = {
              ...newColumns[targetColumnIndex].cards[cardIndex],
              isLoading: true
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
        
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          
          // Update original card to show it was processed
          const targetColumnIndex = newColumns.findIndex(col => col.id === updatedCard.containerId);
          if (targetColumnIndex !== -1) {
            const cardIndex = newColumns[targetColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
            if (cardIndex !== -1) {
              const cardCount = response.card_data?.length || 0;
              newColumns[targetColumnIndex].cards[cardIndex] = {
                ...newColumns[targetColumnIndex].cards[cardIndex],
                isLoading: false,
                aiResponse: `AI processed and created ${cardCount} tasks (${response.execution_time?.toFixed(2)}s)`
              };
            }
          }
          
          // Create new cards based on AI response in TODO column
          const todoColumnIndex = newColumns.findIndex(col => col.id === 'todo');
          if (todoColumnIndex !== -1 && response.card_data && Array.isArray(response.card_data)) {
            // Create multiple cards from the AI response
            const newCards: TaskCard[] = response.card_data.map((cardData: any, index: number) => ({
              id: `card-${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${index}`,
              title: cardData.title || 'AI Generated Task',
              description: cardData.description || 'Generated by AI',
              status: 'todo' as const,
              containerId: 'todo',
              assignees: [],
              labels: cardData.task_type ? [cardData.task_type] : [],
              progress: 0,
              autoCreated: true,
              aiMetadata: {
                taskType: cardData.task_type,
                parameters: cardData.parameters,
                agentId: response.agent_id,
                executionTime: response.execution_time
              }
            }));
            
            newColumns[todoColumnIndex] = {
              ...newColumns[todoColumnIndex],
              cards: [...newColumns[todoColumnIndex].cards, ...newCards]
            };
          }
          
          return newColumns;
        });
      } catch (error) {
        // Handle error
        setColumns(prevColumns => {
          const newColumns = [...prevColumns];
          const targetColumnIndex = newColumns.findIndex(col => col.id === updatedCard.containerId);
          if (targetColumnIndex !== -1) {
            const cardIndex = newColumns[targetColumnIndex].cards.findIndex(card => card.id === updatedCard.id);
            if (cardIndex !== -1) {
              newColumns[targetColumnIndex].cards[cardIndex] = {
                ...newColumns[targetColumnIndex].cards[cardIndex],
                isLoading: false,
                aiResponse: `Error: Failed to process with AI`
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
            
            <div className="flex items-center space-x-3">
              {/* Team Members */}
              <div className="flex -space-x-2">
                {teamMembers.map((member, index) => (
                  <Avatar key={index} className="w-8 h-8 border-2 border-white">
                    <AvatarFallback className={`text-white text-xs font-medium ${member.color}`}>
                      {member.initials}
                    </AvatarFallback>
                  </Avatar>
                ))}
                <Button
                  size="sm"
                  className="w-8 h-8 p-0 rounded-full bg-white/20 hover:bg-white/30 border-2 border-white text-white"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              <Button
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-white/30"
              >
                <Users className="w-4 h-4 mr-2" />
                Invite
              </Button>

              <Button
                size="sm"
                className="bg-white/10 hover:bg-white/20 text-white border-white/20"
                variant="outline"
              >
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
                variant="ghost"
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
      />
    </div>
  );
} 