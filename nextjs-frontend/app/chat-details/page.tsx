"use client"

import { useState, useEffect } from "react";
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { StreamingText } from "@/components/chat/StreamingText";
import { ArrowLeft, FileCode, Code, ChevronDown, ChevronUp, Bot, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface CodeFile {
    id: string;
    name: string;
    language: string;
    content: string;
}

interface ChatMessage {
    id: string;
    sender: "user" | "ai";
    content: string;
    files?: CodeFile[];
}

export default function ChatDetails() {
    const router = useRouter();
    const [activeFileId, setActiveFileId] = useState<string | null>(null);
    const [showCodePanel, setShowCodePanel] = useState(false);
    const [streamingComplete, setStreamingComplete] = useState(false);

    const codeFiles: CodeFile[] = [
        {
            id: "1",
            name: "ChatInterface.tsx",
            language: "typescript",
            content: `import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
// ... more code ...
export function ChatInterface() {
  const [isExpanded, setIsExpanded] = useState(false);
  // ... implementation ...
}`,
        },
        {
            id: "2",
            name: "ChatMessage.tsx",
            language: "typescript",
            content: `import { Avatar } from "@/components/ui/avatar";
// ... more imports ...
export function ChatMessage({ message, sender }) {
  return (
    <div className="flex gap-3 p-4">
      {/* Message content */}
    </div>
  );
}`,
        },
        {
            id: "3",
            name: "utils.ts",
            language: "typescript",
            content: `export function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}`,
        },
    ];

    const chatMessages: ChatMessage[] = [
        {
            id: "1",
            sender: "user",
            content: "How do I implement a chat interface?",
        },
        {
            id: "2",
            sender: "ai",
            content: "I've created a chat interface component for you. Here are the key files: ChatInterface.tsx, ChatMessage.tsx, and utils.ts. The ChatInterface component handles user input and manages the chat state. You can customize the styling using Tailwind CSS.",
            files: codeFiles,
        },
    ];

    useEffect(() => {
        if (codeFiles.length > 0 && !activeFileId) {
            setActiveFileId(codeFiles[0].id);
        }
    }, [codeFiles, activeFileId]);

    const activeFile = codeFiles.find(file => file.id === activeFileId) || codeFiles[0];

    const handleStreamingComplete = () => {
        setStreamingComplete(true);
    };

    const renderMessageContent = (message: ChatMessage) => {
        if (message.sender === 'user') {
            return <p>{message.content}</p>;
        } else {
            return (
                <>
                    <StreamingText
                        text={message.content}
                        speed={5}
                        onComplete={handleStreamingComplete}
                    />

                    {streamingComplete && message.files && (
                        <div className="flex flex-wrap gap-2 mt-4">
                            {message.files.map((file) => (
                                <Button
                                    key={file.id}
                                    variant="outline"
                                    size="sm"
                                    className={`flex items-center gap-2 transition-all ${activeFileId === file.id
                                        ? "border-primary/50 bg-primary/5 text-primary"
                                        : ""
                                        }`}
                                    onClick={() => {
                                        setActiveFileId(file.id);
                                        if (!showCodePanel) {
                                            setShowCodePanel(true);
                                        }
                                    }}
                                >
                                    <FileCode className="h-3.5 w-3.5" />
                                    {file.name}
                                </Button>
                            ))}
                        </div>
                    )}
                </>
            );
        }
    };

    return (
        <div className="flex flex-col h-screen overflow-hidden bg-background">
            {/* Header */}
            <header className="border-b flex items-center p-4 shrink-0 bg-background/95 backdrop-blur-sm sticky top-0 z-10">
                <Button variant="ghost" size="icon" onClick={() => router.push("/")} className="mr-3 rounded-full">
                    <ArrowLeft className="h-5 w-5" />
                </Button>
                <div className="flex flex-col">
                    <h1 className="font-medium text-lg">Chat Session</h1>
                    <p className="text-xs text-muted-foreground">AI Assistant</p>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden">
                {showCodePanel ? (
                    <ResizablePanelGroup direction="horizontal">
                        <ResizablePanel defaultSize={50} minSize={30} maxSize={70}>
                            <div className="h-full flex flex-col">
                                <ScrollArea className="flex-1 px-4 py-6">
                                    <div className="space-y-8 max-w-2xl mx-auto pb-24">
                                        {chatMessages.map((message) => (
                                            <div key={message.id} className="animate-fade-in">
                                                <div className="flex items-start gap-4">
                                                    <Avatar className={cn(
                                                        "h-8 w-8",
                                                        message.sender === 'user' ? "bg-primary/10 text-primary" : "bg-primary text-primary-foreground"
                                                    )}>
                                                        <AvatarFallback>
                                                            {message.sender === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                                        </AvatarFallback>
                                                    </Avatar>

                                                    <div className="flex-1 space-y-2">
                                                        <div className="prose prose-sm">
                                                            {renderMessageContent(message)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </ScrollArea>

                                {/* Add the ChatInterface component at the bottom of the left panel */}
                                <div className="p-4 border-t bg-background/80 backdrop-blur-sm">
                                    <ChatInterface />
                                </div>
                            </div>
                        </ResizablePanel>

                        <ResizableHandle className="bg-border" />

                        <ResizablePanel defaultSize={50}>
                            <div className="h-full flex flex-col">
                                <div className="border-b p-4 flex items-center gap-2 bg-background/95 backdrop-blur-sm sticky top-0 z-10">
                                    <FileCode className="h-4 w-4 text-muted-foreground" />
                                    <h2 className="font-medium text-sm">{activeFile?.name}</h2>
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground ml-auto">
                                        {activeFile?.language}
                                    </span>
                                </div>
                                <ScrollArea className="flex-1 p-6 bg-muted/30">
                                    <pre className="text-sm font-mono whitespace-pre-wrap break-all">
                                        <code>{activeFile?.content}</code>
                                    </pre>
                                </ScrollArea>
                            </div>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                ) : (
                    <div className="h-full flex flex-col">
                        <ScrollArea className="flex-1 px-4 py-6">
                            <div className="space-y-8 max-w-2xl mx-auto pb-24">
                                {chatMessages.map((message) => (
                                    <div key={message.id} className="animate-fade-in">
                                        <div className="flex items-start gap-4">
                                            <Avatar className={cn(
                                                "h-8 w-8",
                                                message.sender === 'user' ? "bg-primary/10 text-primary" : "bg-primary text-primary-foreground"
                                            )}>
                                                <AvatarFallback>
                                                    {message.sender === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                                </AvatarFallback>
                                            </Avatar>

                                            <div className="flex-1 space-y-2">
                                                <div className="prose prose-sm">
                                                    {renderMessageContent(message)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>

                        {/* Add the ChatInterface component at the bottom */}
                        <div className="p-4 border-t bg-background/80 backdrop-blur-sm">
                            <ChatInterface />
                        </div>
                    </div>
                )}
            </div>

            {/* Toggle code panel button */}
            <Button
                variant="outline"
                size="sm"
                className="fixed bottom-24 right-4 z-10 rounded-full shadow-md"
                onClick={() => setShowCodePanel(!showCodePanel)}
            >
                {showCodePanel ? (
                    <>
                        <ChevronUp className="mr-1 h-4 w-4" />
                        Hide Code
                    </>
                ) : (
                    <>
                        <ChevronDown className="mr-1 h-4 w-4" />
                        Show Code
                    </>
                )}
            </Button>
        </div>
    );
}