"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Search, 
  Brain, 
  Zap, 
  CheckCircle, 
  Clock, 
  Code, 
  Globe,
  Sparkles,
  ChevronRight,
  Activity,
  X,
  Loader2,
  Terminal,
  FileText
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchStep {
  id: string;
  type: 'search' | 'thinking' | 'code' | 'result' | 'summary';
  title: string;
  content: string;
  status: 'pending' | 'running' | 'completed';
  timestamp: Date;
  duration?: number;
  tokens?: {
    input: number;
    output: number;
  };
}

interface SearchSession {
  id: string;
  query: string;
  steps: SearchStep[];
  status: 'running' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
}

interface SearchProcessViewerProps {
  isVisible: boolean;
  searchQuery?: string;
  onClose?: () => void;
}

export function SearchProcessViewer({ isVisible, searchQuery, onClose }: SearchProcessViewerProps) {
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState<string>('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Get current active session
  const activeSession = sessions.find(s => s.id === activeSessionId);
  const steps = activeSession?.steps || [];

  // Mock search process simulation
  useEffect(() => {
    if (!isVisible || !searchQuery) return;

    const simulateSearchProcess = async () => {
      // Create new session
      const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newSession: SearchSession = {
        id: sessionId,
        query: searchQuery,
        steps: [],
        status: 'running',
        startTime: new Date()
      };

      // Add new session and set as active
      setSessions(prev => [...prev, newSession]);
      setActiveSessionId(sessionId);
      setCurrentStep(null);
      setStreamingText('');

      const mockSteps: Omit<SearchStep, 'id' | 'timestamp'>[] = [
        {
          type: 'thinking',
          title: 'Analyzing Query',
          content: `Thought: I need to conduct a comprehensive analysis of ${searchQuery}. Let me break this down into specific research areas and gather relevant information.`,
          status: 'pending'
        },
        {
          type: 'code',
          title: 'Executing Search Query',
          content: `tesla_analysis = web_search("${searchQuery} financial performance market analysis")
print("Tesla 2025 Analysis:")
print(tesla_analysis)`,
          status: 'pending'
        },
        {
          type: 'search',
          title: 'Web Search: Financial Analysis',
          content: 'Searching for Tesla stock analysis, financial metrics, and market outlook...',
          status: 'pending'
        },
        {
          type: 'result',
          title: 'Search Results Retrieved',
          content: `## Search Results

[Tesla (TSLA) Stock Forecast & Analyst Price Targets - Stock Analysis](https://stockanalysis.com/stocks/tsla/forecast/)
Stock forecasts and analyst price target predictions for Tesla, Inc. (TSLA) stock, with detailed revenue and earnings estimates...

[Tesla Stock Analysis 2025: Navigating Turbulence Amid Musk Backlash](https://moneysnippets.com/tesla-stock-analysis-2025/)
Understanding Tesla's Recent Performance Decline Year-over-Year Delivery Challenges. In the first quarter of 2025, Tesla reported 336,681 vehicle deliveries...

[Is Tesla Stock a Buy in 2025? 3-Year Performance Analysis](https://www.techi.com/tesla-stock-buy-2025-analysis-forecast/)
It takes more than a quick look at Tesla's share price or recent headlines to determine if the company's stock is a smart investment in 2025...`,
          status: 'pending'
        },
        {
          type: 'code',
          title: 'Analyzing Financial Metrics',
          content: `tesla_financials = web_search("Tesla TSLA financial metrics 2024 revenue earnings profit margins cash flow")
print("Tesla Financial Metrics:")
print(tesla_financials)`,
          status: 'pending'
        },
        {
          type: 'result',
          title: 'Financial Data Retrieved',
          content: `## Financial Metrics

Tesla Q4 2024 Results:
- Revenue: $25.7B (up 2% YoY)
- EPS: $2.35 (up 7% QoQ)
- Automotive Revenue: $19.8B (down 8% YoY)
- Energy Storage: $3.06B (up 113% YoY)
- Gross Margin: 16.3%
- Operating Cash Flow: $6.3B (record in Q3)`,
          status: 'pending'
        },
        {
          type: 'thinking',
          title: 'Synthesizing Analysis',
          content: 'Now I have comprehensive data on Tesla\'s financial performance, market position, and analyst forecasts. Let me synthesize this into a coherent analysis covering the key areas requested.',
          status: 'pending'
        },
        {
          type: 'summary',
          title: 'Final Analysis Complete',
          content: `# Tesla Stock Analysis for 2025

## Current Financial Position
Tesla reported mixed Q4 2024 results with revenue growth of 2% to $25.7B, though automotive revenue declined 8% YoY. The company showed resilience with EPS growth of 7% QoQ to $2.35 and record operating cash flow of $6.3B in Q3.

## Key Growth Drivers
- Energy storage segment surged 113% YoY to $3.06B
- FSD revenue reached $326M from Cybertruck and other features
- Expanding manufacturing capacity and cost optimization initiatives

## Market Outlook
Analysts project varied price targets for 2025, with some forecasting potential upside to $400+ by 2030. However, delivery challenges and margin pressure remain concerns.

## Investment Recommendation
Tesla faces headwinds in 2025 but maintains strong fundamentals in energy storage and autonomous driving technology. Long-term outlook remains positive despite near-term volatility.`,
          status: 'pending',
          tokens: { input: 9483, output: 1428 }
        }
      ];

      // Add steps one by one with delays
      for (let i = 0; i < mockSteps.length; i++) {
        const step: SearchStep = {
          ...mockSteps[i],
          id: `step-${i}`,
          timestamp: new Date(),
          status: 'running'
        };

        // Add step to current session
        setSessions(prev => prev.map(session => 
          session.id === sessionId 
            ? { ...session, steps: [...session.steps, step] }
            : session
        ));
        setCurrentStep(step.id);

        // Simulate streaming text effect
        await streamText(step.content, step.id, sessionId);

        // Mark as completed
        setSessions(prev => prev.map(session => 
          session.id === sessionId 
            ? { 
                ...session, 
                steps: session.steps.map(s => 
                  s.id === step.id 
                    ? { ...s, status: 'completed', duration: Math.random() * 5 + 2 }
                    : s
                )
              }
            : session
        ));

        setCurrentStep(null);
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Mark session as completed
      setSessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { ...session, status: 'completed', endTime: new Date() }
          : session
      ));
    };

    simulateSearchProcess();
  }, [isVisible, searchQuery]);

  const streamText = async (text: string, stepId: string, sessionId: string) => {
    setStreamingText('');
    const words = text.split(' ');
    
    for (let i = 0; i < words.length; i++) {
      const currentText = words.slice(0, i + 1).join(' ');
      setStreamingText(currentText);
      
      // Update the step content in real-time
      setSessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              steps: session.steps.map(s => 
                s.id === stepId 
                  ? { ...s, content: currentText }
                  : s
              )
            }
          : session
      ));

      await new Promise(resolve => setTimeout(resolve, 30 + Math.random() * 20));
    }
    
    setStreamingText('');
  };

  // Auto-scroll to bottom when new content is added
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [steps, streamingText]);

  const getStepIcon = (type: SearchStep['type'], status: SearchStep['status']) => {
    const iconClass = cn(
      "w-4 h-4 transition-all duration-300",
      status === 'running' && "animate-pulse",
      status === 'completed' && "text-green-600",
      status === 'pending' && "text-muted-foreground"
    );

    switch (type) {
      case 'thinking':
        return <Brain className={iconClass} />;
      case 'search':
        return <Search className={iconClass} />;
      case 'code':
        return <Terminal className={iconClass} />;
      case 'result':
        return <FileText className={iconClass} />;
      case 'summary':
        return <Sparkles className={iconClass} />;
      default:
        return <Activity className={iconClass} />;
    }
  };

  const getStepBadge = (type: SearchStep['type']) => {
    const badges = {
      thinking: { label: 'AI Thinking', variant: 'secondary' as const },
      search: { label: 'Web Search', variant: 'default' as const },
      code: { label: 'Code Execution', variant: 'outline' as const },
      result: { label: 'Results', variant: 'secondary' as const },
      summary: { label: 'Analysis', variant: 'default' as const }
    };

    const badge = badges[type];
    return (
      <Badge variant={badge.variant} className="text-xs">
        {badge.label}
      </Badge>
    );
  };

  const getStepContentStyle = (type: SearchStep['type']) => {
    switch (type) {
      case 'code':
        return "bg-slate-950 text-green-400 font-mono border border-slate-800";
      case 'thinking':
        return "bg-purple-50 text-purple-900 border border-purple-200";
      case 'search':
        return "bg-blue-50 text-blue-900 border border-blue-200";
      case 'result':
        return "bg-orange-50 text-orange-900 border border-orange-200";
      case 'summary':
        return "bg-emerald-50 text-emerald-900 border border-emerald-200";
      default:
        return "bg-muted text-muted-foreground border";
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed right-6 top-20 bottom-6 w-[420px] z-50 animate-in slide-in-from-right-2 duration-300">
      <Card className="h-full shadow-2xl border-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 overflow-hidden">
        <CardHeader className="pb-3 border-b bg-gradient-to-r from-primary/5 to-secondary/5">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Search className="w-4 h-4 text-white" />
              </div>
              AI Search Process
            </CardTitle>
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
          {(searchQuery || sessions.length > 0) && (
            <>
              <Separator className="my-2" />
              {/* Session Tabs */}
              {sessions.length > 1 && (
                <div className="flex items-center gap-1 mb-2 overflow-x-auto">
                  {sessions.slice(-3).map((session, index) => (
                    <Button
                      key={session.id}
                      variant={session.id === activeSessionId ? "default" : "ghost"}
                      size="sm"
                      className="h-6 px-2 text-xs flex-shrink-0"
                      onClick={() => setActiveSessionId(session.id)}
                    >
                      Run {sessions.length - 2 + index}
                      {session.status === 'running' && (
                        <Loader2 className="w-3 h-3 ml-1 animate-spin" />
                      )}
                    </Button>
                  ))}
                </div>
              )}
              {/* Current Query */}
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {sessions.length > 1 ? `Run ${sessions.findIndex(s => s.id === activeSessionId) + 1}` : 'Query'}
                </Badge>
                <p className="text-sm text-muted-foreground font-medium truncate">
                  {activeSession?.query || searchQuery}
                </p>
                {activeSession?.status === 'completed' && (
                  <Badge variant="secondary" className="text-xs">
                    ✓ Complete
                  </Badge>
                )}
              </div>
            </>
          )}
        </CardHeader>

        <CardContent className="p-0 h-full overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-6 max-w-full overflow-hidden">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={cn(
                    "relative transition-all duration-500 ease-out",
                    "animate-in slide-in-from-bottom-2"
                  )}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* Step Header */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-300 flex-shrink-0 mt-0.5",
                      step.status === 'completed' && "bg-green-50 border-green-200",
                      step.status === 'running' && "bg-primary/10 border-primary/30 animate-pulse",
                      step.status === 'pending' && "bg-muted border-muted-foreground/20"
                    )}>
                      {getStepIcon(step.type, step.status)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        {getStepBadge(step.type)}
                        {step.status === 'completed' && step.duration && (
                          <Badge variant="outline" className="text-xs">
                            {step.duration.toFixed(1)}s
                          </Badge>
                        )}
                        {step.tokens && (
                          <Badge variant="outline" className="text-xs">
                            {step.tokens.input + step.tokens.output} tokens
                          </Badge>
                        )}
                      </div>
                      <h4 className="font-medium text-sm leading-tight">
                        {step.title}
                      </h4>
                    </div>

                    <div className="flex-shrink-0">
                      {step.status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                      {step.status === 'running' && (
                        <Loader2 className="w-4 h-4 text-primary animate-spin" />
                      )}
                    </div>
                  </div>

                  {/* Step Content */}
                  <div className="ml-11 min-w-0 max-w-full">
                    <div className={cn(
                      "text-sm rounded-lg p-4 transition-all duration-300 search-process-content",
                      getStepContentStyle(step.type)
                    )}>
                      {step.type === 'code' ? (
                        <div className="overflow-x-auto max-w-full">
                          <pre className="text-xs leading-relaxed font-mono whitespace-pre">
                            <code className="block">
                              {step.content}
                              {step.status === 'running' && currentStep === step.id && (
                                <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
                              )}
                            </code>
                          </pre>
                        </div>
                      ) : step.type === 'result' && step.content.includes('http') ? (
                        <div className="space-y-2 max-w-full">
                          {step.content.split('\n').map((line, idx) => {
                            if (line.startsWith('[') && line.includes('](')) {
                              // Handle markdown links
                              const match = line.match(/\[([^\]]+)\]\(([^)]+)\)/);
                              if (match) {
                                return (
                                  <div key={idx} className="force-wrap">
                                    <div className="font-medium text-xs mb-1 force-wrap">{match[1]}</div>
                                    <div className="text-xs text-muted-foreground font-mono bg-muted/50 px-2 py-1 rounded force-wrap">
                                      {match[2]}
                                    </div>
                                  </div>
                                );
                              }
                            }
                            return line.trim() ? (
                              <div key={idx} className="text-xs leading-relaxed force-wrap">
                                {line}
                              </div>
                            ) : (
                              <div key={idx} className="h-2" />
                            );
                          })}
                          {step.status === 'running' && currentStep === step.id && (
                            <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
                          )}
                        </div>
                      ) : (
                        <div className="text-xs leading-relaxed whitespace-pre-wrap force-wrap">
                          {step.content}
                          {step.status === 'running' && currentStep === step.id && (
                            <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Progress Line */}
                  {index < steps.length - 1 && (
                    <div className="ml-4 mt-4 w-px h-6 bg-gradient-to-b from-border to-transparent" />
                  )}
                </div>
              ))}

              {/* Loading indicator for next step */}
              {currentStep && (
                <div className="flex items-center gap-3 text-muted-foreground animate-pulse">
                  <div className="w-8 h-8 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center">
                    <Clock className="w-4 h-4" />
                  </div>
                  <span className="text-sm">Processing next step...</span>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={bottomRef} className="h-1" />
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
} 