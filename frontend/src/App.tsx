import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileText,
  LogOut,
  Plus,
  RefreshCw,
  Send,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getCurrentUser, login } from "./api/auth";
import { sendChatMessage } from "./api/chat";
import { getFeedback, getFeedbackStats, submitFeedback } from "./api/feedback";
import { getHealth } from "./api/health";
import { createSource, getSources, indexSource } from "./api/sources";
import type { UserProfile } from "./types/auth";
import type { ChatSource } from "./types/chat";
import type { FeedbackRating, FeedbackRecord, FeedbackStats } from "./types/feedback";
import type { HealthResponse } from "./types/health";
import type { SourceCreatePayload, SourceRecord } from "./types/source";
import "./styles.css";

type ConnectionState = "checking" | "connected" | "unavailable";
type MessageStatus = "normal" | "warning" | "error";

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  body: string;
  messageId?: string;
  question?: string;
  confidence?: number;
  warning?: string | null;
  sources?: ChatSource[];
  contacts?: string[];
  status?: MessageStatus;
  feedbackRating?: FeedbackRating;
}

const demoUsers = [
  { email: "employee@example.com", label: "Employee" },
  { email: "intern@example.com", label: "Intern" },
  { email: "manager@example.com", label: "Manager" },
  { email: "hr@example.com", label: "HR" },
  { email: "admin@example.com", label: "Admin" },
];

const initialMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    body: "Ask a question after signing in.",
  },
];

