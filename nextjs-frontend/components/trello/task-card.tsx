"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { TaskCard as TaskCardType } from '@/lib/types';
import { Calendar, MessageCircle, Paperclip, Loader2, Sparkles, Link, Bot, Clock, Phone, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TaskCardProps {
  card: TaskCardType;
  className?: string;
}

export function TaskCard({ card, className }: TaskCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 100) return 'bg-green-500';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const getTaskTypeBadge = (taskType: string) => {
    switch (taskType) {
      case 'phone_task':
        return {
          icon: Phone,
          label: 'Phone Call',
          className: 'bg-emerald-100 text-emerald-700 border-emerald-200'
        };
      case 'research_task':
        return {
          icon: Search,
          label: 'Research',
          className: 'bg-indigo-100 text-indigo-700 border-indigo-200'
        };
      default:
        return null;
    }
  };

  return (
    <Card 
      className={cn(
        "w-full mb-3 cursor-pointer card-hover card-enter", 
        className
      )}
    >

      <CardContent className="p-4 relative">

        {card.coverImage && !card.isGeneratingImage && (
          <div className="w-full h-32 mb-3 rounded-md overflow-hidden">
            <img
              src={`data:image/png;base64,${card.coverImage}`}
              alt={card.title}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {card.isGeneratingImage && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex flex-col items-center justify-center z-10 rounded-lg">
            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
            <p className="text-sm text-blue-600 mt-2">Generating Image...</p>
          </div>
        )}
        
        {/* Labels */}
        {card.labels.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {card.labels.map((label) => (
              <div
                key={label.id}
                className={cn(
                  "h-2 w-8 rounded-full transition-all duration-200 hover:w-10", 
                  label.color
                )}
                title={label.name}
              />
            ))}
          </div>
        )}

        {/* Title */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-1 mb-1">
              <h3 className="text-sm font-medium text-gray-900 leading-relaxed line-clamp-3 flex-1">
                {card.title}
              </h3>
              {card.isLoading && (
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
              )}
              {card.aiResponse && !card.isLoading && (
                <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0" />
              )}
            </div>
            
            {/* Dependency and Auto-created indicators */}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {/* Task Type Badge */}
              {card.aiMetadata?.taskType && (() => {
                const taskTypeBadge = getTaskTypeBadge(card.aiMetadata.taskType);
                if (taskTypeBadge) {
                  const IconComponent = taskTypeBadge.icon;
                  return (
                    <Badge className={cn("text-xs", taskTypeBadge.className)}>
                      <IconComponent className="w-3 h-3 mr-1" />
                      {taskTypeBadge.label}
                    </Badge>
                  );
                }
                return null;
              })()}
              
              {card.autoCreated && (
                <Badge className="text-xs bg-blue-100 text-blue-700 border-blue-200">
                  <Bot className="w-3 h-3 mr-1" />
                  AI Created
                </Badge>
              )}
              {(card.dependsOn && card.dependsOn.length > 0) && (
                <Badge className="text-xs bg-orange-100 text-orange-700 border-orange-200">
                  <Link className="w-3 h-3 mr-1" />
                  Depends on {card.dependsOn.length}
                </Badge>
              )}
              {(card.blockedBy && card.blockedBy.length > 0) && (
                <Badge className="text-xs bg-red-100 text-red-700 border-red-200">
                  <Clock className="w-3 h-3 mr-1" />
                  Blocked
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* AI Response */}
        {card.aiResponse && !card.isLoading && (
          <div className="mb-3 p-2 bg-purple-50 border border-purple-200 rounded-md">
            <div className="flex items-center gap-1 mb-1">
              <Sparkles className="w-3 h-3 text-purple-600" />
              <span className="text-xs font-medium text-purple-700">AI Response</span>
            </div>
            <p className="text-xs text-purple-800 line-clamp-3">
              {card.aiResponse}
            </p>
          </div>
        )}

        {/* Loading State */}
        {card.isLoading && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center gap-1 mb-1">
              <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
              <span className="text-xs font-medium text-blue-700">Processing with AI...</span>
            </div>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}

        {/* Execution State */}
        {card.execution && card.execution.status === 'executing' && (
          <div className="mb-3 p-2 border rounded-md animate-pulse">
            <div className="flex items-center gap-1 mb-1">
              {card.execution.executionType === 'web_search' && (
                <>
                  <Search className="w-3 h-3 text-indigo-600 animate-pulse" />
                  <span className="text-xs font-medium text-indigo-700">Performing deep search...</span>
                </>
              )}
              {card.execution.executionType === 'phone_call' && (
                <>
                  <Phone className="w-3 h-3 text-emerald-600 animate-pulse" />
                  <span className="text-xs font-medium text-emerald-700">Making phone call...</span>
                </>
              )}
              {card.execution.executionType === 'ai_processing' && (
                <>
                  <Loader2 className="w-3 h-3 text-purple-600 animate-spin" />
                  <span className="text-xs font-medium text-purple-700">AI processing...</span>
                </>
              )}
            </div>
            <div className="flex space-x-1">
              {card.execution.executionType === 'web_search' && (
                <>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </>
              )}
              {card.execution.executionType === 'phone_call' && (
                <>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </>
              )}
              {card.execution.executionType === 'ai_processing' && (
                <>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Failed Execution State */}
        {card.execution && card.execution.status === 'failed' && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center gap-1 mb-1">
              <div className="w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <span className="text-xs font-medium text-red-700">Execution failed</span>
            </div>
            {card.execution.error && (
              <p className="text-xs text-red-600 line-clamp-2">
                {card.execution.error}
              </p>
            )}
          </div>
        )}

        {/* Completed Execution State */}
        {card.execution && card.execution.status === 'completed' && card.status === 'done' && (
          <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center gap-1 mb-1">
              <div className="w-3 h-3 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">✓</span>
              </div>
              <span className="text-xs font-medium text-green-700">
                {card.execution.executionType === 'web_search' && 'Search completed'}
                {card.execution.executionType === 'phone_call' && 'Call completed'}
                {card.execution.executionType === 'ai_processing' && 'Processing completed'}
              </span>
            </div>
            {card.execution.completedAt && (
              <p className="text-xs text-green-600">
                Completed at {new Date(card.execution.completedAt).toLocaleTimeString()}
              </p>
            )}
          </div>
        )}

        {/* Progress Bar */}
        {card.progress !== undefined && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">Progress</span>
              <span className="text-xs text-gray-600 font-medium">{card.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
              <div
                className={cn(
                  "h-1.5 rounded-full transition-all duration-500 ease-out", 
                  getProgressColor(card.progress)
                )}
                style={{ 
                  width: `${card.progress}%`,
                  transformOrigin: 'left center'
                }}
              />
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between">
          {/* Left side - Meta info */}
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {card.dueDate && (
              <div className="flex items-center gap-1 hover:text-gray-700 transition-colors">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(card.dueDate)}</span>
              </div>
            )}
            {card.attachments && card.attachments > 0 && (
              <div className="flex items-center gap-1 hover:text-gray-700 transition-colors">
                <Paperclip className="w-3 h-3" />
                <span>{card.attachments}</span>
              </div>
            )}
            {card.comments && card.comments > 0 && (
              <div className="flex items-center gap-1 hover:text-gray-700 transition-colors">
                <MessageCircle className="w-3 h-3" />
                <span>{card.comments}</span>
              </div>
            )}
          </div>

          {/* Right side - Assignees */}
          {card.assignees.length > 0 && (
            <div className="flex -space-x-1">
              {card.assignees.slice(0, 3).map((user, index) => (
                <Avatar 
                  key={user.id} 
                  className="w-6 h-6 border-2 border-white transition-transform hover:scale-110 hover:z-10 relative"
                >
                  {user.avatar ? (
                    <AvatarImage src={user.avatar} alt={user.name} />
                  ) : (
                    <AvatarFallback className="text-xs font-medium bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                      {user.initials}
                    </AvatarFallback>
                  )}
                </Avatar>
              ))}
              {card.assignees.length > 3 && (
                <div className="w-6 h-6 rounded-full bg-gray-300 border-2 border-white flex items-center justify-center hover:scale-110 transition-transform">
                  <span className="text-xs text-gray-600 font-medium">+{card.assignees.length - 3}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Special completion badge for done items */}
        {card.status === 'done' && card.progress === 100 && (
          <Badge className="mt-2 bg-green-100 text-green-800 border-green-200 animate-pulse">
            ✓ Complete
          </Badge>
        )}
      </CardContent>
    </Card>
  );
} 