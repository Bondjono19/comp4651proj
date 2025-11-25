import { useEffect, useMemo, useState } from 'react';
import ChatService from '../services/chatService';
import type { Message } from '../types/message';

export function useChat(username: string, roomId: string = 'general') {
  const service = useMemo(() => new ChatService(), []);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    service.connect(username, roomId);
    const unsub = service.onMessage((m) => setMessages((s) => [...s, m]));
    return () => {
      unsub();
      service.close();
    };
  }, [service, username, roomId]);

  const send = (content: string) => service.sendMessage(content);

  return { messages, send };
}