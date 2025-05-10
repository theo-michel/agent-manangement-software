"use client"

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SidebarNavigation } from "@/components/layout/SidebarNavigation";
import { DocContent } from "@/components/docs/DocContent";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { IndexationStatus } from "@/components/indexation/IndexationStatus";
import { convertKBToMB, estimateIndexingPrice } from "@/lib/utils";

export default function RepoDocsPage() {
    const { owner, repo } = useParams();
    const [docData, setDocData] = useState(null);
    const [isIndexed, setIsIndexed] = useState(false);
    const [status, setStatus] = useState<any>(null);
    const [repoInfo, setRepoInfo] = useState<any>(null);

    useEffect(() => {
        fetch(`http://localhost:8000/repos/${owner}/${repo}/status`)
            .then(res => res.json())
            .then(data => {
                setStatus(data);
                setIsIndexed(data.status === "indexed");
            });

        fetch(`http://localhost:8000/repos/${owner}/${repo}/info`)
            .then(res => res.json())
            .then(setRepoInfo);

        if (isIndexed) {
            fetch(`http://localhost:8000/repos/${owner}/${repo}/docs`)
                .then(res => res.json())
                .then(setDocData);
        }
    }, [owner, repo, isIndexed]);

    // Calculate repo size in MB and price
    const repoSizeMB = repoInfo?.size ? convertKBToMB(repoInfo.size) : 0;
    const fileCount = status?.file_count ?? 0;
    const price = estimateIndexingPrice(fileCount, 0.00005, 10, repoSizeMB, 500);

    if (!isIndexed) {
        return (
            <IndexationStatus
                repoName={`${owner}/${repo}`}
                repoSize={repoSizeMB.toString()}
                price={price === "too_large" ? "Too large" : `$${price}`}
                estimatedTime={"10"}
                indexedCount={fileCount}
                onIndexingComplete={() => { }}
            />
        );
    }

    return (
        <div className="flex h-screen">
            <SidebarNavigation onSelectItem={() => { }} />
            <main className="flex-1">
                <DocContent path="" />
                <ChatInterface />
            </main>
        </div>
    );
}

