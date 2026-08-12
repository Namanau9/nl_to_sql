interface ResultsTableProps {
  columns: string[];
  rows: unknown[][];
}

export default function ResultsTable({columns, rows}: ResultsTableProps) {
  if (!rows || rows.length === 0) {
    return (
      <p className="text-sm text-text-tertiary py-4 text-center">No results returned.</p>
    );
  }

  const safeRows = rows.map((row) =>
    columns.map((_, j) =>
      row[j] !== null && row[j] !== undefined ? String(row[j]) : "—"
    )
  );

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-bg-alt">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col, i) => (
              <th
                key={i}
                className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {safeRows.map((row, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              {row.map((value, j) => (
                <td key={j} className="px-4 py-2 text-text-secondary">
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
