"use client";

import React, { useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { TaskCard } from './task-card';
import { TaskCard as TaskCardType } from '@/lib/types';

interface DraggableCardProps {
  card: TaskCardType;
  onClick?: () => void;
}

export function DraggableCard({ card, onClick }: DraggableCardProps) {
  const [dragStarted, setDragStarted] = useState(false);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: card.id,
    data: {
      containerId: card.containerId,
      card: card,
    },
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.6 : 1,
    transition: isDragging ? 'none' : 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    cursor: isDragging ? 'grabbing' : 'pointer',
    zIndex: isDragging ? 1000 : 'auto',
  };

  const handleClick = (e: React.MouseEvent) => {
    // Only handle click if we're not dragging
    if (!isDragging && !dragStarted) {
      onClick?.();
    }
  };

  const handleMouseDown = () => {
    setDragStarted(false);
  };

  const handleDragStart = () => {
    setDragStarted(true);
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      className={`
        ${isDragging 
          ? 'rotate-3 scale-105 shadow-2xl ring-2 ring-blue-300 ring-opacity-50' 
          : 'rotate-0 scale-100 hover:scale-102'
        }
        transition-all duration-200 ease-out
        ${isDragging ? 'drag-overlay' : ''}
      `}
    >
      <TaskCard 
        card={card} 
        className={`
          ${isDragging 
            ? 'shadow-xl border-blue-200 bg-white' 
            : 'hover:shadow-lg border-transparent'
          }
          transition-all duration-200 border-2
          ${!isDragging && 'hover:border-gray-200'}
        `} 
      />
    </div>
  );
} 