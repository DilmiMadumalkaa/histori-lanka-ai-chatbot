import { useEffect, useMemo, useRef, useState } from "react";
import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from "firebase/auth";
import { initializeApp } from "firebase/app";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const STORAGE_KEY = "sl-heritage-chat-sessions";

const styleOptions = ["informative", "concise", "detailed", "academic"];

const GREETING_PATTERN = /^(hi|hello|hey|good morning|good afternoon|good evening)\b[!.?\s]*$/i;

const firebaseConfig = {
  apiKey: "AIzaSyAyjbZwmJPDS1H2u7AhL54V2kn5MbEYfck",
  authDomain: "research-e06e9.firebaseapp.com",
  projectId: "research-e06e9",
  storageBucket: "research-e06e9.firebasestorage.app",
  messagingSenderId: "794277652603",
  appId: "1:794277652603:web:05a272c3a6874e2df4dade",
};

const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);
const googleProvider = new GoogleAuthProvider();

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="9" y="9" width="10" height="10" rx="2" ry="2" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 20h9" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 6L9 17l-5-5" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="send-icon">
      <path d="M3 20L21 12L3 4L3 10L15 12L3 14Z" fill="currentColor" />
    </svg>
  );
}

function BrandLogo() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" className="brand-logo">
      <defs>
        <linearGradient id="hl-ring" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#61d8a6" />
          <stop offset="100%" stopColor="#4fa2ff" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="28" fill="#0f1f34" stroke="url(#hl-ring)" strokeWidth="3" />
      <path d="M18 39h28" stroke="#9cd3ff" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M22 39V25l10-6 10 6v14" fill="none" stroke="#e8f0fa" strokeWidth="2.8" strokeLinejoin="round" />
      <path d="M32 23v16" stroke="#61d8a6" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.5 3.8-5.5 3.8-3.3 0-6-2.8-6-6.2s2.7-6.2 6-6.2c1.9 0 3.1.8 3.9 1.5l2.6-2.5C16.8 3 14.6 2 12 2 6.9 2 2.8 6.2 2.8 11.3S6.9 20.6 12 20.6c6.9 0 9.1-4.9 9.1-7.4 0-.5-.1-.9-.1-1.3H12z"/>
    </svg>
  );
}

function makeId(prefix = "msg") {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createWelcomeMessage() {
  return {
    id: makeId("msg"),
    role: "assistant",
    content: "Welcome to HistoriLanka AI.",
    createdAt: new Date().toISOString(),
  };
}

function getSessionTitle(messages) {
  const firstUser = messages.find((m) => m.role === "user" && m.content?.trim());
  if (!firstUser) {
    return "New chat";
  }
  const title = firstUser.content.trim();
  return title.length > 42 ? `${title.slice(0, 42)}...` : title;
}

function createSession(style = "informative") {
  const now = new Date().toISOString();
  return {
    id: makeId("session"),
    title: "New chat",
    customTitle: false,
    style,
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

function createAssistantMessage(payload) {
  return {
    id: makeId("msg"),
    role: "assistant",
    content: payload.response || "No response text returned.",
    meta: {
      model: payload.model || "N/A",
      quality_score: payload.quality_score ?? "N/A",
      quality_rating: payload.quality_rating || "N/A",
      retrieved_sites_count: payload.retrieved_sites_count ?? "N/A",
      retrieved_sites: Array.isArray(payload.retrieved_sites) ? payload.retrieved_sites : [],
    },
    createdAt: new Date().toISOString(),
  };
}

function hasConversation(session) {
  return Array.isArray(session?.messages)
    && session.messages.some((m) => m.role === "user" && (m.content || "").trim());
}

function formatAuthError(err) {
  const code = err?.code || "";
  if (code.includes("auth/invalid-credential")) {
    return "Invalid email or password.";
  }
  if (code.includes("auth/email-already-in-use")) {
    return "This email is already in use.";
  }
  if (code.includes("auth/weak-password")) {
    return "Password should be at least 6 characters.";
  }
  if (code.includes("auth/popup-closed-by-user")) {
    return "Google sign-in was canceled.";
  }
  if (code.includes("auth/too-many-requests")) {
    return "Too many attempts. Please try again later.";
  }
  return err?.message || "Authentication failed.";
}

function formatSessionTime(iso) {
  if (!iso) {
    return "";
  }
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) {
    return "just now";
  }
  if (diffMin < 60) {
    return `${diffMin}m ago`;
  }
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) {
    return `${diffHr}h ago`;
  }
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) {
    return `${diffDay}d ago`;
  }
  return d.toLocaleDateString();
}

