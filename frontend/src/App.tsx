import { AlertTriangle, CheckCircle2, FileText, Send, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getHealth } from "./api/health";
import type { HealthResponse } from "./types/health";
import "./styles.css";

type ConnectionState = "checking" | "connected" | "unavailable";

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  body: string;
}

const initialMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    body: "Ready.",
  },
];

function App() {
  const [connectionState, setConnectionState] = useState<ConnectionState>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    let active = true;

    getHealth()
      .then((response) => {
        if (!active) return;
        setHealth(response);
        setConnectionState("connected");
      })
      .catch(() => {
        if (!active) return;
        setConnectionState("unavailable");
      });

    return () => {
      active = false;
    };
  }, []);

  const connectionLabel = useMemo(() => {
    if (connectionState === "connected") return "Backend connected";
    if (connectionState === "unavailable") return "Backend unavailable";
    return "Checking backend";
  }, [connectionState]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const question = draft.trim();
    if (!question) return;

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", body: question },
      {
        id: crypto.randomUUID(),
        role: "assistant",
        body: "Chat service pending.",
      },
    ]);
    setDraft("");
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-label="Ctrl-F workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Ctrl-F</p>
            <h1>Company Knowledge</h1>
          </div>
          <div className={`connection connection--${connectionState}`}>
            {connectionState === "connected" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
            <span>{connectionLabel}</span>
          </div>
        </header>

        <div className="content-grid">
          <section className="chat-panel" aria-label="Chat">
            <div className="message-list">
              {messages.map((message) => (
                <article className={`message message--${message.role}`} key={message.id}>
                  <span>{message.role === "assistant" ? "Ctrl-F" : "You"}</span>
                  <p>{message.body}</p>
                </article>
              ))}
            </div>

            <form className="composer" onSubmit={handleSubmit}>
              <label className="sr-only" htmlFor="question">
                Question
              </label>
              <input
                id="question"
                type="text"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask a company question"
              />
              <button type="submit" aria-label="Send question">
                <Send size={18} />
              </button>
            </form>
          </section>

          <aside className="context-panel" aria-label="Answer context">
            <section>
              <div className="panel-heading">
                <ShieldCheck size={18} />
                <h2>Status</h2>
              </div>
              <dl className="metadata-list">
                <div>
                  <dt>API</dt>
                  <dd>{health?.app_name ?? "Pending"}</dd>
                </div>
                <div>
                  <dt>Version</dt>
                  <dd>{health?.version ?? "-"}</dd>
                </div>
                <div>
                  <dt>Environment</dt>
                  <dd>{health?.environment ?? "-"}</dd>
                </div>
              </dl>
            </section>

            <section>
              <div className="panel-heading">
                <FileText size={18} />
                <h2>Sources</h2>
              </div>
              <p className="empty-state">No sources attached.</p>
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}

export default App;

