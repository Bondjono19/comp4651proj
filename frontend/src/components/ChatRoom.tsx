import React, { useEffect, useRef, useState } from 'react';
import ChatService from '../services/chatService';
import type { Message } from '../types/message';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import '../styles/chatroom.css';

const WS_URL = (import.meta.env.VITE_WS_URL as string) || 'ws://localhost:4000';

export default function ChatRoom({ user = 'guest' }: { user?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const serviceRef = useRef<ChatService | null>(null);

  useEffect(() => {
    const service = new ChatService(WS_URL);
    serviceRef.current = service;
    service.connect(user, 'general'); // Join 'general' room by default
    const unsub = service.onMessage((m) => {
      setMessages((s) => [...s, m]);
    });
    return () => {
      unsub();
      service.close();
    };
  }, [user]);

  const send = (text: string) => {
    const m: Message = { id: Date.now().toString() + Math.random().toString(36).slice(2, 8), username: user, content: text, timestamp: Date.now() };
    setMessages((s) => [...s, m]);
    serviceRef.current?.sendMessage(m);
  };

  return (
    // allow ChatRoom to grow to fill the available viewport space provided by App
    <div className="chatroom">
      <MessageList messages={messages} />
      <MessageInput onSend={send} />
    </div>
  );
}