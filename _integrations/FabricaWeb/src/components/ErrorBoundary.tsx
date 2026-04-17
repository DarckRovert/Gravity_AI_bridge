"use client";

import React, { Component, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    name?: string;
}

interface State {
    hasError: boolean;
    error?: Error;
}

/**
 * 🛡️ Granular Error Boundary
 *
 * Wraps individual sections (e.g. Chatbot, Dashboard tabs) so that
 * a crash in one component does NOT bring down the entire page.
 *
 * Usage:
 *   <ErrorBoundary name="Chatbot">
 *     <Chatbot />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        // Silent in production, verbose in dev
        if (process.env.NODE_ENV === 'development') {
            console.error(`[ErrorBoundary:${this.props.name ?? 'unknown'}]`, error, info);
        }
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) return this.props.fallback;

            return (
                <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-center my-4">
                    <span className="text-4xl block mb-3">⚠️</span>
                    <p className="text-red-700 font-bold">Ocurrió un error en {this.props.name ?? 'este componente'}.</p>
                    <p className="text-red-500 text-sm mt-1">Recarga la página para intentar de nuevo.</p>
                    <button
                        onClick={() => this.setState({ hasError: false })}
                        className="mt-4 text-xs text-red-600 underline hover:text-red-800"
                    >
                        Reintentar
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
