import { useState, useRef, useEffect } from "react";
import "./App.css";
import { ChatMessage, QueryResponse, ProcessingStage } from "./types";
import QueryInput from "./components/QueryInput";
import MessageList from "./components/MessageList";
import ProcessingIndicator from "./components/ProcessingIndicator";
import HealthStatus from "./components/HealthStatus";

const API_URL = import.meta.env.VITE_API_URL || window.location.origin;

const STAGE_ORDER: { key: ProcessingStage; label: string }[] = [
  { key: "thinking", label: "Analyzing question..." },
  { key: "schema", label: "Finding relevant schema..." },
  { key: "generating", label: "Generating SQL..." },
  { key: "validating", label: "Validating query..." },
  { key: "executing", label: "Executing query..." },
  { key: "explaining", label: "Analyzing results..." },
];

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<ProcessingStage>("thinking");
  const [health, setHealth] = useState<"ok" | "degraded" | "unknown">("unknown");

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((data) => setHealth(data.status === "ok" ? "ok" : "degraded"))
      .catch(() => setHealth("degraded"));
  }, []);

  const handleSend = async (question: string) => {
    if (isProcessing) return;
    setIsProcessing(true);
    setCurrentStage("thinking");

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

    const stages = STAGE_ORDER;
    let stageIndex = 0;

    const advanceStage = () => {
      if (stageIndex < stages.length) {
        setCurrentStage(stages[stageIndex].key);
        stageIndex++;
      }
    };

    advanceStage();
    setMessages((prev) => [...prev, assistantMessage]);

    const interval = setInterval(() => {
      advanceStage();
    }, 800);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      clearInterval(interval);
      setCurrentStage("done");

      if (!response.ok) {
        const error = await response.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? { ...m, content: "I encountered an error processing your question.", error: error.detail || "Unknown error", results: null }
              : m,
          ),
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
            : m,
        ),
      );
    } catch (e) {
      clearInterval(interval);
      setCurrentStage("done");
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: "I couldn't reach the backend service.", error: String(e), results: null }
            : m,
        ),
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      <header className="glass border-b border-amber-400/20 px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-display text-amber-400">NL to SQL Assistant</h1>
        <HealthStatus status={health} />
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center mt-12">
            <h2 className="text-3xl font-display text-slate-300 mb-4">Ask a business question</h2>
            <p className="text-slate-500 max-w-md">
              "What were our top 5 products by revenue last month?"
              <br />
              "Show monthly revenue for 2026."
              <br />
              "Which category generated the most revenue?"
            </p>
          </div>
        ) : (
          <MessageList messages={messages} />
        )}

        {isProcessing && <ProcessingIndicator stages={STAGE_ORDER} currentStage={currentStage} />}

        <div ref={bottomRef} />
      </main>

      <footer className="p-4 border-t border-slate-700">
        <QueryInput onSend={handleSend} disabled={isProcessing} />
      </footer>
    </div>
  );
}
