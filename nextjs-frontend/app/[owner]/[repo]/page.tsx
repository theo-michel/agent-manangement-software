"use client"

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SidebarNavigation } from "@/components/layout/SidebarNavigation";
import { DocContent } from "@/components/docs/DocContent";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { IndexationStatus } from "@/components/indexation/IndexationStatus";
import { convertKBToMB, estimateIndexingPrice } from "@/lib/utils";
import type { RepositoryInfo } from "@/app/openapi-client/types.gen";
import { getRepositoryStatus, getRepositoryDocs, getGithubRepoInfo } from "@/app/openapi-client/sdk.gen";
import type { RepositoryStatusResponse, DocsResponse } from "@/app/openapi-client/types.gen";

export default function RepoDocsPage() {
    const { owner, repo } = useParams();
    const [docData, setDocData] = useState<DocsResponse | null>(null);
    const [isIndexed, setIsIndexed] = useState(false);
    const [status, setStatus] = useState<RepositoryStatusResponse | null>(null);
    const [repoInfo, setRepoInfo] = useState<RepositoryInfo | null>(null);

    useEffect(() => {
        getRepositoryStatus({
            path: { owner: owner as string, repo: repo as string }
        }).then(response => {
            if ('data' in response && response.data) {
                setStatus(response.data);
                setIsIndexed(response.data.status === "indexed");
            }
        });

        getGithubRepoInfo({
            path: { owner: owner as string, repo: repo as string }
        }).then(response => {
            if ('data' in response && response.data) {
                setRepoInfo(response.data as RepositoryInfo);
            }
        });

        if (isIndexed) {
            getRepositoryDocs({
                path: { owner: owner as string, repo: repo as string }
            }).then(response => {
                if ('data' in response && response.data) {
                    setDocData(response.data);
                }
            });
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

