import { useEffect, useRef } from 'react';
import type { Message } from '../types/message';
import '../styles/message-list.css';

export default function MessageList({ messages }: { messages: Message[] }) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom whenever messages change
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="message-list" ref={listRef}>
      {messages.map((m) => (
        <div key={m.id} className="message-item">
          <div className="message-meta">
            <strong>{m.username}</strong> · <span>{new Date(m.timestamp).toLocaleTimeString()}</span>
          </div>
          <div className="message-content">{m.content}</div>
        </div>
      ))}
    </div>
  );
}