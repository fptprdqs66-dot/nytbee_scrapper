/**
 * NYTBee encoded auto-type bookmarklet.
 *
 * Opens the latest encoded word list in a new tab, waits for focus to return,
 * prompts for the encoded payload, decodes it with the current puzzle letters,
 * and types each answer followed by Enter with human-like delays.
 */
(async () => {
  // Update this URL to wherever you publish the latest encoded word list.
  const LATEST_ENCODED_URL =
    'https://raw.githubusercontent.com/your-org/nytbee_scrapper/main/results/latest.encoded.txt';
  const MIN_KEY_DELAY_MS = 80;
  const MAX_KEY_DELAY_MS = 160;
  const MIN_WORD_DELAY_MS = 220;
  const MAX_WORD_DELAY_MS = 420;

  /** Sleep for a specified duration. */
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  /** Return a random integer between min and max, inclusive. */
  const randomBetween = (min, max) =>
    Math.floor(Math.random() * (max - min + 1)) + min;

  /** Open the latest encoded word list in a separate tab. */
  const openEncodedListTab = () => window.open(LATEST_ENCODED_URL, '_blank', 'noopener');

  /** Wait for focus to return to the current window. */
  const waitForWindowFocus = () =>
    new Promise((resolve) => {
      if (document.hasFocus()) {
        const timeoutId = setTimeout(resolve, 1000);
        window.addEventListener(
          'blur',
          () => {
            clearTimeout(timeoutId);
            window.addEventListener('focus', resolve, { once: true });
          },
          { once: true }
        );
      } else {
        window.addEventListener('focus', resolve, { once: true });
      }
    });

  /** Convert a base64url string into a byte array. */
  const base64UrlToBytes = (payload) => {
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padding = '='.repeat((4 - (normalized.length % 4)) % 4);
    const decoded = atob(normalized + padding);
    return Uint8Array.from(decoded, (char) => char.charCodeAt(0));
  };

  /** Bit reader for packed word data. */
  class BitReader {
    constructor(bytes) {
      this.bytes = bytes;
      this.position = 0;
      this.buffer = 0;
      this.bufferBits = 0;
    }

    /** Read the next value using a fixed number of bits. */
    read(bits) {
      if (bits <= 0) {
        throw new Error('Bit length must be positive.');
      }
      while (this.bufferBits < bits) {
        if (this.position >= this.bytes.length) {
          throw new Error('Unexpected end of encoded data.');
        }
        this.buffer = (this.buffer << 8) | this.bytes[this.position];
        this.bufferBits += 8;
        this.position += 1;
      }
      const shift = this.bufferBits - bits;
      const value = (this.buffer >> shift) & ((1 << bits) - 1);
      this.bufferBits -= bits;
      this.buffer &= shift ? (1 << shift) - 1 : 0;
      return value;
    }
  }

  /**
   * Decode a packed word list using the puzzle letters.
   * The puzzle letters must be 7 letters, with the required letter first.
   */
  const decodeWordList = (payload, letters) => {
    if (!letters || letters.length !== 7) {
      throw new Error('Puzzle letters must be 7 characters (required letter first).');
    }
    const reader = new BitReader(base64UrlToBytes(payload.trim()));
    const totalWords = reader.read(12);
    const decodedWords = [];
    let current = [];

    while (decodedWords.length < totalWords) {
      const value = reader.read(3);
      if (value === 7) {
        decodedWords.push(current.join(''));
        current = [];
      } else {
        current.push(letters[value]);
      }
    }

    return decodedWords;
  };

  /** Try to read the puzzle letters from the NYT Spelling Bee page. */
  const getPuzzleLettersFromPage = () => {
    const letterNodes = [...document.querySelectorAll('[data-testid="hive-letter"]')];
    if (letterNodes.length !== 7) {
      return null;
    }

    const centerNode = document.querySelector('[data-testid="hive-center"] [data-testid="hive-letter"]');
    const centerLetter = centerNode?.textContent?.trim().toLowerCase();
    const outerLetters = letterNodes
      .filter((node) => node !== centerNode)
      .map((node) => node.textContent?.trim().toLowerCase())
      .filter(Boolean);

    if (!centerLetter || outerLetters.length !== 6) {
      return null;
    }

    return `${centerLetter}${outerLetters.join('')}`;
  };

  /** Insert a single character into the active input. */
  const insertCharacter = (target, character, isTextInput, isEditable) => {
    if (isTextInput) {
      const start = target.selectionStart ?? target.value.length;
      const end = target.selectionEnd ?? target.value.length;
      target.value = `${target.value.slice(0, start)}${character}${target.value.slice(end)}`;
      target.selectionStart = target.selectionEnd = start + character.length;
      target.dispatchEvent(
        new InputEvent('input', { bubbles: true, data: character, inputType: 'insertText' })
      );
      return;
    }

    if (isEditable) {
      document.execCommand('insertText', false, character);
    }
  };

  /** Dispatch a keyboard event on the target element. */
  const dispatchKeyEvent = (target, type, key) => {
    const keyboardEvent = new KeyboardEvent(type, {
      key,
      bubbles: true,
      cancelable: true,
    });
    target.dispatchEvent(keyboardEvent);
  };

  /** Press Enter and clear the input field. */
  const pressEnter = (target, isTextInput, isEditable) => {
    dispatchKeyEvent(target, 'keydown', 'Enter');
    if (isTextInput) {
      target.dispatchEvent(
        new InputEvent('input', { bubbles: true, data: null, inputType: 'insertLineBreak' })
      );
      target.value = '';
    } else if (isEditable) {
      document.execCommand('insertParagraph', false);
    }
    dispatchKeyEvent(target, 'keyup', 'Enter');
  };

  /** Type a word with human-like delays, then submit it. */
  const typeWordAndSubmit = async (target, word, isTextInput, isEditable) => {
    for (const letter of word) {
      dispatchKeyEvent(target, 'keydown', letter);
      dispatchKeyEvent(target, 'keypress', letter);
      insertCharacter(target, letter, isTextInput, isEditable);
      dispatchKeyEvent(target, 'keyup', letter);
      await sleep(randomBetween(MIN_KEY_DELAY_MS, MAX_KEY_DELAY_MS));
    }

    pressEnter(target, isTextInput, isEditable);
    await sleep(randomBetween(MIN_WORD_DELAY_MS, MAX_WORD_DELAY_MS));
  };

  const targetElement = document.activeElement;
  const isTextInput =
    targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement;
  const isEditable = Boolean(targetElement?.isContentEditable);

  if (!targetElement || (!isTextInput && !isEditable)) {
    throw new Error('Focus the game input field before running this bookmarklet.');
  }

  openEncodedListTab();
  await waitForWindowFocus();

  const encodedPayload = window.prompt('Paste the encoded NYTBee word list:');
  if (!encodedPayload) {
    throw new Error('No encoded payload provided.');
  }

  const detectedLetters = getPuzzleLettersFromPage();
  const puzzleLetters =
    detectedLetters ?? window.prompt('Enter puzzle letters (required letter first):');
  if (!puzzleLetters) {
    throw new Error('Puzzle letters are required to decode the word list.');
  }

  const answers = decodeWordList(encodedPayload, puzzleLetters.trim().toLowerCase());
  if (!answers.length) {
    throw new Error('No answers were decoded from the payload.');
  }

  console.log(`Typing ${answers.length} decoded answers.`);
  for (const answer of answers) {
    await typeWordAndSubmit(targetElement, answer, isTextInput, isEditable);
  }
  console.log('Finished typing all decoded answers.');
})();
