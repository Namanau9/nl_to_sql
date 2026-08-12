import {useState, useRef, useEffect} from "react";
import "./App.css";
import {ChatMessage, ChatSession, QueryResponse, ProcessingStage, Settings} from "./types";
import QueryInput from "./components/QueryInput";
import MessageList from "./components/MessageList";
import ProcessingIndicator from "./components/ProcessingIndicator";
import HealthStatus from "./components/HealthStatus";
import Sidebar from "./components/Sidebar";
import SettingsModal from "./components/SettingsModal";
import {Menu, Settings as SettingsIcon, X} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || window.location.origin;

const STAGE_ORDER: {key: ProcessingStage; label: string}[] = [
  {key: "thinking", label: "Analyzing question..."},
  {key: "schema", label: "Finding relevant schema..."},
  {key: "generating", label: "Generating SQL..."},
  {key: "validating", label: "Validating query..."},
  {key: "executing", label: "Executing query..."},
  {key: "explaining", label: "Analyzing results..."},
];

const DEFAULT_SETTINGS: Settings = {
  provider: "openrouter",
  model: "google/gemini-2.0-flash-exp:free",
};

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<ProcessingStage>("thinking");
  const [health, setHealth] = useState<"ok" | "degraded" | "unknown">("unknown");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior: "smooth"});
  }, [messages, isProcessing]);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((data) => setHealth(data.status === "ok" ? "ok" : "degraded"))
      .catch(() => setHealth("degraded"));
  }, []);

  const loadSession = (id: string) => {
    const session = sessions.find((s) => s.id === id);
    if (session) {
      setMessages([...session.messages]);
      setActiveSessionId(id);
      setSidebarOpen(false);
    }
  };

  const createNewChat = () => {
    const newSession: ChatSession = {
      id: crypto.randomUUID(),
      title: "New conversation",
      messages: [],
      created_at: new Date(),
    };
    setSessions([newSession, ...sessions]);
    setMessages([]);
    setActiveSessionId(newSession.id);
    setSidebarOpen(false);
  };

  const saveSession = () => {
    if (activeSessionId && messages.length > 0) {
      const session = sessions.find((s) => s.id === activeSessionId);
      if (session) {
        const updated = {...session, messages: [...messages]};
        setSessions(sessions.map((s) => (s.id === activeSessionId ? updated : s)));
      }
    }
  };

  const updateSessionTitle = (id: string, title: string) => {
    setSessions(sessions.map((s) => (s.id === id ? {...s, title} : s)));
  };

  const handleSend = async (question: string) => {
    if (isProcessing) return;
    setIsProcessing(true);
    setCurrentStage("thinking");

    if (!activeSessionId) {
      const newSession: ChatSession = {
        id: crypto.randomUUID(),
        title: question.slice(0, 40) + (question.length > 40 ? "..." : ""),
        messages: [],
        created_at: new Date(),
      };
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    let stageIndex = 0;
    const advanceStage = () => {
      if (stageIndex < STAGE_ORDER.length) {
        setCurrentStage(STAGE_ORDER[stageIndex].key);
        stageIndex++;
      }
    };

    advanceStage();

    const interval = setInterval(() => {
      advanceStage();
    }, 800);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question}),
      });

      clearInterval(interval);
      setCurrentStage("done");

      if (!response.ok) {
        const errorData = await response.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: "I encountered an error processing your question.",
                  error: errorData.detail || "Unknown error",
                  results: null,
                }
              : m
          )
        );
        return;
      }

      const data: QueryResponse = await response.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? {
                ...m,
                content: data.explanation || "Query completed.",
                sql: data.sql,
                results: data.results,
                explanation: data.explanation,
                error: data.error,
                execution_ms: data.execution_ms,
              }
            : m
        )
      );

      if (activeSessionId) {
        updateSessionTitle(activeSessionId, question.slice(0, 40) + (question.length > 40 ? "..." : ""));
      }
    } catch (e) {
      clearInterval(interval);
      setCurrentStage("done");
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? {
                ...m,
                content: "I couldn't reach the backend service.",
                error: String(e),
                results: null,
              }
            : m
        )
      );
    } finally {
      setIsProcessing(false);
      saveSession();
    }
  };

  return (
    <div className="h-screen flex bg-bg text-text-primary">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={loadSession}
        onNewChat={createNewChat}
        onDelete={(id) => {
          setSessions(sessions.filter((s) => s.id !== id));
          if (activeSessionId === id) {
            setMessages([]);
            setActiveSessionId(null);
          }
        }}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-border bg-bg-alt px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5 text-text-secondary" />
            </button>
            <h1 className="font-medium text-text-primary">NL to SQL Assistant</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSettings(true)}
              className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <SettingsIcon className="w-4 h-4 text-text-secondary" />
            </button>
            <HealthStatus status={health} />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto w-full">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center mt-16">
                <h2 className="text-xl font-medium text-text-primary mb-3">Ask a business question</h2>
                <p className="text-sm text-text-tertiary max-w-md space-y-1">
                  <span className="block">"What were our top 5 products by revenue last month?"</span>
                  <span className="block">"Show monthly revenue for 2026."</span>
                  <span className="block">"Which category generated the most revenue?"</span>
                </p>
              </div>
            ) : (
              <MessageList messages={messages} />
            )}

            {isProcessing && <ProcessingIndicator stages={STAGE_ORDER} currentStage={currentStage} />}

            <div ref={bottomRef} />
          </div>
        </main>

        <footer className="border-t border-border bg-bg-alt px-4 py-3">
          <div className="max-w-3xl mx-auto">
            <QueryInput onSend={handleSend} disabled={isProcessing} />
          </div>
        </footer>
      </div>

      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onChange={setSettings}
      />
    </div>
  );
}
