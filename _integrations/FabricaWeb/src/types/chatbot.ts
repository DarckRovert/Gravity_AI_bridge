export interface ChatOption {
    text: string;
    next?: string;
    action?: string;
}

export interface Message {
    id: string;
    text: string;
    sender: 'bot' | 'user';
    isGodMode?: boolean;
}
