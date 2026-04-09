"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { Sidebar } from "@/components/Sidebar";
import { sendMessage, getConversations } from "@/lib/api";
import { Message, Conversation } from "@/lib/types";
import { v4 as uuidv4 } from "uuid";

const USER_ID = "user_" + (typeof window !== "undefined"
  ? (localStorage.getItem("uid") || (() => { const id = uuidv4(); localStorage.setItem("uid", id); return id; })())
  : "default");

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConvId, setCurrentConvId] = useState<string>(uuidv4());
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userId] = useState(USER_ID);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    const convs = await getConversations(userId);
    setConversations(convs);
  };

  const handleSend = useCallback(async (text: string, file?: File) => {
    if (!text.trim() && !file) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    const agentMsg: Message = {
      id: uuidv4(),
      role: "agent",
      content: "",
      timestamp: new Date(),
      streaming: true,
    };
    setMessages(prev => [...prev, agentMsg]);

    try {
      await sendMessage({
        message: text,
        userId,
        conversationId: currentConvId,
        onChunk: (chunk: string) => {
          setMessages(prev => prev.map(m =>
            m.id === agentMsg.id ? { ...m, content: m.content + chunk } : m
          ));
        },
        onDone: () => {
          setMessages(prev => prev.map(m =>
            m.id === agentMsg.id ? { ...m, streaming: false } : m
          ));
          loadConversations();
        }
      });
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === agentMsg.id
          ? { ...m, content: "❌ Error conectando con el agente. Revisa la conexión.", streaming: false }
          : m
      ));
    } finally {
      setIsLoading(false);
    }
  }, [userId, currentConvId]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentConvId(uuidv4());
    setSidebarOpen(false);
  };

  const handleSelectConversation = (conv: Conversation) => {
    setCurrentConvId(conv.id);
    setSidebarOpen(false);
    // Cargar mensajes de esa conversación
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-[#0f0f0f]">
      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen}
        conversations={conversations}
        currentConvId={currentConvId}
        onNewChat={handleNewChat}
        onSelectConv={handleSelectConversation}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main chat */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-[#2a2a2a] bg-[#0f0f0f]">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-[#1a1a1a] transition-colors text-[#888]"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#7c6aff] to-[#a78bfa] flex items-center justify-center text-xs font-bold">
              N
            </div>
            <span className="font-semibold text-sm">Nexus AI</span>
          </div>

          <div className="ml-auto flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
            <span className="text-xs text-[#888]">En línea</span>
          </div>
        </header>

        {/* Chat */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={handleSend}
          userId={userId}
          conversationId={currentConvId}
        />
      </div>

      {/* Overlay sidebar en móvil */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-10 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
