"use client";

import React from 'react';

/**
 * Parses simple markdown: **bold** and [links](url)
 * Returns an array of React nodes for inline rendering.
 */
export function renderMarkdown(text: string): (string | React.ReactNode)[] {
    const segments: (string | React.ReactNode)[] = [];
    let lastIndex = 0;
    let keyIdx = 0;

    const combinedRegex = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*/g;
    let match;

    while ((match = combinedRegex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            segments.push(text.slice(lastIndex, match.index));
        }

        if (match[1] && match[2]) {
            segments.push(
                <a key={`link-${keyIdx++}`} href={match[2]} target="_blank" rel="noopener noreferrer"
                    className="text-accent underline hover:text-primary font-medium">
                    {match[1]}
                </a>
            );
        } else if (match[3]) {
            segments.push(<strong key={`bold-${keyIdx++}`} className="font-bold">{match[3]}</strong>);
        }

        lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
        segments.push(text.slice(lastIndex));
    }

    return segments;
}
