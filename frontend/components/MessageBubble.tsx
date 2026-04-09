"use client";

import { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import remarkGfm from "remark-gfm";
import { useState } from "react";

interface Props { message: Message; }

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 items-start fade-up ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-[#7c6aff] to-[#a78bfa] flex items-center justify-center text-xs font-bold mt-1">
          N
        </div>
      )}

      {/* Bubble */}
      <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? "bg-[#7c6aff] text-white rounded-tr-sm"
          : "bg-[#1a1a1a] border border-[#2a2a2a] text-[#e8e8e8] rounded-tl-sm"
      }`}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  const lang = match ? match[1] : "";
                  if (!inline && lang) {
                    return (
                      <CodeBlock code={String(children).replace(/\n$/, "")} language={lang} />
                    );
                  }
                  return <code className={className} {...props}>{children}</code>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
            {message.streaming && (
              <span className="inline-block w-2 h-4 bg-[#7c6aff] cursor ml-0.5 align-middle" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative mt-2 mb-2">
      <div className="flex items-center justify-between bg-[#1e1e2e] px-4 py-2 rounded-t-lg border border-[#2a2a2a]">
        <span className="text-xs text-[#888] font-mono">{language}</span>
        <button
          onClick={copy}
          className="text-xs text-[#888] hover:text-white transition-colors px-2 py-1 rounded hover:bg-[#2a2a2a]"
        >
          {copied ? "✅ Copiado" : "📋 Copiar"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        customStyle={{
          margin: 0,
          borderRadius: "0 0 8px 8px",
          border: "1px solid #2a2a2a",
          borderTop: "none",
          fontSize: "0.82em",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
