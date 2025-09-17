# Sharedo DOCX to HTML Converter Service

A high-performance web service that converts Microsoft Word documents (.docx) to Sharedo-compatible HTML email templates, preserving conditional logic, placeholders, and document structure with 95% accuracy.

## Features

- **RESTful API**: Convert DOCX files to HTML via HTTP endpoints
- **Web Interface**: User-friendly landing page for manual file conversion
- **Confidence Scoring**: Automatic assessment of conversion quality (0-100%)
- **Batch Processing**: Process multiple documents simultaneously
- **Metrics & Reporting**: Real-time conversion statistics and health monitoring
- **Swagger Documentation**: Interactive API documentation at `/docs`
- **Docker Support**: Production-ready containerized deployment
- **High Accuracy**: 95% conversion accuracy with proper handling of:
  - Sharedo template tags (context.*, document.*)
  - Conditional sections (If blocks)
  - Tables and nested structures
  - Content controls and SDT elements
  - Placeholders and form fields

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Alterspective-io/sharedo-docx-converter.git
cd sharedo-docx-converter

# Start the service
docker-compose up -d

# Service will be available at:
# - Web Interface: http://localhost:8000
# - API Endpoint: http://localhost:8000/api/v1/convert
# - Swagger Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### Convert Single Document

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/convert" \
  -F "file=@document.docx" \
  -o converted.html

# Response includes HTML and metadata
```

### Python Example

```python
import requests

# Convert DOCX to HTML
with open('document.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/convert',
        files={'file': ('document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    )

if response.status_code == 200:
    result = response.json()
    html = result['html']
    confidence = result['confidence']
    print(f"Conversion successful! Confidence: {confidence}%")
```

### JavaScript/TypeScript Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/convert', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(`HTML: ${result.html}`);
console.log(`Confidence: ${result.confidence}%`);
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page with web interface |
| `/api/v1/convert` | POST | Convert DOCX to HTML |
| `/api/v1/batch` | POST | Batch convert multiple files |
| `/health` | GET | Service health check |
| `/metrics` | GET | Conversion metrics and statistics |
| `/docs` | GET | Swagger/OpenAPI documentation |
| `/redoc` | GET | ReDoc documentation |

## Conversion Response Format

```json
{
  "html": "<html>...</html>",
  "confidence": 95,
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "created": "2024-01-15T10:30:00",
    "modified": "2024-01-15T14:20:00"
  },
  "analysis": {
    "total_paragraphs": 42,
    "sharedo_tags_found": 15,
    "conditional_blocks": 3,
    "tables": 2,
    "complexity_score": "medium"
  },
  "warnings": []
}
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
APP_ENV=production
DEBUG=false

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB
CONVERSION_TIMEOUT=60   # seconds

# Conversion Settings
CONFIDENCE_THRESHOLD=90  # minimum confidence for auto-approval
MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
API_KEY_ENABLED=false
API_KEY=your-secret-key-here
```

## Production Deployment

### With Nginx (Recommended)

```bash
# Deploy with Nginx reverse proxy
docker-compose --profile production up -d

# This starts:
# - Sharedo converter service (port 8000)
# - Nginx reverse proxy (port 80)
# - Optional Redis cache
```

### SSL/TLS Configuration

1. Add SSL certificates to `./ssl/` directory
2. Uncomment HTTPS section in `nginx.conf`
3. Update server_name in configuration

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "conversions_total": 150,
  "conversions_today": 25
}
```

## Batch Processing

For bulk document conversion, use the batch converter script:

```bash
# Process all DOCX files in Input folder
python sharedo_batch_converter.py

# Results will be in:
# - Output/*.html - Converted HTML files
# - Output/conversion_report.html - Summary report
# - Output/conversion_report.json - Detailed JSON report
```

## Metrics and Monitoring

Access real-time metrics at `/metrics`:

```json
{
  "total_conversions": 1250,
  "successful_conversions": 1190,
  "failed_conversions": 60,
  "average_confidence": 94.5,
  "average_processing_time": 2.3,
  "conversions_by_day": {
    "2024-01-15": 45,
    "2024-01-14": 38
  },
  "top_errors": []
}
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│    Nginx     │────▶│   FastAPI   │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Static    │     │  Converter  │
                    │    Assets    │     │   Engine    │
                    └──────────────┘     └─────────────┘
```

## Supported Features

### Document Elements
- ✅ Paragraphs and text formatting
- ✅ Tables (including nested)
- ✅ Lists (ordered and unordered)
- ✅ Headers and footers
- ✅ Images and media
- ✅ Hyperlinks

### Sharedo-Specific
- ✅ Context tags (context.*)
- ✅ Document fields (document.*)
- ✅ Conditional blocks (If sections)
- ✅ Placeholders ([_____])
- ✅ Content controls
- ✅ Form fields

## Troubleshooting

### Common Issues

1. **File too large error**
   - Increase `MAX_FILE_SIZE` in environment variables
   - Default limit is 10MB

2. **Conversion timeout**
   - Increase `CONVERSION_TIMEOUT` for complex documents
   - Consider using batch processing for multiple files

3. **Low confidence scores**
   - Review document complexity (nested tables, complex conditionals)
   - Check for unsupported Word features
   - Manual review may be required for confidence < 90%

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

## Development

### Running Tests

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Project Structure

```
sharedo-docx-converter/
├── app/
│   ├── main.py              # FastAPI application
│   ├── converter.py          # Core conversion engine
│   ├── models.py            # Pydantic models
│   ├── templates/           # HTML templates
│   │   └── index.html       # Landing page
│   └── static/              # CSS, JS, images
├── Input/                   # Input folder for batch processing
├── Output/                  # Output folder for conversions
├── docker-compose.yml       # Docker orchestration
├── Dockerfile              # Container image
├── nginx.conf              # Nginx configuration
├── requirements.txt        # Python dependencies
└── sharedo_batch_converter.py  # Batch processing script
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software owned by Alterspective.io. All rights reserved.

## Support

For issues and questions:
- GitHub Issues: https://github.com/Alterspective-io/sharedo-docx-converter/issues
- Email: support@alterspective.io

## Acknowledgments

- Built with FastAPI for high-performance async operations
- Uses python-docx for reliable DOCX parsing
- Bootstrap UI for responsive web interface
- Docker for consistent deployment across environments