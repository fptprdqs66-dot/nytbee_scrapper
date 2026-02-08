/**
 * Load the bundled wordlist from the extension package.
 * @returns {Promise<Set<string>>} Set of words.
 */
async function loadWordList() {
  const wordListUrl = chrome.runtime.getURL("wordlist/nytbee_dict.txt");
  const response = await fetch(wordListUrl);
  if (!response.ok) {
    throw new Error(`Failed to load wordlist: ${response.status}`);
  }
  const text = await response.text();
  const words = text
    .split(/\r?\n/)
    .map((line) => line.trim().toLowerCase())
    .filter((line) => line.length > 0);
  return new Set(words);
}

/**
 * Attempt to extract puzzle letters from the Spelling Bee page.
 * @returns {{center: string, outer: string[]}} The center letter and outer letters.
 */
function extractPuzzleLetters() {
  const letterElements = Array.from(
    document.querySelectorAll(
      ".sb-letter, [data-testid='spelling-bee-letter'], [aria-label='Spelling Bee Letter']"
    )
  );

  const letters = letterElements
    .map((element) => element.textContent || "")
    .map((text) => text.trim().toLowerCase())
    .filter(Boolean);

  const centerElement = document.querySelector(
    ".sb-letter--center, [data-testid='spelling-bee-letter-center']"
  );
  const center = centerElement?.textContent?.trim().toLowerCase() || letters[0] || "";
  const outer = letters.filter((letter) => letter !== center);

  return { center, outer };
}

/**
 * Filter the word list to valid Spelling Bee answers.
 * @param {Iterable<string>} words
 * @param {{center: string, outer: string[]}} letters
 * @returns {{valid: string[], pangrams: string[]}}
 */
function findValidWords(words, letters) {
  const allowed = new Set([letters.center, ...letters.outer]);
  const valid = [];
  const pangrams = [];

  for (const word of words) {
    if (word.length < 4) {
      continue;
    }
    if (!word.includes(letters.center)) {
      continue;
    }

    let usesOnlyAllowed = true;
    for (const character of word) {
      if (!allowed.has(character)) {
        usesOnlyAllowed = false;
        break;
      }
    }
    if (!usesOnlyAllowed) {
      continue;
    }

    valid.push(word);
    if ([...allowed].every((character) => word.includes(character))) {
      pangrams.push(word);
    }
  }

  return { valid, pangrams };
}

/**
 * Submit words to the Spelling Bee input field.
 * @param {string[]} words
 */
function submitWords(words) {
  const input = document.querySelector("input[type='text'], input[aria-label='Enter a word']");
  const submitButton = document.querySelector("button[type='submit'], button[aria-label='Submit']");

  if (!input || !submitButton) {
    throw new Error("Could not find the Spelling Bee input or submit button.");
  }

  for (const word of words) {
    input.value = word;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    submitButton.click();
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "solve") {
    return false;
  }

  (async () => {
    const wordList = await loadWordList();
    const letters = extractPuzzleLetters();

    if (!letters.center) {
      throw new Error("Unable to detect puzzle letters.");
    }

    const results = findValidWords(wordList, letters);

    if (message?.payload?.action === "fill") {
      submitWords(results.valid);
    }

    sendResponse({
      letters,
      valid: results.valid,
      pangrams: results.pangrams
    });
  })().catch((error) => {
    sendResponse({ error: error.message });
  });

  return true;
});
