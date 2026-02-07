/**
 * NYTBee auto-type shortcut.
 *
 * Run this in the browser console (or wrap as a bookmarklet) while the cursor
 * is focused in the Spelling Bee input field. It fetches today's answers from
 * nytbee.com, then types each answer followed by Enter.
 */
(async () => {
  const KEY_DELAY_MS = 10;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const formatTodayDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  };

  const answerPageUrl = `https://nytbee.com/Bee_${formatTodayDate()}.html`;

  const fetchAnswerPage = async () => {
    try {
      const response = await fetch(answerPageUrl, { credentials: 'omit' });
      if (!response.ok) {
        throw new Error(`NYTBee responded with status ${response.status}`);
      }
      return await response.text();
    } catch (directFetchError) {
      const proxyUrl = `https://r.jina.ai/http://nytbee.com/Bee_${formatTodayDate()}.html`;
      const proxyResponse = await fetch(proxyUrl, { credentials: 'omit' });
      if (!proxyResponse.ok) {
        throw new Error(
          `Unable to fetch NYTBee answers directly (${directFetchError}) or via proxy (${proxyResponse.status}).`
        );
      }
      return await proxyResponse.text();
    }
  };

  const extractAnswers = (html) => {
    const documentParser = new DOMParser();
    const parsedDocument = documentParser.parseFromString(html, 'text/html');
    const answerItems = [...parsedDocument.querySelectorAll('#main-answer-list li')];

    const normalizedAnswers = answerItems
      .map((item) => (item.textContent || '').trim().toLowerCase())
      .map((answer) => answer.replace(/[^a-z]/g, ''))
      .filter((answer) => answer.length > 0);

    return [...new Set(normalizedAnswers)];
  };

  const targetElement = document.activeElement;
  const isTextInput =
    targetElement instanceof HTMLInputElement || targetElement instanceof HTMLTextAreaElement;
  const isEditable = Boolean(targetElement?.isContentEditable);

  if (!targetElement || (!isTextInput && !isEditable)) {
    throw new Error('Focus the game input field before running this shortcut.');
  }

  const dispatchKeyEvent = (type, key) => {
    const keyboardEvent = new KeyboardEvent(type, {
      key,
      bubbles: true,
      cancelable: true,
    });
    targetElement.dispatchEvent(keyboardEvent);
  };

  const insertCharacter = (character) => {
    if (isTextInput) {
      const start = targetElement.selectionStart ?? targetElement.value.length;
      const end = targetElement.selectionEnd ?? targetElement.value.length;
      targetElement.value = `${targetElement.value.slice(0, start)}${character}${targetElement.value.slice(end)}`;
      targetElement.selectionStart = targetElement.selectionEnd = start + character.length;
      targetElement.dispatchEvent(new InputEvent('input', { bubbles: true, data: character, inputType: 'insertText' }));
      return;
    }

    if (isEditable) {
      document.execCommand('insertText', false, character);
    }
  };

  const pressEnter = () => {
    dispatchKeyEvent('keydown', 'Enter');
    if (isTextInput) {
      targetElement.dispatchEvent(new InputEvent('input', { bubbles: true, data: null, inputType: 'insertLineBreak' }));
      targetElement.value = '';
    } else if (isEditable) {
      document.execCommand('insertParagraph', false);
    }
    dispatchKeyEvent('keyup', 'Enter');
  };

  const typeWordAndSubmit = async (word) => {
    for (const letter of word) {
      dispatchKeyEvent('keydown', letter);
      dispatchKeyEvent('keypress', letter);
      insertCharacter(letter);
      dispatchKeyEvent('keyup', letter);
      await sleep(KEY_DELAY_MS);
    }

    pressEnter();
    await sleep(KEY_DELAY_MS);
  };

  const html = await fetchAnswerPage();
  const answers = extractAnswers(html);

  if (!answers.length) {
    throw new Error('No answers were extracted from the NYTBee page.');
  }

  console.log(`Typing ${answers.length} answers from ${answerPageUrl}`);
  for (const answer of answers) {
    await typeWordAndSubmit(answer);
  }
  console.log('Finished typing all answers.');
})();
