/**
 * Minimal NYT Spelling Bee auto-typist using window.gameData.today.answers.
 *
 * Focus the game input field, then run as a bookmarklet or console snippet.
 */
javascript:(async()=>{const answers=window.gameData?.today?.answers;if(!Array.isArray(answers)||answers.length===0){alert("No window.gameData.today.answers found.");return;}const sleep=ms=>new Promise(r=>setTimeout(r,ms));const charDelay=80;const wordDelay=600;for(const word of answers){for(const ch of word){window.dispatchEvent(new KeyboardEvent("keydown",{key:ch,bubbles:true}));await sleep(charDelay);}window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}));await sleep(wordDelay);}})();
