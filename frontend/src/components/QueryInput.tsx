import {useState, useRef, useEffect} from "react";
import {cn} from "../lib/utils";

interface QueryInputProps {
  onSend: (question: string) => void;
  disabled?: boolean;
}

export default function QueryInput({onSend, disabled}: QueryInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const hasValue = value.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask a business question..."
          className={cn(
            "w-full px-4 py-3 bg-bg-alt border border-border rounded-lg",
            "text-text-primary placeholder-text-tertiary",
            "focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent",
            "resize-none transition-colors text-sm leading-relaxed",
            "min-h-[44px] max-h-40",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
          maxLength={500}
          rows={1}
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !hasValue}
        className={cn(
          "px-4 py-3 rounded-lg font-medium text-sm transition-all flex-shrink-0",
          "bg-accent hover:bg-accent-hover text-white",
          "disabled:opacity-40 disabled:cursor-not-allowed",
          "flex items-center justify-center min-w-[80px]"
        )}
      >
        {disabled ? (
          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          "Send"
        )}
      </button>
    </form>
  );
}
