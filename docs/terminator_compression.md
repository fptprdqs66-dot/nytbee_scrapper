# Terminator Compression Experiments

Seed: 23
Sample count: 50

| Method | Avg Encoded Chars | Avg Ratio vs Terminator |
| --- | ---: | ---: |
| `terminated` | 28.4 | 1.000 |
| `terminated+zlib` | 40.1 | 2.783 |
| `terminated+bz2` | 91.9 | 9.179 |
| `terminated+lzma` | 105.0 | 13.464 |
