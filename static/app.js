// Global state
let selectedFile = null;
let conversionResult = null;

// DOM elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const convertButton = document.getElementById('convertButton');
const resultsSection = document.getElementById('resultsSection');
const htmlOutput = document.getElementById('htmlOutput');
const htmlPreview = document.getElementById('htmlPreview');
const metadataOutput = document.getElementById('metadataOutput');
const copyButton = document.getElementById('copyButton');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    hljs.highlightAll();
});

function initializeEventListeners() {
    // File input handling
    fileInput.addEventListener('change', handleFileSelection);
    
    // Drop zone handling
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleFileDrop);
    dropZone.addEventListener('dragleave', handleDragLeave);
    
    // Convert button
    convertButton.addEventListener('click', handleConversion);
    
    // Copy button
    copyButton.addEventListener('click', handleCopyToClipboard);
    
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
    });
}

function handleFileSelection(event) {
    const file = event.target.files[0];
    selectFile(file);
}

function handleDragOver(event) {
    event.preventDefault();
    dropZone.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    dropZone.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        selectFile(files[0]);
    }
}

function selectFile(file) {
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.docx')) {
        showError('Please select a DOCX file.');
        return;
    }
    
    selectedFile = file;
    updateDropZoneWithFile(file);
    convertButton.disabled = false;
}

function updateDropZoneWithFile(file) {
    const dropZoneContent = dropZone.querySelector('.drop-zone-content');
    dropZoneContent.innerHTML = `
        <div class="file-info">
            <strong>📄 ${file.name}</strong><br>
            <small>${formatFileSize(file.size)} • ${file.type || 'DOCX document'}</small>
        </div>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function handleConversion() {
    if (!selectedFile) return;
    
    setLoadingState(true);
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }
        
        conversionResult = await response.json();
        displayResults(conversionResult);
        
    } catch (error) {
        showError(`Conversion failed: ${error.message}`);
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(loading) {
    const buttonText = convertButton.querySelector('.button-text');
    const buttonSpinner = convertButton.querySelector('.button-spinner');
    
    if (loading) {
        buttonText.style.display = 'none';
        buttonSpinner.style.display = 'inline';
        convertButton.disabled = true;
    } else {
        buttonText.style.display = 'inline';
        buttonSpinner.style.display = 'none';
        convertButton.disabled = !selectedFile;
    }
}

function displayResults(result) {
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Update HTML output
    htmlOutput.textContent = result.html;
    hljs.highlightElement(htmlOutput);
    
    // Update preview
    htmlPreview.innerHTML = result.html;
    
    // Update metadata
    displayMetadata(result.metadata, result.warnings);
    
    // Switch to HTML tab
    switchTab('html');
}

function displayMetadata(metadata, warnings) {
    const metadataHtml = `
        <div class="metadata-grid">
            <div class="metadata-card">
                <h4>Content Information</h4>
                <p><strong>Title:</strong> ${metadata.title || 'Not specified'}</p>
                <p><strong>Type:</strong> ${metadata.type}</p>
                <p><strong>Description:</strong> ${metadata.description || 'Not specified'}</p>
            </div>
            <div class="metadata-card">
                <h4>SEO Information</h4>
                <p><strong>SEO Title:</strong> ${metadata.seo_title || 'Not specified'}</p>
                <p><strong>SEO Description:</strong> ${metadata.seo_description || 'Not specified'}</p>
            </div>
        </div>
        
        ${warnings && warnings.length > 0 ? `
            <div class="warnings-section">
                <h4>⚠️ Manual Actions Required</h4>
                ${warnings.map(warning => `
                    <div class="warning-item">${warning}</div>
                `).join('')}
            </div>
        ` : ''}
    `;
    
    metadataOutput.innerHTML = metadataHtml;
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

async function handleCopyToClipboard() {
    if (!conversionResult || !conversionResult.html) return;
    
    try {
        await navigator.clipboard.writeText(conversionResult.html);
        
        // Visual feedback
        const originalText = copyButton.textContent;
        copyButton.textContent = '✓ Copied!';
        copyButton.classList.add('copied');
        
        setTimeout(() => {
            copyButton.textContent = originalText;
            copyButton.classList.remove('copied');
        }, 2000);
        
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        
        // Fallback: select text
        const range = document.createRange();
        range.selectNode(htmlOutput);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        
        copyButton.textContent = '📋 Text Selected';
        setTimeout(() => {
            copyButton.textContent = '📋 Copy to Clipboard';
        }, 2000);
    }
}

function showError(message) {
    // Remove existing error messages
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Create new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // Insert after upload section
    const uploadSection = document.querySelector('.upload-section');
    uploadSection.insertAdjacentElement('afterend', errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}