import { useEffect, useMemo, useState } from 'react';
import ChatService from '../services/chatService';
import type { Message } from '../types/message';

const WS_URL = (import.meta.env.VITE_WS_URL as string) || 'ws://localhost:4000';

export function useChat() {
  const service = useMemo(() => new ChatService(WS_URL), []);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    service.connect();
    const unsub = service.onMessage((m) => setMessages((s) => [...s, m]));
    return () => {
      unsub();
      service.close();
    };
  }, [service]);

  const send = (m: Message) => service.sendMessage(m);

  return { messages, send };
}