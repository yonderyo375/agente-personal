const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SendMessageParams {
  message: string;
  userId: string;
  conversationId: string;
  onChunk: (chunk: string) => void;
  onDone: () => void;
}

export async function sendMessage({
  message, userId, conversationId, onChunk, onDone
}: SendMessageParams) {
  const resp = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      user_id: userId,
      conversation_id: conversationId,
      stream: true,
    }),
  });

  if (!resp.ok) throw new Error(`API error: ${resp.status}`);

  const reader = resp.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) throw new Error("No stream");

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split("\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") { onDone(); return; }
        try {
          const parsed = JSON.parse(data);
          if (parsed.chunk) onChunk(parsed.chunk);
        } catch {}
      }
    }
  }
  onDone();
}

export async function getConversations(userId: string) {
  try {
    const resp = await fetch(`${API_URL}/conversations/${userId}`);
    const data = await resp.json();
    return data.conversations || [];
  } catch { return []; }
}

export async function getMessages(userId: string, conversationId: string) {
  try {
    const resp = await fetch(`${API_URL}/conversations/${userId}/${conversationId}/messages`);
    const data = await resp.json();
    return data.messages || [];
  } catch { return []; }
}

export async function uploadFile(file: File, userId: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("user_id", userId);
  const resp = await fetch(`${API_URL}/upload`, { method: "POST", body: form });
  return await resp.json();
}

export async function getTools() {
  try {
    const resp = await fetch(`${API_URL}/tools`);
    const data = await resp.json();
    return data.tools || [];
  } catch { return []; }
}
