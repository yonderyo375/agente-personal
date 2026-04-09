"use client";

import { Conversation } from "@/lib/types";

interface Props {
  open: boolean;
  conversations: Conversation[];
  currentConvId: string;
  onNewChat: () => void;
  onSelectConv: (conv: Conversation) => void;
  onClose: () => void;
}

export function Sidebar({ open, conversations, currentConvId, onNewChat, onSelectConv, onClose }: Props) {
  return (
    <aside className={`
      fixed md:relative z-20 top-0 left-0 h-full w-72
      bg-[#111] border-r border-[#2a2a2a]
      flex flex-col
      transition-transform duration-300
      ${open ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#7c6aff] to-[#a78bfa] flex items-center justify-center text-xs font-bold">
            N
          </div>
          <span className="font-bold text-sm">Nexus AI</span>
        </div>
        <button onClick={onClose} className="md:hidden p-1.5 text-[#888] hover:text-white">✕</button>
      </div>

      {/* New chat button */}
      <div className="px-3 py-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl border border-[#2a2a2a] hover:bg-[#1a1a1a] hover:border-[#7c6aff]/40 transition-all text-sm text-[#ccc]"
        >
          <span className="text-[#7c6aff] text-lg">+</span>
          Nuevo chat
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1">
        {conversations.length > 0 && (
          <p className="text-[10px] text-[#555] uppercase tracking-wider px-2 py-1">
            Conversaciones
          </p>
        )}
        {conversations.map(conv => (
          <button
            key={conv.id}
            onClick={() => onSelectConv(conv)}
            className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all truncate ${
              conv.id === currentConvId
                ? "bg-[#7c6aff]/20 text-white border border-[#7c6aff]/30"
                : "text-[#888] hover:bg-[#1a1a1a] hover:text-[#ccc]"
            }`}
          >
            💬 {conv.title || "Conversación"}
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[#2a2a2a]">
        <p className="text-[10px] text-[#444] text-center">
          Nexus AI · Powered by Gemini
        </p>
      </div>
    </aside>
  );
}
