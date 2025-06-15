import { Column, TaskCard, User, TaskLabel } from "./types";

// Mock users
export const mockUsers: User[] = [
  { id: "1", name: "Alice Johnson", initials: "AJ" },
  { id: "2", name: "Bob Smith", initials: "BS" },
  { id: "3", name: "Carol Davis", initials: "CD" },
  { id: "4", name: "David Wilson", initials: "DW" },
  { id: "5", name: "Eva Brown", initials: "EB" },
];

// Mock labels
export const mockLabels: TaskLabel[] = [
  { id: "1", name: "Frontend", color: "bg-blue-500" },
  { id: "2", name: "Backend", color: "bg-green-500" },
  { id: "3", name: "Design", color: "bg-pink-500" },
  { id: "4", name: "Bug", color: "bg-red-500" },
  { id: "5", name: "Feature", color: "bg-purple-500" },
  { id: "6", name: "Research", color: "bg-yellow-500" },
];

// Mock cards - Start with empty board
export const mockCards: TaskCard[] = [];

// Mock columns
export const mockColumns: Column[] = [
  {
    id: "todo",
    title: "To do",
    cards: mockCards.filter((card) => card.status === "todo"),
  },
  {
    id: "doing",
    title: "Doing",
    cards: mockCards.filter((card) => card.status === "doing"),
  },
  {
    id: "done",
    title: "Done",
    cards: mockCards.filter((card) => card.status === "done"),
  },
];
