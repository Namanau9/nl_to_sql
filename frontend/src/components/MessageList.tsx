import { ChatMessage } from "../types";
import ResultsTable from "./ResultsTable";

interface MessageListProps {
  messages: ChatMessage[];
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-6">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`rounded-xl p-4 ${
            msg.role === "user"
              ? "bg-amber-400/10 border border-amber-400/30 ml-12"
              : "glass border border-slate-700"
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                msg.role === "user"
                  ? "bg-amber-400 text-slate-900"
                  : "bg-slate-700 text-amber-400"
              }`}
            >
              {msg.role === "user" ? "U" : "AI"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-300 leading-relaxed break-words">
                {msg.content}
              </p>
              {msg.error && (
                <p className="mt-2 text-sm text-red-400">{msg.error}</p>
              )}
              {msg.sql && (
                <pre className="mt-3 text-xs text-slate-400 bg-slate-800/50 rounded-lg p-3 overflow-x-auto border border-slate-700">
                  <code>{msg.sql}</code>
                </pre>
              )}
              {msg.results && (
                <div className="mt-3">
                  <ResultsTable columns={msg.results.columns} rows={msg.results.rows} />
                  <p className="text-xs text-slate-500 mt-2">
                    {msg.results.row_count} rows returned in {msg.results.execution_ms}ms
                  </p>
                </div>
              )}
              {msg.explanation && (!msg.results || msg.role === "assistant") && (
                <p className="mt-2 text-sm text-slate-300 italic leading-relaxed">
                  {msg.explanation}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
