# Browser-Based Demo UI

This directory contains a browser-based demo interface for the Medical Literature Graph API mini server.

## Features

- **Interactive Query Builder**: Select from 26+ pre-built query examples
- **Live Query Editor**: Edit and customize JSON queries in real-time
- **Formatted Responses**: JSON responses with syntax highlighting
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Clear error messages for invalid queries

## Files

- `index.html` - Main HTML interface
- `styles.css` - Styling and responsive design
- `app.js` - JavaScript application logic
- `examples.json` - Generated examples from EXAMPLES.md (auto-generated)

## Usage

### Starting the Server

```bash
cd tests/mini_server
python server.py
```

The server will start on `http://localhost:8000/`

### Accessing the UI

Open your browser and navigate to:
- **Demo UI**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Examples API**: http://localhost:8000/api/v1/examples

### Using the Interface

1. **Select an Example**: Choose from the dropdown menu
2. **Review the Query**: The JSON query will populate in the text area
3. **Edit (Optional)**: Modify the query as needed
4. **Execute**: Click "Execute Query" to send the request
5. **View Response**: See the formatted JSON response below

### Buttons

- **Execute Query**: Submit the query to the API
- **Clear**: Reset the form
- **Format JSON**: Pretty-print the JSON in the text area

### Keyboard Shortcuts

- `Ctrl+Enter` or `Cmd+Enter`: Execute the query

## Regenerating Examples

If you update `client/curl/EXAMPLES.md`, regenerate the examples file:

```bash
cd tests/mini_server
python examples_parser.py
```

This will update `static/examples.json` with the latest examples.

## Technical Details

### Architecture

```
Browser → index.html → app.js → /api/v1/query → FastAPI → Query Executor
                              ↓
                        examples.json (loaded on init)
```

### Dependencies

**Python** (server-side):
- FastAPI
- Uvicorn

**JavaScript** (client-side):
- Vanilla JavaScript (no frameworks)
- Prism.js (syntax highlighting, loaded from CDN)

### API Endpoints Used

- `POST /api/v1/query` - Execute graph queries
- `GET /api/v1/examples` - Get parsed examples
- `GET /api/v1/stats` - Get graph statistics

## Development

### Making Changes

1. Edit HTML/CSS/JS files in `static/`
2. The server will auto-reload (using uvicorn's `--reload` flag)
3. Refresh your browser to see changes

### Adding New Examples

1. Add examples to `client/curl/EXAMPLES.md`
2. Run `python examples_parser.py` to regenerate
3. Refresh the browser - new examples will appear in dropdown

## Screenshots

The UI includes:
- Clean gradient header with API branding
- Informative "About This API" section
- Dropdown selector with all available examples
- Syntax-highlighted JSON editor
- Response display with success/error indicators
- Mobile-responsive design

## Browser Compatibility

Tested on:
- Chrome/Chromium
- Firefox
- Safari
- Edge

Requires modern browser with ES6+ support.
