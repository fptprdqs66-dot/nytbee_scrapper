# NYTBee Helper Safari Extension

This folder contains a Safari-compatible web extension that bundles `nytbee_dict.txt`
so the solver can run offline without hitting external dictionaries.

## Setup in Safari

1. Open Xcode and choose **File > New > Project**.
2. Select **Safari Extension App** and point the extension's root folder to
   `safari-extension`.
3. Enable the extension in **Safari > Settings > Extensions**.
4. Visit the Spelling Bee page and click the extension icon to find or fill answers.

## Notes

- The wordlist is bundled at `wordlist/nytbee_dict.txt` and loaded directly by the
  content script.
- If the page layout changes, update the selectors in `content.js`.
