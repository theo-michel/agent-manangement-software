"use client";

import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { Button } from '@/components/ui/button';
import { DraggableCard } from './draggable-card';
import { Column, TaskCard } from '@/lib/types';
import { Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DroppableColumnProps {
  column: Column;
  className?: string;
  onCardClick?: (card: TaskCard) => void;
  onAddCard?: (columnId: string) => void;
}

export function DroppableColumn({ column, className, onCardClick, onAddCard }: DroppableColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
    data: {
      containerId: column.id,
      accepts: ['card'],
      items: column.cards.map(card => card.id),
    },
  });

  const getColumnHeaderClass = (columnId: string) => {
    switch (columnId) {
      case 'todo':
        return 'text-gray-700';
      case 'doing':
        return 'text-blue-700';
      case 'done':
        return 'text-green-700';
      default:
        return 'text-gray-700';
    }
  };

  const getColumnAccentColor = (columnId: string) => {
    switch (columnId) {
      case 'todo':
        return 'border-gray-300 bg-gray-50';
      case 'doing':
        return 'border-blue-300 bg-blue-50';
      case 'done':
        return 'border-green-300 bg-green-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  return (
    <div 
      ref={setNodeRef}
      className={cn(
        "flex flex-col w-80 rounded-lg p-3 transition-all duration-300 ease-out",
        "border-2 border-transparent",
        getColumnAccentColor(column.id),
        isOver && "shadow-xl ring-4 ring-blue-300 ring-opacity-30 scale-102 border-blue-300",
        !isOver && "hover:shadow-md hover:scale-101",
        className
      )}
      style={{
        transform: isOver ? 'scale(1.02)' : 'scale(1)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className={cn(
          "font-semibold text-sm transition-colors duration-200", 
          getColumnHeaderClass(column.id),
          isOver && "text-blue-700"
        )}>
          {column.title}
        </h2>
        <span className={cn(
          "text-xs px-2 py-1 rounded-full transition-all duration-200",
          "text-gray-500 bg-gray-200",
          isOver && "text-blue-600 bg-blue-100 scale-110"
        )}>
          {column.cards.length}
        </span>
      </div>

      {/* Cards Drop Zone */}
      <div className={cn(
        "flex-1 space-y-0 transition-all duration-300 ease-out",
        "min-h-[200px] rounded-lg p-2 -m-2",
        isOver && "min-h-[220px] bg-blue-50/50 border-2 border-dashed border-blue-300"
      )}>
        {column.cards.map((card, index) => (
          <div
            key={card.id}
            className="animate-in slide-in-from-top-2 duration-200"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <DraggableCard 
              card={card} 
              onClick={() => onCardClick?.(card)}
            />
          </div>
        ))}
        
        {/* Visual drop indicator */}
        {isOver && (
          <div className="drop-indicator h-3 rounded-full mx-2 mb-2 transition-all duration-200" />
        )}

        {/* Empty state */}
        {column.cards.length === 0 && !isOver && (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-lg">
            Drop cards here
          </div>
        )}
      </div>

    </div>
  );
} 