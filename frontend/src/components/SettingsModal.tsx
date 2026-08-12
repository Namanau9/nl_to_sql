import {Settings} from "../types";
import {X} from "lucide-react";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  settings: Settings;
  onChange: (settings: Settings) => void;
}

export default function SettingsModal({open, onClose, settings, onChange}: SettingsModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-bg-alt border border-border rounded-xl shadow-elevated w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-text-primary">Settings</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-text-secondary" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Provider
            </label>
            <select
              value={settings.provider}
              onChange={(e) => onChange({...settings, provider: e.target.value})}
              className="w-full px-3 py-2 border border-border rounded-lg bg-bg text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            >
              <option value="openrouter">OpenRouter</option>
              <option value="mock">Mock (for testing)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Model
            </label>
            <input
              type="text"
              value={settings.model}
              onChange={(e) => onChange({...settings, model: e.target.value})}
              className="w-full px-3 py-2 border border-border rounded-lg bg-bg text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              placeholder="e.g. google/gemini-2.0-flash-exp:free"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
