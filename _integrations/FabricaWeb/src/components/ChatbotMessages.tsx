"use client";

import React from 'react';
import { Message, ChatOption } from '@/types/chatbot';
import { renderMarkdown } from './ChatbotMarkdown';
import NFTCard from './NFTCard';

interface ChatbotMessagesProps {
    messages: Message[];
    streamingText: string;
    isTyping: boolean;
    typingText: string;
    isAdmin: boolean;
    currentOptions: ChatOption[];
    messagesEndRef: React.RefObject<HTMLDivElement | null>;
    onOptionClick: (opt: ChatOption) => void;
}

/**
 * Renders the chat message list, streaming indicator, typing indicator, and quick-reply options.
 */
export default function ChatbotMessages({
    messages,
    streamingText,
    isTyping,
    typingText,
    isAdmin,
    currentOptions,
    messagesEndRef,
    onOptionClick,
}: ChatbotMessagesProps) {
    return (
        <>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-paper/30">
                {messages.map(msg => {
                    // NFT Card detection
                    if (msg.text.includes("NFT MINTED:")) {
                        const lines = msg.text.split('\n');
                        const id = lines[0]?.split('#')[1] || '000';
                        const label = lines[2]?.split('Item: ')[1] || 'Mystery Cake';
                        return (
                            <div key={msg.id} className="flex justify-start w-full animate-fade-in">
                                <div className="w-full">
                                    <NFTCard id={id} label={label} />
                                </div>
                            </div>
                        );
                    }

                    return (
                        <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] p-3 rounded-2xl text-sm whitespace-pre-wrap ${msg.sender === 'user' ? 'bg-primary text-white rounded-tr-none' : msg.isGodMode ? 'bg-gradient-to-br from-purple-50 to-pink-50 text-primary shadow-md rounded-tl-none border border-purple-200' : 'bg-white text-primary shadow-sm rounded-tl-none border border-primary/10'}`}>
                                {renderMarkdown(msg.text)}
                            </div>
                        </div>
                    );
                })}

                {/* Streaming text */}
                {streamingText && (
                    <div className="flex justify-start">
                        <div className="max-w-[85%] p-3 rounded-2xl rounded-tl-none text-sm whitespace-pre-wrap bg-white text-primary shadow-sm border border-primary/10 animate-pulse" style={{ animationDuration: '2s' }}>
                            {renderMarkdown(streamingText)}
                            <span className="inline-block w-1.5 h-4 bg-primary/40 ml-0.5 animate-pulse rounded-sm" />
                        </div>
                    </div>
                )}

                {/* Typing indicator */}
                {isTyping && !streamingText && (
                    <div className="flex justify-start">
                        <div className={`${isAdmin ? 'bg-gradient-to-r from-purple-100 to-pink-100' : 'bg-white'} p-3 rounded-2xl rounded-tl-none shadow-sm border border-primary/10 text-xs text-gray-500 italic`}>
                            {isAdmin ? '⚡ Procesando...' : typingText}
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Quick-reply options */}
            {currentOptions.length > 0 && (
                <div className="p-2 bg-gray-50 flex flex-wrap gap-2 justify-center border-t border-gray-100 max-h-24 overflow-y-auto">
                    {currentOptions.map((opt, idx) => (
                        <button key={idx} onClick={() => onOptionClick(opt)} className={`${isAdmin ? 'border-purple-400 text-purple-600 hover:bg-purple-500' : 'border-accent text-accent hover:bg-accent'} bg-white border text-xs font-bold px-3 py-1 rounded-full hover:text-white transition`}>
                            {opt.text}
                        </button>
                    ))}
                </div>
            )}
        </>
    );
}
