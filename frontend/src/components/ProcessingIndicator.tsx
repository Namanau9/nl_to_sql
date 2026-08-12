import { ProcessingStage } from "../types";

interface ProcessingIndicatorProps {
  stages: { key: ProcessingStage; label: string }[];
  currentStage: ProcessingStage;
}

export default function ProcessingIndicator({ stages, currentStage }: ProcessingIndicatorProps) {
  const currentIndex = stages.findIndex((s) => s.key === currentStage);

  return (
    <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="glass border border-amber-400/30 rounded-xl px-8 py-6 max-w-md w-full mx-4">
        <h3 className="text-amber-400 font-display text-lg mb-4">Processing your question</h3>
        <div className="space-y-3">
          {stages.map((stage, i) => {
            const isActive = i === currentIndex;
            const isComplete = i < currentIndex;
            return (
              <div key={stage.key} className="flex items-center gap-3">
                <div
                  className={`stage-dot ${isActive ? "active" : ""} ${isComplete ? "complete" : ""}`}
                />
                <span
                  className={`text-sm transition-colors ${
                    isActive ? "text-amber-400" : isComplete ? "text-emerald-400" : "text-slate-500"
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
