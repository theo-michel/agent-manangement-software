"use client"

import { useState, useEffect } from "react";
import { ChevronRight } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

interface DocContentProps {
  path: string;
  searchQuery?: string;
}

const getDocContent = (path: string): { title: string; content: string } => {
  const docs: Record<string, { title: string; content: string }> = {
    "/docs/getting-started/introduction": {
      title: "Introduction",
      content: `
# Introduction

Welcome to the documentation explorer for GitHub repositories. This tool helps you browse, search, and understand code repositories more efficiently.

## Features

- **Repository Navigation**: Browse through the directory structure
- **Documentation Viewer**: Read formatted documentation
- **AI Chat Assistant**: Ask questions about the codebase
- **Advanced Search**: Find code and documentation quickly

## Getting Started

To begin exploring a repository, you can:

1. Use the sidebar navigation to browse files and folders
2. Search for specific terms using the search bar
3. Ask questions to the AI assistant at the bottom of the screen

The documentation is generated automatically from the repository contents, including README files, code comments, and other documentation formats.

\`\`\`typescript
// Example usage of the Documentation Explorer API
import { DocumentationExplorer } from '@docu-flow/core';

const explorer = new DocumentationExplorer({
  repository: 'https://github.com/user/repo',
  options: {
    generateDocs: true,
    aiAssistEnabled: true,
  }
});

await explorer.initialize();
\`\`\`

Our goal is to make codebases more accessible and understandable for everyone on your team.
      `
    },
    "/docs/getting-started/installation": {
      title: "Installation",
      content: `
# Installation

Setting up the Documentation Explorer is quick and straightforward.

## Prerequisites

- Node.js 16.0 or higher
- A GitHub account with access to the repositories you want to explore

## Install via npm

\`\`\`bash
npm install @docu-flow/explorer
\`\`\`

## Install via yarn

\`\`\`bash
yarn add @docu-flow/explorer
\`\`\`

## Configuration

Create a configuration file named \`docu-flow.config.js\` in your project root:

\`\`\`javascript
// docu-flow.config.js
module.exports = {
  repositories: [
    {
      name: 'My Repository',
      url: 'https://github.com/username/repository',
      branch: 'main',
      accessToken: process.env.GITHUB_TOKEN // Optional
    }
  ],
  output: {
    path: './docs',
    format: 'markdown'
  },
  features: {
    aiAssistant: true,
    codeHighlighting: true,
    searchIndex: true
  }
}
\`\`\`

## Environment Variables

Create a \`.env\` file with the following variables:

\`\`\`
GITHUB_TOKEN=your_personal_access_token
AI_API_KEY=your_api_key_for_assistant
\`\`\`

Now you're ready to start exploring your repositories with enhanced documentation!
      `
    },
    "/docs/components/button": {
      title: "Button Component",
      content: `
# Button Component

The Button component is a versatile UI element used for triggering actions.

## Import

\`\`\`tsx
import { Button } from '@docu-flow/ui';
\`\`\`

## Usage

\`\`\`tsx
import React from 'react';
import { Button } from '@docu-flow/ui';

function MyComponent() {
  return (
    <div>
      <Button variant="primary">Click Me</Button>
      <Button variant="secondary" disabled>Disabled</Button>
      <Button variant="outline" size="sm">Small Outline</Button>
    </div>
  );
}
\`\`\`

## Props

| Name | Type | Default | Description |
|------|------|---------|-------------|
| variant | 'primary' \| 'secondary' \| 'outline' \| 'ghost' | 'primary' | The visual style of the button |
| size | 'sm' \| 'md' \| 'lg' | 'md' | The size of the button |
| disabled | boolean | false | Whether the button is disabled |
| isLoading | boolean | false | Shows a loading indicator |
| leftIcon | ReactNode | undefined | Icon to display before button text |
| rightIcon | ReactNode | undefined | Icon to display after button text |
| onClick | () => void | undefined | Function called when button is clicked |
| className | string | undefined | Additional CSS classes |

## Examples

### Primary Button

\`\`\`tsx
<Button variant="primary">Primary Button</Button>
\`\`\`

### Button with Icon

\`\`\`tsx
import { ArrowRight } from 'lucide-react';

<Button rightIcon={<ArrowRight />}>Next Step</Button>
\`\`\`

### Loading State

\`\`\`tsx
<Button isLoading>Processing...</Button>
\`\`\`
      `
    },
    "default": {
      title: "Documentation",
      content: `
# Documentation

Select a topic from the sidebar to view related documentation.

## Available Sections

- Getting Started
- Components
- API Reference
- Examples

Click on any item in the navigation tree to explore the documentation.
      `
    }
  };

  return docs[path] || docs["default"];
};

export function DocContent({ path, searchQuery = "" }: DocContentProps) {
  const [doc, setDoc] = useState<{ title: string; content: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      setDoc(getDocContent(path));
      setLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [path]);

  const highlightSearch = (content: string, query: string) => {
    if (!query) return content;

    const parts = content.split(/(`{3}[\s\S]*?`{3})/g);

    return parts.map((part, index) => {
      if (part.startsWith("```") && part.endsWith("```")) {
        return part;
      }

      if (query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return part.replace(regex, '<span class="search-highlight">$1</span>');
      }

      return part;
    }).join('');
  };

  const renderMarkdown = (markdown: string, query: string) => {
    if (query) {
      markdown = highlightSearch(markdown, query);
    }

    const html = markdown
      .replace(/```(.*?)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^\* (.*$)/gm, '<li>$1</li>')
      .replace(/^\- (.*$)/gm, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

    return html;
  };

  if (loading) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <Skeleton className="h-10 w-3/4 mb-6" />
        <Skeleton className="h-6 w-full mb-2" />
        <Skeleton className="h-6 w-5/6 mb-2" />
        <Skeleton className="h-6 w-full mb-6" />

        <Skeleton className="h-8 w-2/3 mb-4" />
        <Skeleton className="h-6 w-full mb-2" />
        <Skeleton className="h-6 w-full mb-2" />
        <Skeleton className="h-6 w-4/5 mb-6" />

        <Skeleton className="h-32 w-full mb-6" />

        <Skeleton className="h-8 w-2/3 mb-4" />
        <Skeleton className="h-6 w-full mb-2" />
        <Skeleton className="h-6 w-3/4 mb-2" />
      </div>
    );
  }

  if (!doc) {
    return <div className="p-6">Document not found</div>;
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-6 max-w-3xl mx-auto">
        <div className="flex items-center text-sm text-muted-foreground mb-2">
          <span>Documentation</span>
          <ChevronRight className="mx-1 h-4 w-4" />
          <span>{path.split('/').filter(Boolean).join(' / ')}</span>
        </div>
        <div className="markdown-content">
          <div dangerouslySetInnerHTML={{
            __html: renderMarkdown(doc.content, searchQuery)
          }} />
        </div>
      </div>
    </ScrollArea>
  );
}
