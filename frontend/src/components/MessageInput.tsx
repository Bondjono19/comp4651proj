import React, { useState } from 'react';
import '../styles/message-input.css';

export default function MessageInput({ onSend }: { onSend: (text: string) => void }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = value.trim();
    if (!t) return;
    onSend(t);
    setValue('');
  }

  // fixed to the bottom of the viewport so it's always visible
  return (
    <form onSubmit={handleSubmit} className="message-input-form">
      <input
        className="message-input-field"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type a message..."
      />
      <button type="submit" className="message-input-button">Send</button>
    </form>
  );
}