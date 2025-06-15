"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { TaskCard, User } from '@/lib/types';
import {
  Calendar,
  MessageCircle,
  Paperclip,
  User as UserIcon,
  Tag,
  Clock,
  BarChart3,
  Save,
  X,
  Plus,
  Sparkles,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CardDetailModalProps {
  card: TaskCard | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedCard: TaskCard) => void;
  availableUsers: User[];
  phoneCallsEnabled: boolean;
  webSearchEnabled: boolean;
}

export function CardDetailModal({
  card,
  isOpen,
  onClose,
  onSave,
  availableUsers,
  phoneCallsEnabled,
  webSearchEnabled,
}: CardDetailModalProps) {
  const [editedCard, setEditedCard] = useState<TaskCard | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (card) {
      setEditedCard({ ...card });
      setIsEditing(!card.title || card.title.trim() === '');
    }
  }, [card]);

  if (!card || !editedCard) return null;

  const handleSave = () => {
    if (editedCard.title.trim()) {
      onSave(editedCard);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    if (card.title) {
      setEditedCard({ ...card });
      setIsEditing(false);
    } else {
      onClose();
    }
  };

  const updateProgress = (progress: number) => {
    setEditedCard({ ...editedCard, progress });
  };

  const toggleAssignee = (user: User) => {
    const isAssigned = editedCard.assignees.some(a => a.id === user.id);
    if (isAssigned) {
      setEditedCard({
        ...editedCard,
        assignees: editedCard.assignees.filter(a => a.id !== user.id)
      });
    } else {
      setEditedCard({
        ...editedCard,
        assignees: [...editedCard.assignees, user]
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Tag className="w-5 h-5" />
            {isEditing ? 'Edit Card' : 'Card Details'}
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Title
              </label>
              {isEditing ? (
                <Input
                  value={editedCard.title}
                  onChange={(e) => setEditedCard({ ...editedCard, title: e.target.value })}
                  placeholder="Enter card title..."
                  className="text-lg font-medium"
                  autoFocus
                />
              ) : (
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">{editedCard.title}</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    Edit
                  </Button>
                </div>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Description
              </label>
              {isEditing ? (
                <Textarea
                  value={editedCard.description || ''}
                  onChange={(e) => setEditedCard({ ...editedCard, description: e.target.value })}
                  placeholder="Add a more detailed description..."
                  rows={4}
                />
              ) : (
                <div className="min-h-[100px] p-3 border rounded-md bg-gray-50">
                  {editedCard.description ? (
                    <p className="text-gray-700 whitespace-pre-wrap">{editedCard.description}</p>
                  ) : (
                    <p className="text-gray-400 italic">No description provided</p>
                  )}
                </div>
              )}
            </div>

            {/* AI Response */}
            {(editedCard.aiResponse || editedCard.isLoading) && (
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block flex items-center gap-2">
                  {editedCard.isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  ) : (
                    <Sparkles className="w-4 h-4 text-purple-600" />
                  )}
                  AI Response
                </label>
                {editedCard.isLoading ? (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                    <div className="flex items-center gap-2 mb-2">
                      <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                      <span className="text-sm font-medium text-blue-700">Processing with AI...</span>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-purple-50 border border-purple-200 rounded-md">
                    <p className="text-gray-700 whitespace-pre-wrap">{editedCard.aiResponse}</p>
                  </div>
                )}
              </div>
            )}

            {/* Feature Settings */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Feature Settings
              </label>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Phone Calls
                  </span>
                  <Badge className={phoneCallsEnabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}>
                    {phoneCallsEnabled ? "Enabled" : "Disabled"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <MessageCircle className="w-4 h-4" />
                    Web Search
                  </span>
                  <Badge className={webSearchEnabled ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600"}>
                    {webSearchEnabled ? "Enabled" : "Disabled"}
                  </Badge>
                </div>
              </div>
            </div>



            {/* Action Buttons */}
            {isEditing && (
              <div className="flex gap-2 pt-4 border-t">
                <Button onClick={handleSave} className="flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  Save Changes
                </Button>
                <Button variant="outline" onClick={handleCancel} className="flex items-center gap-2">
                  <X className="w-4 h-4" />
                  Cancel
                </Button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Status
              </label>
              <Badge
                variant="outline"
                className={cn(
                  "capitalize",
                  editedCard.status === 'todo' && "border-gray-300 text-gray-700",
                  editedCard.status === 'doing' && "border-blue-300 text-blue-700 bg-blue-50",
                  editedCard.status === 'done' && "border-green-300 text-green-700 bg-green-50"
                )}
              >
                {editedCard.status === 'todo' ? 'To Do' : editedCard.status === 'doing' ? 'In Progress' : 'Done'}
              </Badge>
            </div>

            {/* Assignees */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block flex items-center gap-2">
                <UserIcon className="w-4 h-4" />
                Assignees
              </label>
              <div className="space-y-2">
                {editedCard.assignees.map((user) => (
                  <div key={user.id} className="flex items-center gap-2">
                    <Avatar className="w-6 h-6">
                      {user.avatar ? (
                        <AvatarImage src={user.avatar} alt={user.name} />
                      ) : (
                        <AvatarFallback className="text-xs bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                          {user.initials}
                        </AvatarFallback>
                      )}
                    </Avatar>
                    <span className="text-sm text-gray-700">{user.name}</span>
                    {isEditing && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleAssignee(user)}
                        className="ml-auto text-red-600 hover:text-red-700"
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                ))}
                
                {isEditing && (
                  <div className="border-t pt-2">
                    <p className="text-xs text-gray-500 mb-2">Available users:</p>
                    <div className="space-y-1">
                      {availableUsers
                        .filter(user => !editedCard.assignees.some(a => a.id === user.id))
                        .map((user) => (
                          <Button
                            key={user.id}
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleAssignee(user)}
                            className="w-full justify-start h-8"
                          >
                            <Avatar className="w-5 h-5 mr-2">
                              <AvatarFallback className="text-xs bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                                {user.initials}
                              </AvatarFallback>
                            </Avatar>
                            <span className="text-sm">{user.name}</span>
                            <Plus className="w-3 h-3 ml-auto" />
                          </Button>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Due Date */}
            {editedCard.dueDate && (
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Due Date
                </label>
                <p className="text-sm text-gray-600">{formatDate(editedCard.dueDate)}</p>
              </div>
            )}

            {/* Activity Stats */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700">Activity</h3>
              
              {editedCard.comments !== undefined && editedCard.comments > 0 && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MessageCircle className="w-4 h-4" />
                  <span>{editedCard.comments} comment{editedCard.comments !== 1 ? 's' : ''}</span>
                </div>
              )}
              
              {editedCard.attachments !== undefined && editedCard.attachments > 0 && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Paperclip className="w-4 h-4" />
                  <span>{editedCard.attachments} attachment{editedCard.attachments !== 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 