import {ProcessingStage} from "../types";

interface ProcessingIndicatorProps {
  stages: {key: ProcessingStage; label: string}[];
  currentStage: ProcessingStage;
}

export default function ProcessingIndicator({stages, currentStage}: ProcessingIndicatorProps) {
  const currentIndex = stages.findIndex((s) => s.key === currentStage);

  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-100 flex-shrink-0 flex items-center justify-center">
        <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
      <div className="flex-1">
        <div className="rounded-xl bg-bg-alt border border-border px-4 py-3 shadow-subtle">
          <p className="text-sm text-text-secondary">Processing your question...</p>
          <div className="mt-2 space-y-1.5">
            {stages.map((stage, i) => {
              const isActive = i === currentIndex;
              const isComplete = i < currentIndex;
              return (
                <div key={stage.key} className="flex items-center gap-2">
                  <div
                    className={`
                      w-1.5 h-1.5 rounded-full transition-all
                      ${isActive ? "bg-accent w-2 h-2" : ""}
                      ${isComplete ? "bg-emerald-400" : ""}
                      ${!isActive && !isComplete ? "bg-slate-300" : ""}
                    `}
                  />
                  <span
                    className={`
                      text-xs transition-colors
                      ${isActive ? "text-accent" : ""}
                      ${isComplete ? "text-emerald-500" : ""}
                      ${!isActive && !isComplete ? "text-text-tertiary" : ""}
                    `}
                  >
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
