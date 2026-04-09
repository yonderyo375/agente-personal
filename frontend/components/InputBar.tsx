"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { uploadFile } from "@/lib/api";

interface Props {
  onSend: (text: string, file?: File) => void;
  isLoading: boolean;
  userId: string;
}

export function InputBar({ onSend, isLoading, userId }: Props) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if ((!text.trim() && !file) || isLoading) return;
    onSend(text, file || undefined);
    setText("");
    setFile(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setUploading(true);
    try {
      await uploadFile(f, userId);
      setText(prev => prev + ` [Archivo: ${f.name}]`);
    } finally {
      setUploading(false);
    }
  };

  const handleInput = () => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
    }
  };

  return (
    <div className="px-4 pb-4 pt-2">
      {/* File preview */}
      {file && (
        <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl text-xs text-[#888]">
          <span>📎 {file.name}</span>
          <button onClick={() => setFile(null)} className="ml-auto hover:text-white">✕</button>
        </div>
      )}

      <div className="flex items-end gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl px-3 py-2 focus-within:border-[#7c6aff]/60 transition-colors">
        {/* File button */}
        <button
          onClick={() => fileRef.current?.click()}
          className="p-1.5 text-[#888] hover:text-[#7c6aff] transition-colors shrink-0 mb-0.5"
          title="Adjuntar archivo"
        >
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
          </svg>
        </button>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept=".txt,.pdf,.py,.js,.json,.csv,.md,.html,.css"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKey}
          placeholder="Escribe un mensaje..."
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-sm text-[#e8e8e8] placeholder-[#555] py-1 max-h-40"
          disabled={isLoading || uploading}
        />

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={isLoading || uploading || (!text.trim() && !file)}
          className="p-1.5 rounded-lg bg-[#7c6aff] hover:bg-[#6b5aee] disabled:opacity-30 disabled:cursor-not-allowed transition-colors shrink-0 mb-0.5"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <svg width="16" height="16" fill="none" stroke="white" strokeWidth="2.5" viewBox="0 0 24 24">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22,2 15,22 11,13 2,9"/>
            </svg>
          )}
        </button>
      </div>

      <p className="text-center text-[10px] text-[#444] mt-2">
        Enter para enviar · Shift+Enter para nueva línea
      </p>
    </div>
  );
}
