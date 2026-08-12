import {Sun, Moon} from "lucide-react";
import {cn} from "../lib/utils";

interface ThemeToggleProps {
  theme: "light" | "dark";
  onToggle: () => void;
}

export default function ThemeToggle({theme, onToggle}: ThemeToggleProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className={cn(
        "p-1.5 rounded-lg transition-all duration-200",
        theme === "dark"
          ? "bg-slate-100 text-slate-700 hover:bg-slate-200"
          : "bg-slate-100 text-slate-700 hover:bg-slate-200"
      )}
    >
      {theme === "dark" ? (
        <Sun className="w-4 h-4" />
      ) : (
        <Moon className="w-4 h-4" />
      )}
    </button>
  );
}
