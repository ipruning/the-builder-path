/**
 * Copy text from an element to the clipboard
 * @param {string} elementId - The ID of the element containing text to copy
 */
function copyToClipboard(elementId) {
  const text = document.getElementById(elementId).innerText;

  // Method 1: Use navigator.clipboard API (modern browsers)
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => {
        updateCopyButtonText('copy-btn-' + elementId);
      })
      .catch(err => {
        console.error('Failed to copy using navigator.clipboard:', err);
        fallbackCopyMethod(text, 'copy-btn-' + elementId);
      });
  } else {
    // Method 2: Fallback to textarea method if navigator.clipboard is not available
    fallbackCopyMethod(text, 'copy-btn-' + elementId);
  }
}

/**
 * Fallback copy method using document.execCommand
 * @param {string} text - The text to copy
 * @param {string} buttonId - The ID of the button to update
 */
function fallbackCopyMethod(text, buttonId) {
  // Create temporary textarea element
  const textArea = document.createElement("textarea");
  textArea.value = text;

  // Make it invisible to user
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    // Try to execute copy command
    const successful = document.execCommand('copy');
    if (successful) {
      updateCopyButtonText(buttonId);
    } else {
      console.error('execCommand copy failed');
      alert('Copy failed, please copy manually');
    }
  } catch (err) {
    console.error('execCommand error:', err);
    alert('Copy failed, please copy manually');
  }

  document.body.removeChild(textArea);
}

/**
 * Update the copy button text to indicate success
 * @param {string} buttonId - The ID of the button to update
 */
function updateCopyButtonText(buttonId) {
  const btn = document.getElementById(buttonId);
  const originalText = btn.innerText;
  btn.innerText = "复制成功";
  setTimeout(() => {
    btn.innerText = originalText;
  }, 2000);
} 
