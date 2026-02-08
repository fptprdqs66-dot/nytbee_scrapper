/**
 * Send a message to the active tab to solve the puzzle.
 * @param {"solve"|"fill"} action
 */
function requestSolve(action) {
  const status = document.getElementById("status");
  status.textContent = "Working...";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tabId = tabs[0]?.id;
    if (!tabId) {
      status.textContent = "No active Spelling Bee tab found.";
      return;
    }

    chrome.tabs.sendMessage(
      tabId,
      { type: "solve", payload: { action } },
      (response) => {
        if (chrome.runtime.lastError) {
          status.textContent = "Unable to contact the Spelling Bee tab.";
          return;
        }

        if (response?.error) {
          status.textContent = response.error;
          return;
        }

        const results = document.getElementById("results");
        const words = response?.valid || [];
        const pangrams = response?.pangrams || [];
        results.value = words.join("\n");
        status.textContent = `Found ${words.length} words, ${pangrams.length} pangram(s).`;
      }
    );
  });
}

document.getElementById("solve").addEventListener("click", () => requestSolve("solve"));
document.getElementById("fill").addEventListener("click", () => requestSolve("fill"));
