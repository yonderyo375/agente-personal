"use client";

import { useEffect, useRef, useState } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";

interface Props {
  messages: Message[];
  isLoading: boolean;
  onSend: (text: string, file?: File) => void;
  userId: string;
  conversationId: string;
}

export function ChatWindow({ messages, isLoading, onSend, userId, conversationId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-2">
        {messages.length === 0 && (
          <WelcomeScreen onSend={onSend} />
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && messages[messages.length - 1]?.streaming === false && (
          <div className="flex gap-3 items-start fade-up">
            <AgentAvatar />
            <div className="flex gap-1 items-center pt-3">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-[#7c6aff] animate-pulse"
                  style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <InputBar onSend={onSend} isLoading={isLoading} userId={userId} />
    </div>
  );
}

function AgentAvatar() {
  return (
    <div className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-[#7c6aff] to-[#a78bfa] flex items-center justify-center text-xs font-bold mt-1">
      N
    </div>
  );
}

function WelcomeScreen({ onSend }: { onSend: (t: string) => void }) {
  const suggestions = [
    "¿Qué puedes hacer?",
    "Escribe un script en Python para descargar imágenes",
    "Busca las últimas noticias de IA",
    "Calcula 15% de propina para $47.50",
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-6 text-center px-4">
      <div>
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#7c6aff] to-[#a78bfa] flex items-center justify-center text-2xl font-bold mx-auto mb-4">
          N
        </div>
        <h1 className="text-2xl font-bold mb-2">Nexus AI</h1>
        <p className="text-[#888] text-sm max-w-sm">
          Tu agente autónomo. Puedo buscar en la web, ejecutar código, analizar archivos y mucho más.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSend(s)}
            className="text-left px-4 py-3 rounded-xl border border-[#2a2a2a] bg-[#1a1a1a] hover:bg-[#242424] hover:border-[#7c6aff]/40 transition-all text-sm text-[#ccc]"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