const initialSourceForm: SourceCreatePayload = {
  title: "Vacation Policy",
  description: "Approved HR policy for paid time off.",
  source_type: "document",
  location: "data/approved_sources/hr/vacation.md",
  owning_department: "Human Resources",
  allowed_roles: ["employee", "manager", "hr", "admin"],
  allowed_departments: [],
  approval_status: "approved",
  version: "2026.1",
};

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function App() {
  const [connectionState, setConnectionState] = useState<ConnectionState>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [token, setToken] = useState<string | null>(() => window.localStorage.getItem("ctrlf_token"));
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loginEmail, setLoginEmail] = useState(demoUsers[0].email);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [feedbackRecords, setFeedbackRecords] = useState<FeedbackRecord[]>([]);
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [sourceRecords, setSourceRecords] = useState<SourceRecord[]>([]);
  const [sourceForm, setSourceForm] = useState<SourceCreatePayload>(initialSourceForm);
  const [sourceStatus, setSourceStatus] = useState<string | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [isSourceSaving, setIsSourceSaving] = useState(false);
  const [indexingSourceId, setIndexingSourceId] = useState<number | null>(null);

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

  useEffect(() => {
    if (!token) return;

    let active = true;
    getCurrentUser(token)
      .then((profile) => {
        if (!active) return;
        setUser(profile);
      })
      .catch(() => {
        if (!active) return;
        clearSession();
      });

    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !user?.permissions.includes("feedback:review")) return;

    refreshFeedbackReview().catch((error) => {
      setFeedbackError(error instanceof Error ? error.message : "Feedback review could not be loaded.");
    });
  }, [token, user]);

  useEffect(() => {
    if (!token || !user?.permissions.includes("sources:manage")) return;

    refreshSourceRegistry().catch((error) => {
      setSourceError(error instanceof Error ? error.message : "Source registry could not be loaded.");
    });
  }, [token, user]);

  const latestAssistantSources = useMemo(() => {
    return [...messages].reverse().find((message) => message.sources?.length)?.sources ?? [];
  }, [messages]);

  const latestConfidence = useMemo(() => {
    return [...messages].reverse().find((message) => message.confidence !== undefined)?.confidence;
  }, [messages]);

  const connectionLabel = useMemo(() => {
    if (connectionState === "connected") return "Backend connected";
    if (connectionState === "unavailable") return "Backend unavailable";
    return "Checking backend";
  }, [connectionState]);

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoggingIn(true);
    setLoginError(null);

    try {
      const response = await login(loginEmail, "demo");
      window.localStorage.setItem("ctrlf_token", response.access_token);
      setToken(response.access_token);
      setUser(response.user);
      setMessages(initialMessages);
      setConversationId(null);
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const question = draft.trim();
    if (!question || !token || isSending) return;

    setDraft("");
    setIsSending(true);
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", body: question }]);

    try {
      const response = await sendChatMessage(token, question, conversationId);
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          messageId: response.message_id,
          question,
          body: response.answer,
          confidence: response.confidence,
          warning: response.warning,
          sources: response.sources,
          contacts: response.suggested_contacts,
          status: response.warning ? "warning" : "normal",
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          body: error instanceof Error ? error.message : "Chat request failed.",
          status: "error",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  async function handleFeedback(message: ChatMessage, rating: FeedbackRating) {
    if (!token || !message.messageId || !message.question || message.confidence === undefined) return;

    setFeedbackError(null);
    try {
      await submitFeedback(token, {
        message_id: message.messageId,
        rating,
        question: message.question,
        answer: message.body,
        confidence: message.confidence,
        sources: message.sources ?? [],
        comment: null,
      });
      setMessages((current) =>
        current.map((item) => (item.id === message.id ? { ...item, feedbackRating: rating } : item)),
      );
      if (user?.permissions.includes("feedback:review")) {
        await refreshFeedbackReview(token);
      }
    } catch (error) {
      setFeedbackError(error instanceof Error ? error.message : "Feedback could not be saved.");
    }
  }

  async function refreshFeedbackReview(activeToken = token) {
    if (!activeToken || !user?.permissions.includes("feedback:review")) return;

    const [records, stats] = await Promise.all([getFeedback(activeToken), getFeedbackStats(activeToken)]);
    setFeedbackRecords(records);
    setFeedbackStats(stats);
  }

  async function refreshSourceRegistry(activeToken = token) {
    if (!activeToken || !user?.permissions.includes("sources:manage")) return;

    const sources = await getSources(activeToken);
    setSourceRecords(sources);
  }

  async function handleSourceSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || isSourceSaving) return;

    setIsSourceSaving(true);
    setSourceError(null);
    setSourceStatus(null);

    try {
      const created = await createSource(token, sourceForm);
      setSourceStatus(`Added ${created.title}.`);
      await refreshSourceRegistry(token);
    } catch (error) {
      setSourceError(error instanceof Error ? error.message : "Source could not be saved.");
    } finally {
      setIsSourceSaving(false);
    }
  }

  async function handleIndexSource(source: SourceRecord) {
    if (!token || indexingSourceId !== null) return;

    setIndexingSourceId(source.id);
    setSourceError(null);
    setSourceStatus(null);

    try {
      const result = await indexSource(token, source.id);
      setSourceStatus(`Indexed ${result.chunk_count} chunk${result.chunk_count === 1 ? "" : "s"} from ${source.title}.`);
      await refreshSourceRegistry(token);
    } catch (error) {
      setSourceError(error instanceof Error ? error.message : "Source could not be indexed.");
    } finally {
      setIndexingSourceId(null);
    }
  }

  function clearSession() {
    window.localStorage.removeItem("ctrlf_token");
    setToken(null);
    setUser(null);
    setConversationId(null);
    setMessages(initialMessages);
    setFeedbackRecords([]);
    setFeedbackStats(null);
    setFeedbackError(null);
    setSourceRecords([]);
    setSourceStatus(null);
    setSourceError(null);
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

        {!user ? (
          <section className="login-panel" aria-label="Login">
            <div>
              <p className="eyebrow">Demo Access</p>
              <h2>Sign in</h2>
            </div>
            <form className="login-form" onSubmit={handleLogin}>
              <label htmlFor="demo-user">User</label>
              <select id="demo-user" value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)}>
                {demoUsers.map((demoUser) => (
                  <option key={demoUser.email} value={demoUser.email}>
                    {demoUser.label} - {demoUser.email}
                  </option>
                ))}
              </select>
              <button type="submit" disabled={isLoggingIn || connectionState !== "connected"}>
                <UserRound size={18} />
                <span>{isLoggingIn ? "Signing in" : "Sign in"}</span>
              </button>
              {loginError ? <p className="form-error">{loginError}</p> : null}
            </form>
          </section>
        ) : (
          <div className="content-grid">
            <section className="chat-panel" aria-label="Chat">
              <div className="message-list">
                {messages.map((message) => (
                  <article className={`message message--${message.role} message--${message.status ?? "normal"}`} key={message.id}>
                    <span>{message.role === "assistant" ? "Ctrl-F" : "You"}</span>
                    <p>{message.body}</p>
                    {message.confidence !== undefined ? (
                      <p className="message-meta">Confidence {Math.round(message.confidence * 100)}%</p>
                    ) : null}
                    {message.warning ? <p className="message-warning">{message.warning}</p> : null}
                    {message.contacts?.length ? (
                      <p className="message-meta">Contacts: {message.contacts.join(", ")}</p>
                    ) : null}
                    {message.role === "assistant" && message.messageId ? (
                      <div className="feedback-controls" aria-label="Answer feedback">
                        <button
                          type="button"
                          onClick={() => handleFeedback(message, "helpful")}
                          disabled={message.feedbackRating !== undefined}
                          aria-label="Mark answer helpful"
                        >
                          <ThumbsUp size={15} />
                          <span>Helpful</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFeedback(message, "not_helpful")}
                          disabled={message.feedbackRating !== undefined}
                          aria-label="Mark answer not helpful"
                        >
                          <ThumbsDown size={15} />
                          <span>Not helpful</span>
                        </button>
                        {message.feedbackRating ? <span>Recorded: {message.feedbackRating.replace("_", " ")}</span> : null}
                      </div>
                    ) : null}
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
                  disabled={isSending}
                />
                <button type="submit" aria-label="Send question" disabled={isSending || !draft.trim()}>
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
                    <dt>User</dt>
                    <dd>{user.name}</dd>
                  </div>
                  <div>
                    <dt>Role</dt>
                    <dd>{user.role}</dd>
                  </div>
                  <div>
                    <dt>Dept.</dt>
                    <dd>{user.department}</dd>
                  </div>
                  <div>
                    <dt>API</dt>
                    <dd>{health?.app_name ?? "Pending"}</dd>
                  </div>
                  <div>
                    <dt>Confidence</dt>
                    <dd>{latestConfidence === undefined ? "-" : `${Math.round(latestConfidence * 100)}%`}</dd>
                  </div>
                </dl>
                <button className="secondary-button" type="button" onClick={clearSession}>
                  <LogOut size={16} />
                  <span>Sign out</span>
                </button>
                {feedbackError ? <p className="form-error">{feedbackError}</p> : null}
              </section>

              <section>
                <div className="panel-heading">
                  <FileText size={18} />
                  <h2>Sources</h2>
                </div>
                {latestAssistantSources.length ? (
                  <ol className="source-list">
                    {latestAssistantSources.map((source) => (
                      <li key={`${source.source_id}-${source.location}`}>
                        <a href={source.location} target="_blank" rel="noreferrer">
                          {source.title}
                        </a>
                        <p>{source.excerpt}</p>
                        <span>Score {Math.round(source.score * 100)}%</span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="empty-state">No sources attached.</p>
                )}
              </section>

              {user.permissions.includes("sources:manage") ? (
                <section>
                  <div className="panel-heading">
                    <Database size={18} />
                    <h2>Source Registry</h2>
                  </div>

                  <form className="admin-form" onSubmit={handleSourceSubmit}>
                    <label htmlFor="source-title">Title</label>
                    <input
                      id="source-title"
                      value={sourceForm.title}
                      onChange={(event) => setSourceForm((current) => ({ ...current, title: event.target.value }))}
                    />

                    <label htmlFor="source-location">Location</label>
                    <input
                      id="source-location"
                      value={sourceForm.location}
                      onChange={(event) => setSourceForm((current) => ({ ...current, location: event.target.value }))}
                    />

                    <label htmlFor="source-department">Owner</label>
                    <input
                      id="source-department"
                      value={sourceForm.owning_department}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, owning_department: event.target.value }))
                      }
                    />

                    <label htmlFor="source-roles">Roles</label>
                    <input
                      id="source-roles"
                      value={sourceForm.allowed_roles.join(", ")}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, allowed_roles: splitList(event.target.value) }))
                      }
                    />

                    <label htmlFor="source-status">Status</label>
                    <select
                      id="source-status"
                      value={sourceForm.approval_status}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, approval_status: event.target.value }))
                      }
                    >
                      <option value="approved">approved</option>
                      <option value="draft">draft</option>
                      <option value="archived">archived</option>
                    </select>

                    <div className="action-row">
                      <button type="submit" disabled={isSourceSaving}>
                        <Plus size={15} />
                        <span>{isSourceSaving ? "Adding" : "Add"}</span>
                      </button>
                      <button type="button" onClick={() => refreshSourceRegistry()} disabled={!token}>
                        <RefreshCw size={15} />
                        <span>Refresh</span>
                      </button>
                    </div>
                  </form>

                  {sourceStatus ? <p className="form-success">{sourceStatus}</p> : null}
                  {sourceError ? <p className="form-error">{sourceError}</p> : null}

                  {sourceRecords.length ? (
                    <ol className="source-admin-list">
                      {sourceRecords.slice(0, 5).map((source) => (
                        <li key={source.id}>
                          <div>
                            <strong>{source.title}</strong>
                            <span>{source.approval_status}</span>
                          </div>
                          <p>{source.location}</p>
                          <button
                            type="button"
                            onClick={() => handleIndexSource(source)}
                            disabled={indexingSourceId !== null || source.approval_status !== "approved"}
                          >
                            {indexingSourceId === source.id ? "Indexing" : source.indexed_at ? "Reindex" : "Index"}
                          </button>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="empty-state">No registered sources.</p>
                  )}
                </section>
              ) : null}

              {user.permissions.includes("feedback:review") ? (
                <section>
                  <div className="panel-heading">
                    <ThumbsUp size={18} />
                    <h2>Feedback</h2>
                  </div>
                  {feedbackStats ? (
                    <dl className="metadata-list">
                      <div>
                        <dt>Total</dt>
                        <dd>{feedbackStats.total}</dd>
                      </div>
                      <div>
                        <dt>Helpful</dt>
                        <dd>{feedbackStats.helpful}</dd>
                      </div>
                      <div>
                        <dt>Needs work</dt>
                        <dd>{feedbackStats.not_helpful}</dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="empty-state">No feedback loaded.</p>
                  )}
                  {feedbackRecords.length ? (
                    <ol className="review-list">
                      {feedbackRecords.slice(0, 4).map((record) => (
                        <li key={record.id}>
                          <span>{record.rating.replace("_", " ")}</span>
                          <p>{record.question}</p>
                        </li>
                      ))}
                    </ol>
                  ) : null}
                </section>
              ) : null}
            </aside>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
