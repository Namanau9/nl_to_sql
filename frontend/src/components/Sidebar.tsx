import {ChatSession} from "../types";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onDelete,
  isOpen,
  onClose,
}: SidebarProps) {
  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <div
        className={`
          fixed lg:fixed lg:translate-x-0 z-50 lg:z-0
          inset-y-0 left-0 w-64 bg-bg-alt border-r border-border
          flex flex-col h-screen transition-transform duration-200
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="p-4 border-b border-border">
          <button
            onClick={onNewChat}
            className="w-full px-3 py-2 text-sm font-medium text-text-primary bg-accent/5 border border-accent/20 rounded-lg hover:bg-accent/10 transition-colors flex items-center justify-center gap-2"
          >
            <span className="text-xs">+</span>
            New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 ? (
            <p className="text-xs text-text-tertiary text-center py-8 px-4">
              No conversations yet.
            </p>
          ) : (
            <ul className="py-2">
              {sessions.map((session) => (
                <li key={session.id}>
                  <button
                    onClick={() => onSelect(session.id)}
                    className={`
                      w-full text-left px-4 py-2.5 group
                      ${activeSessionId === session.id
                        ? "bg-accent/5"
                        : "hover:bg-bg"}
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors truncate">
                        {session.title}
                      </span>
                    </div>
                    <p className="text-xs text-text-tertiary mt-0.5">
                      {session.messages.length} message{session.messages.length !== 1 ? "s" : ""} · {session.created_at.toLocaleDateString()}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}
