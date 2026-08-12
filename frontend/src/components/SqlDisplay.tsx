import {Prism as SyntaxHighlighter} from "react-syntax-highlighter";
import {oneLight} from "react-syntax-highlighter/dist/esm/styles/prism";
import {useTheme} from "../hooks/useTheme";

interface SqlDisplayProps {
  sql: string;
}

const wrapLines = true;

const baseCustomStyle = {
  borderRadius: "8px",
  padding: "12px 16px",
  fontSize: "13px",
  lineHeight: "1.5",
};

const baseLineNumberStyle = {
  fontSize: "12px",
  marginRight: "16px",
};

export default function SqlDisplay({sql}: SqlDisplayProps) {
  const {theme} = useTheme();

  const oneLightOverride = {
    ...oneLight,
    backgroundColor: "rgb(var(--color-bg-alt))",
    color: "rgb(var(--color-text-secondary))",
  };

  const customStyle = {
    ...baseCustomStyle,
    backgroundColor: theme === "dark" ? "rgb(24 28 45)" : "rgb(248 250 252)",
    borderColor: "rgb(var(--color-border))",
  };

  const lineNumberStyle = {
    ...baseLineNumberStyle,
    color: theme === "dark" ? "rgb(107 114 128)" : "rgb(149 156 169)",
  };

  return (
    <SyntaxHighlighter
      language="sql"
      style={oneLightOverride}
      customStyle={customStyle}
      wrapLines={wrapLines}
      lineNumberStyle={lineNumberStyle}
      PreTag="pre"
    >
      {sql}
    </SyntaxHighlighter>
  );
}
