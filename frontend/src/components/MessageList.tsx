import {ChatMessage} from "../types";
import ResultsTable from "./ResultsTable";
import SqlDisplay from "./SqlDisplay";

interface MessageListProps {
  messages: ChatMessage[];
}

export default function MessageList({messages}: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div key={msg.id} className="flex gap-3">
          <div
            className={`
              w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-medium
              ${msg.role === "user"
                ? "bg-accent text-white"
                : "bg-slate-100 text-slate-600"}
            `}
          >
            {msg.role === "user" ? "U" : "AI"}
          </div>
          <div className="flex-1 min-w-0">
            <div
              className={`
                rounded-xl px-4 py-3
                ${msg.role === "user"
                  ? "bg-accent/5 border border-accent/10"
                  : "bg-bg-alt border border-border shadow-subtle"}
              `}
            >
              <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                {msg.content || (msg.error ? "I encountered an error processing your question." : "Thinking...")}
              </p>
            </div>

            {msg.error && (
              <div className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                <p className="text-xs text-red-600">{msg.error}</p>
              </div>
            )}

            {msg.sql && (
              <div className="mt-2">
                <SqlDisplay sql={msg.sql} />
              </div>
            )}

            {msg.results && (
              <div className="mt-2">
                <ResultsTable columns={msg.results.columns} rows={msg.results.rows} />
                {msg.results.row_count > 0 && (
                  <p className="text-xs text-text-tertiary mt-2">
                    {msg.results.row_count} row{msg.results.row_count !== 1 ? "s" : ""} in {msg.results.execution_ms}ms
                  </p>
                )}
              </div>
            )}

            {msg.explanation && msg.role === "assistant" && !msg.content && (
              <p className="text-sm text-text-secondary mt-1 italic">
                {msg.explanation}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
