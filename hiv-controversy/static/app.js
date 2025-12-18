/**
 * HIV Controversy Knowledge Graph - Query Interface JavaScript
 *
 * Handles:
 * - Loading Cypher query examples
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
const exampleDescription = document.getElementById('example-description');
const queryInput = document.getElementById('query-input');
const submitButton = document.getElementById('submit-button');
const clearButton = document.getElementById('clear-button');
const statsButton = document.getElementById('stats-button');
const responseSection = document.getElementById('response-section');
const errorSection = document.getElementById('error-section');
const responseOutput = document.getElementById('response-output');
const errorOutput = document.getElementById('error-output');
const responseStatus = document.getElementById('response-status');
const responseCount = document.getElementById('response-count');
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
    statsButton.addEventListener('click', handleStats);

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
        exampleDescription.textContent = '';
        hideResponse();
        hideError();
        return;
    }

    currentExample = examples[selectedIndex];
    queryInput.value = currentExample.query;
    exampleDescription.textContent = currentExample.description;
    hideResponse();
    hideError();
}

/**
 * Handle query submission
 */
async function handleSubmit() {
    const query = queryInput.value.trim();

    if (!query) {
        showError('Please enter a Cypher query');
        return;
    }

    hideError();
    hideResponse();
    setLoading(true);

    try {
        const startTime = performance.now();

        // Execute Cypher query via the API
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
            }),
        });

        const endTime = performance.now();
        const executionTime = Math.round(endTime - startTime);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Show response
        showResponse(data, executionTime);

    } catch (error) {
        console.error('Query execution failed:', error);
        showError(`Query failed: ${error.message}`);
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
    exampleDescription.textContent = '';
    currentExample = null;
    hideResponse();
    hideError();
}

/**
 * Handle stats button
 */
async function handleStats() {
    hideError();
    hideResponse();
    setLoading(true);

    try {
        const startTime = performance.now();

        const response = await fetch('/stats');

        const endTime = performance.now();
        const executionTime = Math.round(endTime - startTime);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Format stats nicely
        const formattedData = {
            message: 'Graph Statistics',
            ...data
        };

        showResponse({
            results: [formattedData],
            count: 1,
            error: null
        }, executionTime);

    } catch (error) {
        console.error('Failed to fetch stats:', error);
        showError(`Failed to fetch stats: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

/**
 * Show response
 */
function showResponse(data, executionTime) {
    responseSection.style.display = 'block';

    // Update status badge
    if (data.error) {
        responseStatus.textContent = 'Error';
        responseStatus.className = 'status-badge status-error';
    } else {
        responseStatus.textContent = 'Success';
        responseStatus.className = 'status-badge status-success';
    }

    // Update count badge
    responseCount.textContent = `${data.count || 0} result${(data.count || 0) === 1 ? '' : 's'}`;
    responseCount.className = 'count-badge';

    // Update time badge
    responseTime.textContent = `${executionTime}ms`;
    responseTime.className = 'time-badge';

    // Format and display results
    responseOutput.textContent = JSON.stringify(data, null, 2);

    // Apply syntax highlighting
    if (window.Prism) {
        Prism.highlightElement(responseOutput);
    }

    // Scroll to response
    responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Show error
 */
function showError(message) {
    errorSection.style.display = 'block';
    errorOutput.textContent = message;

    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide response
 */
function hideResponse() {
    responseSection.style.display = 'none';
}

/**
 * Hide error
 */
function hideError() {
    errorSection.style.display = 'none';
}

/**
 * Set loading state
 */
function setLoading(loading) {
    const btnText = submitButton.querySelector('.btn-text');
    const btnSpinner = submitButton.querySelector('.btn-spinner');

    if (loading) {
        submitButton.disabled = true;
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline';
    } else {
        submitButton.disabled = false;
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
