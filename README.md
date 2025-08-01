# Delhi High Court Case Scraper

A comprehensive web scraper and Flask application for searching and retrieving case information from the Delhi High Court website.

## 🏛️ Court Information

**Target Court**: Delhi High Court (https://delhihighcourt.nic.in)
- **Jurisdiction**: High Court of Delhi, India
- **Case Types Supported**: 140+ case types including:
  - W.P.(C) - Writ Petition (Civil)
  - CRL.M.C. - Criminal Miscellaneous
  - O.M.P. (E) (COMM.) - Original Miscellaneous Petition (Commercial)
  - F.A.O. - First Appeal Original
  - And many more...

## 🚀 Features

- **Complete Case Type Support**: All 140+ case types available on Delhi High Court website
- **Automated CAPTCHA Handling**: Intelligent CAPTCHA extraction and validation
- **Multi-format Results**: Support for judgment tables and case listing tables
- **PDF Download Links**: Direct access to judgment documents
- **Responsive Web Interface**: User-friendly Flask-based frontend
- **Error Handling**: Comprehensive error detection and reporting

## 🛠️ Setup Steps

### Prerequisites
- Python 3.7 or higher
- Internet connection
- **Docker (Optional)**: For containerized deployment

### Option 1: Local Installation

1. **Clone or Download the Project**
   ```bash
   # If using git
   git clone <repository-url>
   cd "Code Data Fetcher"
   
   # Or download and extract the ZIP file
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The application should be running with the case search interface

### Option 2: Docker Deployment

#### Quick Start with Docker Compose (Recommended)
```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# Stop the application
docker-compose down
```

#### Manual Docker Commands
```bash
# Build the Docker image
docker build -t delhi-court-scraper .

# Run the container
docker run -d \
  --name delhi-court-scraper \
  -p 5000:5000 \
  -v $(pwd)/downloads:/app/downloads \
  delhi-court-scraper

# View logs
docker logs delhi-court-scraper

# Stop the container
docker stop delhi-court-scraper
```

#### Docker Features
- **Isolated Environment**: Runs in containerized environment
- **Easy Deployment**: Single command deployment
- **Persistent Downloads**: PDF files saved to host machine
- **Health Checks**: Automatic container health monitoring
- **Auto-restart**: Container restarts on failure


## 🔐 CAPTCHA Strategy

### How CAPTCHA is Handled

The Delhi High Court website uses a **text-based CAPTCHA** system to prevent automated access. Our scraper employs the following strategy:

#### 1. **CAPTCHA Detection**
- The scraper automatically detects the CAPTCHA element on the page
- CAPTCHA code is extracted from `<span id="captcha-code">` element
- No image processing required - text is directly available in HTML

#### 2. **CAPTCHA Extraction Process**
```python
# Step 2: Extract CAPTCHA code from HTML
captcha_element = soup.find('span', {'id': 'captcha-code'})
captcha_code = captcha_element.get_text(strip=True)
```

#### 3. **CAPTCHA Validation**
- **Validation Endpoint**: `/app/validateCaptcha`
- **Method**: XMLHttpRequest POST request
- **Headers**: Includes `X-Requested-With: XMLHttpRequest`
- **Payload**: `_token` and `captchaInput` fields

#### 4. **CAPTCHA Workflow**
1. **Access Site** → Get initial page with CAPTCHA
2. **Extract CAPTCHA** → Parse HTML for captcha code and security token
3. **Validate CAPTCHA** → Send AJAX request to validate captcha
4. **Submit Search** → Use validated session to search cases
5. **Parse Results** → Extract case data from response

#### 5. **Key Technical Details**
- **Session Management**: Maintains cookies across all requests
- **Security Token**: Extracts and uses `_token` for CSRF protection
- **User-Agent Spoofing**: Uses Chrome browser headers
- **Timeout Handling**: 30-second timeout for all requests

#### 6. **CAPTCHA Advantages**
- ✅ **No Image Processing**: Text-based CAPTCHA is directly readable
- ✅ **High Success Rate**: No OCR errors or image recognition failures
- ✅ **Fast Processing**: Instant extraction and validation
- ✅ **Reliable**: Consistent success across different sessions

## 📊 Usage

### Web Interface
1. Open `http://localhost:5000` in your browser
2. Select case type from the comprehensive dropdown (140+ options)
3. Enter case number (e.g., `11180`)
4. Enter year (e.g., `2025`)
5. Click "Search Cases"
6. View results with case details and PDF links

### Programmatic Usage
```python
from delhi_court_scraper import DelhiCourtScraper

scraper = DelhiCourtScraper()
result = scraper.search_case('CW', '11180', '2025')  # Using website code
print(result)
```

## 🗂️ Case Type Mapping

The application includes a comprehensive mapping system between user-friendly display names and website codes:

| Display Name | Website Code | Full Name |
|--------------|--------------|-----------|
| W.P.(C) | CW | Writ Petition (Civil) |
| CRL.M.C. | CRLMM | Criminal Miscellaneous |
| O.M.P. (E) (COMM.) | OMPCOMM | Original Miscellaneous Petition (Commercial) |
| F.A.O. | FAO | First Appeal Original |

*And 136+ more case types...*

## 📁 Project Structure

```
Code Data Fetcher/
├── app.py                    # Main Flask application
├── delhi_court_scraper.py    # Core scraper functionality
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker container configuration
├── docker-compose.yml       # Docker Compose configuration
├── .dockerignore           # Docker build exclusions
├── run_tests.py            # Full test suite runner
├── run_scraper_tests.py    # Simple scraper test runner
├── templates/
│   └── index.html           # Web interface template
├── tests/                   # Unit tests directory
│   ├── __init__.py         # Test package init
│   ├── test_scraper_simple.py # Simple scraper tests
├── downloads/               # PDF downloads directory
└── README.md               # This file
```

## 🔧 Technical Architecture

### Core Components
1. **Flask Web Application** (`app.py`)
   - RESTful API endpoints
   - Case type mapping system
   - Error handling and logging

2. **Scraper Engine** (`delhi_court_scraper.py`)
   - 5-step scraping process
   - Session management
   - CAPTCHA automation

3. **Frontend Interface** (`templates/index.html`)
   - Responsive design
   - Dynamic case type dropdown
   - Result display formatting

### Dependencies
- **Flask**: Web framework
- **Requests**: HTTP client library
- **BeautifulSoup4**: HTML parsing
- **Logging**: Error tracking and debugging

## ⚠️ Important Notes

### Legal Compliance
- This tool is for educational and research purposes
- Respect the website's terms of service
- Use responsibly and avoid excessive requests
- Consider implementing delays between requests

### Rate Limiting
- The scraper includes built-in delays
- Avoid running multiple concurrent instances
- Monitor for any rate limiting responses

### Data Accuracy
- Case information is scraped directly from official website
- PDF links provide access to original court documents
- Always verify critical information with official sources

## 🐛 Troubleshooting

### Common Issues

1. **"No cases found" Error**
   - Verify case number and year are correct
   - Ensure case type is properly selected
   - Check if case exists on the court website

2. **CAPTCHA Validation Failed**
   - Usually resolves automatically on retry
   - Check internet connection
   - Verify website accessibility

3. **Connection Timeout**
   - Check internet connectivity
   - Website may be temporarily unavailable
   - Try again after a few minutes

### Docker Issues

1. **Docker Build Fails**
   ```bash
   # Clean Docker cache and rebuild
   docker system prune -f
   docker-compose build --no-cache
   ```

2. **Container Won't Start**
   ```bash
   # Check logs for errors
   docker-compose logs delhi-court-scraper
   
   # Restart the service
   docker-compose restart
   ```

3. **Port Already in Use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "5001:5000"  # Use different host port
   ```

4. **Downloads Not Persisting**
   - Ensure downloads directory exists on host
   - Check volume mapping in docker-compose.yml
   - Verify container has write permissions

### Logging
The application generates detailed logs for debugging:
- Check console output for real-time information
- Review `app.log` file for persistent logging
