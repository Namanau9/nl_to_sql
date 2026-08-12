import { useState } from "react";

interface QueryInputProps {
  onSend: (question: string) => void;
  disabled?: boolean;
}

export default function QueryInput({ onSend, disabled }: QueryInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setValue("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Ask a business question..."
        className="flex-1 px-4 py-2.5 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400/50 transition-colors text-sm"
        maxLength={500}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="btn-primary px-5 py-2.5 rounded-lg font-medium text-sm flex items-center gap-2 disabled:opacity-50"
      >
        {disabled ? (
          <>
            <span className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
            Processing...
          </>
        ) : (
          <>Send</>
        )}
      </button>
    </form>
  );
}
