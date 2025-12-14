/**
 * Medical Literature Graph API - Demo UI JavaScript
 * 
 * Handles:
 * - Loading examples from examples.json
 * - Populating the dropdown selector
 * - Submitting queries to the API
 * - Displaying formatted responses
 * - Error handling
 */

// State
let examples = [];
let currentExample = null;

// DOM Elements
const exampleSelect = document.getElementById('example-select');
const queryInput = document.getElementById('query-input');
const submitButton = document.getElementById('submit-button');
const clearButton = document.getElementById('clear-button');
const formatButton = document.getElementById('format-button');
const responseSection = document.getElementById('response-section');
const errorSection = document.getElementById('error-section');
const responseOutput = document.getElementById('response-output');
const errorOutput = document.getElementById('error-output');
const responseStatus = document.getElementById('response-status');
const responseTime = document.getElementById('response-time');

/**
 * Initialize the application
 */
async function init() {
    try {
        await loadExamples();
        populateExampleSelector();
        attachEventListeners();
    } catch (error) {
        console.error('Failed to initialize:', error);
        showError('Failed to load examples. Please refresh the page.');
    }
}

/**
 * Load examples from examples.json
 */
async function loadExamples() {
    try {
        const response = await fetch('/static/examples.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        examples = await response.json();
        console.log(`Loaded ${examples.length} examples`);
    } catch (error) {
        console.error('Error loading examples:', error);
        throw error;
    }
}

/**
 * Populate the example selector dropdown
 */
function populateExampleSelector() {
    examples.forEach((example, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = example.title;
        exampleSelect.appendChild(option);
    });
}

/**
 * Attach event listeners
 */
function attachEventListeners() {
    exampleSelect.addEventListener('change', handleExampleSelect);
    submitButton.addEventListener('click', handleSubmit);
    clearButton.addEventListener('click', handleClear);
    formatButton.addEventListener('click', handleFormat);
    
    // Allow Ctrl+Enter or Cmd+Enter to submit
    queryInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            handleSubmit();
        }
    });
}

/**
 * Handle example selection
 */
function handleExampleSelect() {
    const selectedIndex = exampleSelect.value;
    
    if (selectedIndex === '') {
        currentExample = null;
        queryInput.value = '';
        hideResponse();
        hideError();
        return;
    }
    
    currentExample = examples[selectedIndex];
    queryInput.value = JSON.stringify(currentExample.query, null, 2);
    hideResponse();
    hideError();
}

/**
 * Handle query submission
 */
async function handleSubmit() {
    const queryText = queryInput.value.trim();
    
    if (!queryText) {
        showError('Please enter or select a query.');
        return;
    }
    
    // Parse and validate JSON
    let query;
    try {
        query = JSON.parse(queryText);
    } catch (error) {
        showError(`Invalid JSON: ${error.message}`);
        return;
    }
    
    // Show loading state
    setLoading(true);
    hideResponse();
    hideError();
    
    try {
        const startTime = performance.now();
        
        const response = await fetch('/api/v1/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(query)
        });
        
        const endTime = performance.now();
        const responseTime = Math.round(endTime - startTime);
        
        const data = await response.json();
        
        if (response.ok) {
            showResponse(data, responseTime);
        } else {
            showError(`HTTP ${response.status}: ${data.message || 'Request failed'}`);
        }
    } catch (error) {
        showError(`Network error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

/**
 * Handle clear button
 */
function handleClear() {
    exampleSelect.value = '';
    queryInput.value = '';
    currentExample = null;
    hideResponse();
    hideError();
}

/**
 * Handle format button - prettify JSON
 */
function handleFormat() {
    const queryText = queryInput.value.trim();
    
    if (!queryText) {
        return;
    }
    
    try {
        const query = JSON.parse(queryText);
        queryInput.value = JSON.stringify(query, null, 2);
    } catch (error) {
        showError(`Cannot format invalid JSON: ${error.message}`);
    }
}

/**
 * Show response
 */
function showResponse(data, responseTime) {
    hideError();
    
    responseStatus.textContent = data.status === 'success' ? '✓ Success' : '⚠ Warning';
    responseStatus.className = data.status === 'success' ? 'status-badge success' : 'status-badge warning';
    responseTime.textContent = `Response time: ${responseTime}ms`;
    
    // Format and display the response
    const formattedJson = JSON.stringify(data, null, 2);
    responseOutput.textContent = formattedJson;
    
    // Apply syntax highlighting
    if (typeof Prism !== 'undefined') {
        Prism.highlightElement(responseOutput);
    }
    
    responseSection.style.display = 'block';
    
    // Scroll to response
    responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Show error
 */
function showError(message) {
    hideResponse();
    
    errorOutput.textContent = message;
    errorSection.style.display = 'block';
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide response section
 */
function hideResponse() {
    responseSection.style.display = 'none';
}

/**
 * Hide error section
 */
function hideError() {
    errorSection.style.display = 'none';
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    const btnText = submitButton.querySelector('.btn-text');
    const btnSpinner = submitButton.querySelector('.btn-spinner');
    
    if (isLoading) {
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline';
    } else {
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
