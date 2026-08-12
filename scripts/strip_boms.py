"""Strip UTF-8 BOMs from all text files in the repo (Windows tooling artifact)."""
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
exts = {'.py', '.md', '.sql', '.yml', '.yaml', '.toml', '.txt', '.json', '.ts', '.tsx', '.jsx', '.js', '.html', '.css', '.env.example', '.gitignore'}
count = 0
for p in root.rglob('*'):
    if not p.is_file():
        continue
    if p.name.startswith('.'):
        if p.suffix not in {'.env'} and p.name not in {'.env.example', '.gitignore'}:
            pass
    if 'node_modules' in p.parts or '.venv' in p.parts or '.git' in p.parts:
        continue
    data = p.read_bytes()
    if data.startswith(b'\xef\xbb\xbf'):
        p.write_bytes(data[3:])
        count += 1
        print(f'stripped BOM: {p.name}')
print(f'done: {count} files')
