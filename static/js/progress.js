// static/js/progress.js
// Handles image preview, basic drag & drop hints, and form UX.

(() => {
  const logoInput = document.getElementById('logo-input');
  const productInput = document.getElementById('product-input');
  const logoPreview = document.getElementById('logo-preview');
  const productPreview = document.getElementById('product-preview');
  const form = document.getElementById('upload-form');
  const status = document.getElementById('status');
  const submitBtn = document.getElementById('submit-btn');
  const clearBtn = document.getElementById('clear-btn');

  function readAndPreview(file, imgEl) {
    if (!file) return;
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      imgEl.src = reader.result;
    });
    reader.readAsDataURL(file);
  }

  logoInput && logoInput.addEventListener('change', (ev) => {
    const f = ev.target.files[0];
    if (f) readAndPreview(f, logoPreview);
  });

  productInput && productInput.addEventListener('change', (ev) => {
    const f = ev.target.files[0];
    if (f) readAndPreview(f, productPreview);
  });

  // Basic drag-and-drop support for both inputs
  function enableDropForInput(inputEl, previewEl) {
    const parent = inputEl.closest('.preview-box');
    if (!parent) return;

    parent.addEventListener('dragover', (e) => {
      e.preventDefault();
      parent.style.borderColor = 'rgba(0,123,255,0.6)';
      parent.style.background = '#f8fbff';
    });
    parent.addEventListener('dragleave', (e) => {
      parent.style.borderColor = '';
      parent.style.background = '';
    });
    parent.addEventListener('drop', (e) => {
      e.preventDefault();
      parent.style.borderColor = '';
      parent.style.background = '';
      const file = e.dataTransfer.files[0];
      if (!file) return;
      // set the files of the input (works in most browsers)
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      inputEl.files = dataTransfer.files;
      readAndPreview(file, previewEl);
    });
  }

  enableDropForInput(logoInput, logoPreview);
  enableDropForInput(productInput, productPreview);

  // Show processing banner and disable submit
  form.addEventListener('submit', () => {
    status.style.display = 'block';
    submitBtn.disabled = true;
    submitBtn.innerText = 'Generating...';
  });

  // Clear previews (reset input and images)
  clearBtn.addEventListener('click', (e) => {
    e.preventDefault();
    logoInput.value = '';
    productInput.value = '';
    logoPreview.src = '/static/placeholder_logo.png';
    productPreview.src = '/static/placeholder_product.png';
    submitBtn.disabled = false;
    status.style.display = 'none';
    submitBtn.innerText = 'Generate Creatives';
  });

  // Optional: graceful fallback placeholder images
  // If placeholder images are missing, use inline blank data URI
  function ensurePlaceholder(imgEl, fallbackDataURI) {
    imgEl.addEventListener('error', () => {
      imgEl.src = fallbackDataURI;
    });
  }

  const blankDataURI = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23f5f5f5" width="100%25" height="100%25"/><text x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23999" font-size="20">Preview</text></svg>';
  ensurePlaceholder(logoPreview, blankDataURI);
  ensurePlaceholder(productPreview, blankDataURI);

})();
