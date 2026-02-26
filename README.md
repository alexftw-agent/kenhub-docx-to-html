# Kenhub DOCX to HTML Converter

A standalone web tool that converts DOCX files (exported from Google Docs) into clean HTML formatted for the Kenhub admin interface.

## Features

- **Drag & drop** file upload interface
- **Real-time conversion** from DOCX to clean admin HTML
- **Preview panel** to visually verify output
- **Copy to clipboard** functionality
- **Metadata extraction** (title, description, SEO fields)
- **Content type detection** (article vs study unit)
- **Warning system** for manual actions needed

## Transformation Rules

The converter follows specific rules derived from sample content pairs:

- Converts DOCX paragraph styles to appropriate HTML headings
- Handles bold/italic formatting with `<strong>`/`<em>` tags
- Detects and converts lists (numbered and bulleted)
- Processes tables with proper structure and formatting
- Identifies special markers for widgets ([Video:], [Table of Contents], etc.)
- Applies content-specific wrappers (study units vs articles)
- Extracts metadata from document properties

See `TRANSFORM_RULES.md` for detailed conversion logic.

## Tech Stack

- **Backend**: Python FastAPI
- **DOCX Processing**: python-docx + lxml
- **Frontend**: Vanilla HTML/CSS/JS with Inter font
- **Deployment**: Railway + Docker

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run locally:
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

3. Open http://localhost:8080

## Deployment

Deploy to Railway:

```bash
railway init
railway up --detach
```

## Testing

Test with the sample files in `samples/` directory. Upload a sample DOCX and compare the output structure to the corresponding target HTML.

## Note

The converter outputs clean HTML structure but does not generate:
- Interactive links (added manually in admin)
- Specific widget IDs (assigned in admin)
- Final styling (handled by admin CSS)

This tool focuses on content structure and formatting conversion.