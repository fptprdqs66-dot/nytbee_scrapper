/**
 * Background service worker for NYTBee Helper.
 * Safari requires a background script in the extension bundle for messaging.
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log("NYTBee Helper installed.");
});
