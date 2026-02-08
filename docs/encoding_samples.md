# Terminator Encoding Samples

Seed: 23

Command used:

```
python - <<'PY'
import sys
from pathlib import Path
import random

ROOT = Path('.').resolve()
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

from nytbee_solver import encoding, solver

random.seed(23)
alphabet = 'abcdefghijklmnopqrstuvwxyz'
wordlist_path = ROOT / 'nytbee_dict.txt'

lines = ["# Terminator Encoding Samples", "", "Seed: 23", "", "| Puzzle Letters (required first) | Word Count | Encoded |", "| --- | ---: | --- |"]

for _ in range(5):
    letters = ''.join(random.sample(alphabet, 7))
    required = letters[0]
    words, _, _, _ = solver.solve_spelling_bee(letters, wordlist_path=wordlist_path)
    encoded = encoding.encode_terminated(words, letters, required)
    lines.append(f"| `{letters}` | {len(words)} | `{encoded}` |")

output_path = ROOT / 'docs' / 'encoding_samples.md'
output_path.parent.mkdir(exist_ok=True)
output_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
print(f"Wrote {output_path}")
PY
```

| Puzzle Letters (required first) | Word Count | Encoded |
| --- | ---: | --- |
| `yjcaszn` | 4 | `AET2HQe-ew9eHA` |
| `mqlegio` | 17 | `ARlAfiw8Ww8yY6ofVG62HDTfDD4Y3FT4qXFD4oe41XGT4yXA` |
| `ahtozdc` | 29 | `AdGLfCQx-GD-Cx-IvxC-Yx-Yy-YXzw-eY-dHoxHoQ9bovIWPIR5CI5dF7CPeQvQx6GfQy6CTfRC6IWPTF6ewQ4A` |
| `wpnaqux` | 4 | `AELLHLC5YLHDSfA` |
| `lybgxsz` | 0 | `AAA` |
