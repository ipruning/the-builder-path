/**
 * Updates the file name display when a file is selected and uploads the file
 * @param {HTMLInputElement} input - The file input element
 */
function updateFileName(input) {
  const fileNameDisplay = document.getElementById('file-name-display');
  const uploadStatusElement = document.getElementById('upload-status');
  const extractButton = document.querySelector('.btn-extract');
  const resultsSection = document.querySelector('.results-section');

  if (input.files && input.files.length > 0) {
    const file = input.files[0];
    fileNameDisplay.textContent = file.name;

    // Enable extract button when new file is selected
    if (extractButton) {
      extractButton.disabled = false;
    }

    // Only upload PDF files
    if (file.type === 'application/pdf') {
      uploadPDF(file);
    }
  } else {
    fileNameDisplay.textContent = '';
    if (uploadStatusElement) {
      uploadStatusElement.textContent = '';
      uploadStatusElement.style.display = 'none';
    }
    // Clear the hidden temp filename field
    const tempFilenameInput = document.getElementById('temp_filename');
    if (tempFilenameInput) {
      tempFilenameInput.value = '';
    }

    // Hide results section when no file is selected
    if (resultsSection) {
      resultsSection.classList.remove('active');
    }

    // Disable extract button when no file is selected
    if (extractButton) {
      extractButton.disabled = true;
    }
  }
}

/**
 * Uploads a PDF file immediately after selection
 * @param {File} file - The PDF file to upload
 */
function uploadPDF(file) {
  const uploadStatusElement = document.getElementById('upload-status');
  const extractButton = document.querySelector('.btn-extract');
  if (!uploadStatusElement) return;

  // Disable extract button during upload
  if (extractButton) {
    extractButton.disabled = true;
  }

  uploadStatusElement.textContent = '上传中...';
  uploadStatusElement.className = 'upload-status uploading';
  uploadStatusElement.style.display = 'flex';

  const formData = new FormData();
  formData.append('pdf_file', file);

  const xhr = new XMLHttpRequest();

  // Setup progress monitoring
  xhr.upload.addEventListener('progress', (event) => {
    if (event.lengthComputable) {
      const percentComplete = Math.round((event.loaded / event.total) * 100);
      uploadStatusElement.textContent = `上传中：${percentComplete}%`;
    }
  });

  xhr.addEventListener('load', () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const response = JSON.parse(xhr.responseText);
      uploadStatusElement.textContent = '上传完成';
      uploadStatusElement.className = 'upload-status success';
      uploadStatusElement.style.display = 'flex';

      // Store the temp filename in a hidden input for later use
      const tempFilenameInput = document.getElementById('temp_filename');
      if (tempFilenameInput && response.temp_filename) {
        tempFilenameInput.value = response.temp_filename;
      }

      const originalFilenameInput = document.createElement('input');
      originalFilenameInput.type = 'hidden';
      originalFilenameInput.name = 'original_filename';
      originalFilenameInput.value = response.original_filename;
      document.querySelector('form').appendChild(originalFilenameInput);

      // Enable extract button after successful upload
      if (extractButton) {
        extractButton.disabled = false;
      }
    } else {
      uploadStatusElement.textContent = '上传失败';
      uploadStatusElement.className = 'upload-status error';
      uploadStatusElement.style.display = 'flex';
      // Enable extract button on error to allow retry
      if (extractButton) {
        extractButton.disabled = false;
      }
    }
  });

  xhr.addEventListener('error', () => {
    uploadStatusElement.textContent = '上传出错';
    uploadStatusElement.className = 'upload-status error';
    uploadStatusElement.style.display = 'flex';
    // Enable extract button on error to allow retry
    if (extractButton) {
      extractButton.disabled = false;
    }
  });

  xhr.addEventListener('abort', () => {
    uploadStatusElement.textContent = '上传取消';
    uploadStatusElement.className = 'upload-status';
    uploadStatusElement.style.display = 'flex';
    // Enable extract button on abort to allow retry
    if (extractButton) {
      extractButton.disabled = false;
    }
  });

  xhr.open('POST', '/api/pdf/upload');
  xhr.send(formData);
}

// Add this function to update the processing status display
function updateProcessingStatus(status, progress) {
  const extractButton = document.querySelector('.btn-extract');
  const resultsSection = document.querySelector('.results-section');

  if (extractButton) {
    if (!extractButton.classList.contains('processing')) {
      extractButton.classList.add('processing');
    }
    extractButton.disabled = true;
    extractButton.innerHTML = `
      <div class="progress-fill" style="width: ${progress}%"></div>
      <div class="button-text">${progress}%</div>
    `;
  }

  // Show results section when processing starts
  if (resultsSection && !resultsSection.classList.contains('active')) {
    resultsSection.classList.add('active');
  }
}

// Add this function to disable extract button during processing
function disableExtractButton() {
  const extractButton = document.querySelector('.btn-extract');
  if (extractButton) {
    extractButton.disabled = true;
  }
}

// Add this function to enable extract button after processing
function enableExtractButton() {
  const extractButton = document.querySelector('.btn-extract');
  if (extractButton) {
    extractButton.disabled = false;
    extractButton.classList.remove('processing');
    extractButton.innerHTML = '<div class="button-text">提取</div>';
  }
} 
