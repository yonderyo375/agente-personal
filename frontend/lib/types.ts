export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: Date;
  streaming?: boolean;
  file?: { name: string; id: string };
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  updated_at: string;
}
