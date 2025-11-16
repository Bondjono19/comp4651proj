import type { Message } from '../types/message';
import '../styles/message-list.css';

export default function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className="message-list">
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