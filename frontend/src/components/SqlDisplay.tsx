import {Prism as SyntaxHighlighter} from "react-syntax-highlighter";
import {oneLight} from "react-syntax-highlighter/dist/esm/styles/prism";

interface SqlDisplayProps {
  sql: string;
}

const customStyle = {
  backgroundColor: "rgb(248 250 252)",
  borderRadius: "8px",
  padding: "12px 16px",
  fontSize: "13px",
  lineHeight: "1.5",
};

const wrapLines = true;
const lineNumberStyle = {
  color: "rgb(149 156 169)",
  fontSize: "12px",
  marginRight: "16px",
};

export default function SqlDisplay({sql}: SqlDisplayProps) {
  return (
    <SyntaxHighlighter
      language="sql"
      style={oneLight}
      customStyle={customStyle}
      wrapLines={wrapLines}
      lineNumberStyle={lineNumberStyle}
      PreTag="pre"
    >
      {sql}
    </SyntaxHighlighter>
  );
}