export default function App() {
  const [sessions, setSessions] = useState(() => {
    const fresh = createSession("informative");
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return [fresh];
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length === 0) {
        return [fresh];
      }
      // Always open with a fresh chat while still keeping recent history.
      return [fresh, ...parsed.filter(hasConversation)];
    } catch {
      return [fresh];
    }
  });
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [query, setQuery] = useState("");
  const [style, setStyle] = useState("informative");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState("");
  const [editingMessageId, setEditingMessageId] = useState("");
  const [editingText, setEditingText] = useState("");
  const [openRecentMenuId, setOpenRecentMenuId] = useState("");
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [authMode, setAuthMode] = useState("signin");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [showAuthLogoImage, setShowAuthLogoImage] = useState(true);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const formRef = useRef(null);
  const chatStreamRef = useRef(null);
  const accountMenuRef = useRef(null);

  const activeSession = useMemo(() => {
    if (!sessions.length) {
      return null;
    }
    return sessions.find((s) => s.id === activeSessionId) || sessions[0];
  }, [sessions, activeSessionId]);

  const messages = activeSession?.messages || [];

  const isFreshSession = useMemo(() => {
    if (!messages.length) {
      return true;
    }
    const hasUserMessages = messages.some((m) => m.role === "user");
    if (hasUserMessages) {
      return false;
    }
    return messages.length === 1 && (messages[0].content || "").toLowerCase().includes("welcome");
  }, [messages]);

  const recentSessions = useMemo(
    () => [...sessions].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)),
    [sessions]
  );

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthLoading(false);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (!sessions.length) {
      const fresh = createSession(style);
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      return;
    }
    if (!activeSessionId || !sessions.some((s) => s.id === activeSessionId)) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId, style]);

  useEffect(() => {
    if (activeSession?.style && activeSession.style !== style) {
      setStyle(activeSession.style);
    }
  }, [activeSession, style]);

  useEffect(() => {
    const el = chatStreamRef.current;
    if (!el) {
      return;
    }
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading, activeSessionId]);

  useEffect(() => {
    function handleOutsideClick(event) {
      if (!accountMenuRef.current) {
        return;
      }
      if (!accountMenuRef.current.contains(event.target)) {
        setAccountMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const userEmail = user?.email || "Signed in";
  const userName = (user?.displayName || userEmail.split("@")[0] || "User").trim();
  const userInitials = userName.slice(0, 2).toUpperCase();
  const userPlan = "Free";

  async function handleGoogleLogin() {
    setAuthBusy(true);
    setAuthError("");
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      setAuthError(formatAuthError(err));
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleEmailAuth(e) {
    e.preventDefault();
    if (!authEmail.trim() || !authPassword) {
      setAuthError("Email and password are required.");
      return;
    }

    setAuthBusy(true);
    setAuthError("");
    try {
      if (authMode === "signup") {
        await createUserWithEmailAndPassword(auth, authEmail.trim(), authPassword);
      } else {
        await signInWithEmailAndPassword(auth, authEmail.trim(), authPassword);
      }
      setAuthEmail("");
      setAuthPassword("");
    } catch (err) {
      setAuthError(formatAuthError(err));
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleSignOut() {
    const ok = window.confirm("Are you sure you want to logout?");
    if (!ok) {
      return;
    }

    setError("");
    try {
      await signOut(auth);
    } catch (err) {
      setError(`Sign out failed: ${formatAuthError(err)}`);
    }
  }

  function updateActiveSession(transform) {
    if (!activeSession) {
      return;
    }
    setSessions((prev) =>
      prev.map((session) => {
        if (session.id !== activeSession.id) {
          return session;
        }
        const updated = transform(session);
        return {
          ...updated,
          title: updated.customTitle ? updated.title : getSessionTitle(updated.messages),
          updatedAt: new Date().toISOString(),
        };
      })
    );
  }

  function handleNewChat() {
    const fresh = createSession(style);
    setSessions((prev) => [fresh, ...prev.filter(hasConversation)]);
    setActiveSessionId(fresh.id);
    setOpenRecentMenuId("");
    setQuery("");
    setError("");
  }

  function handleStyleChange(e) {
    const nextStyle = e.target.value;
    setStyle(nextStyle);
    updateActiveSession((session) => ({ ...session, style: nextStyle }));
  }

  function handleRenameSession(sessionId) {
    const target = sessions.find((s) => s.id === sessionId);
    if (!target) {
      return;
    }

    const nextTitle = window.prompt("Enter new session title", target.title || "New chat");
    if (nextTitle === null) {
      return;
    }

    const cleaned = nextTitle.trim();
    if (!cleaned) {
      setError("Session title cannot be empty.");
      return;
    }

    setError("");
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              title: cleaned,
              customTitle: true,
              updatedAt: new Date().toISOString(),
            }
          : session
      )
    );
  }

  function handleDeleteSession(sessionId) {
    const target = sessions.find((s) => s.id === sessionId);
    if (!target) {
      return;
    }

    const ok = window.confirm(`Delete session "${target.title}"?`);
    if (!ok) {
      return;
    }

    const remaining = sessions.filter((s) => s.id !== sessionId);
    if (remaining.length === 0) {
      const fresh = createSession(style);
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      return;
    }

    setSessions(remaining);
    if (activeSessionId === sessionId) {
      setActiveSessionId(remaining[0].id);
    }
    setOpenRecentMenuId("");
  }

  function handleStartEditRequest(message) {
    setEditingMessageId(message.id);
    setEditingText(message.content || "");
  }

  function handleCancelEditRequest() {
    setEditingMessageId("");
    setEditingText("");
  }

  async function handleSendEditedRequest() {
    const cleaned = editingText.trim();
    if (!cleaned) {
      setError("Request text cannot be empty.");
      return;
    }

    setLoading(true);
    setError("");

    updateActiveSession((session) => ({
      ...session,
      messages: (() => {
        const idx = session.messages.findIndex((m) => m.id === editingMessageId);
        if (idx < 0) {
          return session.messages;
        }
        const edited = {
          ...session.messages[idx],
          content: cleaned,
          editedAt: new Date().toISOString(),
        };
        // Keep messages only up to the edited request, then regenerate below it.
        return [...session.messages.slice(0, idx), edited];
      })(),
    }));

    setEditingMessageId("");
    setEditingText("");

    if (GREETING_PATTERN.test(cleaned)) {
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            id: makeId("msg"),
            role: "assistant",
            content: "Hi, how can I help you?",
            createdAt: new Date().toISOString(),
          },
        ],
      }));
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleaned, style }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Failed to get response from API.");
      }

      const payload = await response.json();
      const assistantMessage = createAssistantMessage(payload);
      updateActiveSession((session) => ({
        ...session,
        messages: [...session.messages, assistantMessage],
      }));
    } catch (err) {
      const msg = err.message || "Unexpected error";
      setError(msg);
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            id: makeId("msg"),
            role: "assistant",
            content: `I could not generate a response: ${msg}`,
            meta: {
              model: "error",
              quality_score: "N/A",
              quality_rating: "error",
              retrieved_sites_count: "N/A",
              retrieved_sites: [],
            },
            createdAt: new Date().toISOString(),
          },
        ],
      }));
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyMessage(message) {
    const text = message.content || "";
    if (!text) {
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(message.id);
      window.setTimeout(() => setCopiedMessageId(""), 1200);
    } catch {
      setError("Could not copy message to clipboard.");
    }
  }

  async function askQuestion(e) {
    e.preventDefault();
    const cleaned = query.trim();
    if (!cleaned) {
      setError("Please enter a question.");
      return;
    }

    const userMessage = {
      id: makeId("msg"),
      role: "user",
      content: cleaned,
      createdAt: new Date().toISOString(),
    };

    updateActiveSession((session) => ({
      ...session,
      messages: [...session.messages, userMessage],
    }));
    setQuery("");

    if (GREETING_PATTERN.test(cleaned)) {
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            id: makeId("msg"),
            role: "assistant",
            content: "Hi, how can I help you?",
            createdAt: new Date().toISOString(),
          },
        ],
      }));
      setError("");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleaned, style }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Failed to get response from API.");
      }

      const payload = await response.json();
      const assistantMessage = createAssistantMessage(payload);
      updateActiveSession((session) => ({
        ...session,
        messages: [...session.messages, assistantMessage],
      }));
    } catch (err) {
      const msg = err.message || "Unexpected error";
      setError(msg);
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            id: makeId("msg"),
            role: "assistant",
            content: `I could not generate a response: ${msg}`,
            meta: {
              model: "error",
              quality_score: "N/A",
              quality_rating: "error",
              retrieved_sites_count: "N/A",
              retrieved_sites: [],
            },
            createdAt: new Date().toISOString(),
          },
        ],
      }));
    } finally {
      setLoading(false);
      formRef.current?.querySelector("textarea")?.focus();
    }
  }

  function handleComposerKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading) {
        formRef.current?.requestSubmit();
      }
    }
  }

  if (authLoading) {
    return (
      <div className="auth-shell">
        <div className="auth-card auth-loading">Checking login...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="auth-shell">
        <div className="auth-scene" aria-hidden="true">
          <span className="auth-orb auth-orb-a" />
          <span className="auth-orb auth-orb-b" />
          <span className="auth-grid" />
        </div>

        <div className="auth-card auth-card-creative">
          <div className="auth-popup-top" aria-hidden="true">
            <span className="dot dot-red" />
            <span className="dot dot-amber" />
            <span className="dot dot-green" />
          </div>
          <div className="auth-brand auth-brand-creative">
            <div className="auth-logo-wrap">
              {showAuthLogoImage ? (
                <img
                  src="/historilanka-logo.png"
                  alt="HistoriLanka AI"
                  className="auth-hero-logo"
                  onError={() => setShowAuthLogoImage(false)}
                />
              ) : (
                <BrandLogo />
              )}
            </div>
            <h2>Explore the Ancient Wonders</h2>
            <p className="auth-subtitle">Sign in to continue your guided journey through Sri Lankan heritage.</p>
          </div>

          <button type="button" className="auth-google-btn" onClick={handleGoogleLogin} disabled={authBusy}>
            <GoogleIcon />
            <span>{authBusy ? "Please wait..." : "Continue with Google"}</span>
          </button>

          <div className="auth-divider">or</div>

          <form className="auth-form" onSubmit={handleEmailAuth}>
            <input
              type="email"
              placeholder="Email"
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              autoComplete="email"
            />
            <input
              type="password"
              placeholder="Password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              autoComplete={authMode === "signup" ? "new-password" : "current-password"}
            />
            <button type="submit" className="auth-email-btn" disabled={authBusy}>
              {authMode === "signup" ? "Create account" : "Login with email"}
            </button>
          </form>

          <button
            type="button"
            className="auth-mode-btn"
            onClick={() => {
              setAuthError("");
              setAuthMode((prev) => (prev === "signin" ? "signup" : "signin"));
            }}
            disabled={authBusy}
          >
            {authMode === "signin" ? "Need an account? Sign up" : "Already have an account? Sign in"}
          </button>

          {authError && <p className="auth-error">{authError}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-shell">
      <aside className="chat-sidebar">
        <div className="sidebar-brand">
          <BrandLogo />
          <div>
            <h1>HistoriLanka AI</h1>
            <p className="sidebar-subtitle">RAG + Fine-tuned GPT</p>
            <span className="sidebar-badge">Heritage Copilot</span>
          </div>
        </div>
        <button type="button" className="new-chat-btn" onClick={handleNewChat}>
          + New chat
        </button>
        <div className="sidebar-card">
          <span className="label">Response style</span>
          <select value={style} onChange={handleStyleChange}>
            {styleOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
        <div className="sidebar-card session-list">
          <span className="label">Recents</span>
          {recentSessions.map((session) => (
            <div
              key={session.id}
              className={`session-item ${session.id === activeSession?.id ? "active" : ""}`}
            >
              <div className="session-head">
                <button
                  type="button"
                  className="session-title-btn"
                  onClick={() => {
                    setActiveSessionId(session.id);
                    setOpenRecentMenuId("");
                  }}
                >
                  {session.title}
                </button>
                <button
                  type="button"
                  className="recent-menu-btn"
                  aria-label="Session options"
                  title="Session options"
                  onClick={() =>
                    setOpenRecentMenuId((prev) => (prev === session.id ? "" : session.id))
                  }
                >
                  ...
                </button>
              </div>
              {openRecentMenuId === session.id && (
                <div className="session-actions">
                  <button type="button" onClick={() => handleRenameSession(session.id)}>
                    Rename
                  </button>
                  <button type="button" onClick={() => handleDeleteSession(session.id)}>
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-footer-account" ref={accountMenuRef}>
          {accountMenuOpen && (
            <div className="account-menu-popup">
              <div className="account-menu-profile">
                <span className="account-avatar">{userInitials}</span>
                <div>
                  <div className="account-name">{userName}</div>
                  <div className="account-email">{userEmail}</div>
                </div>
              </div>
              <button type="button" className="account-menu-item danger" onClick={handleSignOut}>Log out</button>
            </div>
          )}

          <button
            type="button"
            className="account-chip"
            onClick={() => setAccountMenuOpen((prev) => !prev)}
            aria-label="Account menu"
          >
            <span className="account-avatar">{userInitials}</span>
            <span className="account-chip-text">
              <strong>{userName}</strong>
              <small>{userPlan}</small>
            </span>
          </button>
        </div>
      </aside>

      <main className={`chat-main ${isFreshSession ? "landing-mode" : ""}`}>
        {isFreshSession ? (
          <section className="landing-stage" aria-live="polite">
            <div className="landing-hero">
              <h2>Welcome to HistoriLanka AI.</h2>
              <p>Discover routes, context, and stories behind Sri Lanka's ancient wonders.</p>
            </div>
            <form
              ref={formRef}
              onSubmit={askQuestion}
              className="composer landing"
            >
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder="Ask anything about Sri Lankan historical sites..."
                rows={2}
              />
              <button type="submit" disabled={loading}>
                {loading ? "Sending..." : <SendIcon />}
              </button>
            </form>
          </section>
        ) : (
          <>
            <header className="chat-headline">
              <h3>{activeSession?.title || "Conversation"}</h3>
              <span className="chat-headline-style">Style: {style}</span>
            </header>
            <section
              ref={chatStreamRef}
              className="chat-stream"
              aria-live="polite"
            >
              {messages.map((message, index) => (
            <article key={`${message.role}-${message.createdAt}-${index}`} className={`msg ${message.role}`}>
              <div className="msg-role">{message.role === "user" ? "You" : "Assistant"}</div>
              {message.role === "user" && editingMessageId === message.id ? (
                <div className="msg-edit-area">
                  <textarea
                    value={editingText}
                    onChange={(e) => setEditingText(e.target.value)}
                    rows={3}
                  />
                  <div className="msg-edit-actions">
                    <button type="button" onClick={handleSendEditedRequest}>
                      Send
                    </button>
                    <button type="button" onClick={handleCancelEditRequest}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <p>{message.content}</p>
              )}

              {editingMessageId !== message.id && (
                <div className="msg-actions">
                  <button
                    type="button"
                    className="icon-btn"
                    onClick={() => handleCopyMessage(message)}
                    title={copiedMessageId === message.id ? "Copied" : "Copy"}
                    aria-label={copiedMessageId === message.id ? "Copied" : "Copy message"}
                  >
                    {copiedMessageId === message.id ? <CheckIcon /> : <CopyIcon />}
                  </button>
                  {message.role === "user" && (
                    <button
                      type="button"
                      className="icon-btn"
                      onClick={() => handleStartEditRequest(message)}
                      title="Edit request"
                      aria-label="Edit request"
                    >
                      <EditIcon />
                    </button>
                  )}
                </div>
              )}
            </article>
              ))}

              {loading && (
                <article className="msg assistant loading">
                  <div className="msg-role">Assistant</div>
                  <p>Thinking...</p>
                </article>
              )}
            </section>

            <form ref={formRef} onSubmit={askQuestion} className="composer">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder="Ask anything about Sri Lankan historical sites..."
                rows={2}
              />
              <button type="submit" disabled={loading}>
                {loading ? "Sending..." : <SendIcon />}
              </button>
            </form>
          </>
        )}

        {error && <div className="chat-error">{error}</div>}
      </main>
    </div>
  );
}
