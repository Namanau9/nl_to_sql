import { QueryResultData } from "../types";

interface ResultsTableProps {
  columns: string[];
  rows: unknown[][];
}

export default function ResultsTable({ columns, rows }: ResultsTableProps) {
  if (!rows || rows.length === 0) {
    return <p className="text-xs text-slate-500">No results returned.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-800/30">
      <table className="min-w-full text-xs">
        <thead>
          <tr className="border-b border-slate-700">
            {columns.map((col, i) => (
              <th
                key={i}
                className="px-3 py-2 text-left text-slate-300 font-medium whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-slate-800 last:border-0">
              {columns.map((_, j) => (
                <td key={j} className="px-3 py-2 text-slate-400 whitespace-nowrap">
                  {row[j] !== null && row[j] !== undefined ? String(row[j]) : "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
