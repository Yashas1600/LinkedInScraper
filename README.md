# LinkedIn Profile Scraper

A Python-based tool for scraping LinkedIn profiles using Selenium and undetected Chrome driver. This project includes both a scraper for extracting profile data and a fun guessing game to test your knowledge of the scraped profiles.

## Features

### Main Scraper (`main.py`)
- **Automated LinkedIn Login**: Uses your `li_at` session cookie for authentication
- **Two Scraping Modes**:
  - **Single Profile Mode**: Scrape a specific LinkedIn profile URL
  - **Multi-Name Search Mode**: Search for multiple people by name using Google search
- **Comprehensive Data Extraction**:
  - Full name and LinkedIn URL
  - Education (major/minor detection)
  - Work experiences (company, role, description)
- **Smart Profile Parsing**: Handles various LinkedIn profile layouts and formats
- **Secure Cookie Management**: Stores authentication securely in `.env` file

### Profile Guessing Game (`guess.py`)
- Interactive yes/no question game
- Uses scraped profile data to guess which person you're thinking of
- Focuses on work experience questions for better accuracy
- Handles contradictory answers and provides helpful feedback

<img width="805" height="245" alt="image" src="https://github.com/user-attachments/assets/ca37e96c-bc0b-41db-b8f6-4b9a45685267" />
<img width="795" height="469" alt="image" src="https://github.com/user-attachments/assets/471b8182-60b9-40f6-87cd-b43c64ef70ca" />



## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd LinkedInScraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome/Chromium**: Make sure you have Google Chrome installed on your system.

## Setup

### Getting Your LinkedIn Session Cookie (`li_at`)

1. **Login to LinkedIn** in your browser
2. **Open Developer Tools** (F12 or right-click → Inspect)
3. **Go to Application/Storage tab** → Cookies → `https://www.linkedin.com`
4. **Find the `li_at` cookie** and copy its value
5. **Save it securely** - the script will prompt you to enter it on first run

⚠️ **Important**: Keep your `li_at` cookie private and secure. It provides access to your LinkedIn account.

## Usage

### Scraping Profiles

Run the main scraper:

```bash
python main.py
```

You'll be prompted to choose between two modes:

#### Single Profile Mode
- Type `url` when prompted
- Enter a LinkedIn profile URL
- Results saved to `profile.json`

#### Multi-Name Search Mode
- Type `names` when prompted  
- Enter names separated by commas: `John Smith, Jane Doe, Bob Johnson`
- The script will search Google for each person's LinkedIn profile
- Results saved to `options.json`

### Playing the Guessing Game

After scraping multiple profiles:

```bash
python guess.py
```

The game will:
1. Load profiles from `options.json`
2. Ask you to think of one person
3. Ask 5 yes/no questions about work experience
4. Try to guess who you're thinking of!

## Command Line Options

### Main Scraper Options

```bash
python main.py --reset    # Clear saved credentials and re-prompt
```

## File Structure

```
LinkedInScraper/
├── main.py              # Main scraping script
├── guess.py             # Profile guessing game
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .env                # Your li_at cookie (created automatically)
├── profile.json        # Single profile results
└── options.json        # Multi-profile results
```

## How It Works

### Authentication
- Uses your LinkedIn session cookie (`li_at`) to bypass login
- Automatically validates the session before scraping
- Prompts for a new cookie if the current one expires

### Web Scraping
- Uses `undetected-chromedriver` to avoid detection
- Implements smart scrolling to load dynamic content
- Handles various LinkedIn profile layouts and structures
- Extracts structured data from HTML elements

### Data Extraction
- **Names**: Extracted from `<h1>` tags
- **Education**: Parsed from Education section with smart major/minor detection
- **Experience**: Extracts company, role, and description from experience cards
- **Text Normalization**: Cleans up LinkedIn's UI separators and duplicates

## Dependencies

- `selenium`: Web browser automation
- `undetected-chromedriver`: Chrome driver that avoids detection
- `python-dotenv`: Environment variable management
- `setuptools`: Python package management

## Troubleshooting

### Common Issues

1. **"Login failed"**: Your `li_at` cookie may have expired
   - Run with `--reset` flag to enter a new cookie
   - Make sure you're logged into LinkedIn in your browser

2. **Chrome driver issues**: 
   - Make sure Chrome is installed and up to date
   - The script auto-detects your Chrome version

3. **Profile not found**: 
   - Check that the LinkedIn URL is correct and public
   - Some profiles may be private or restricted

4. **Slow performance**:
   - The script includes delays to avoid being rate-limited
   - LinkedIn's dynamic loading can take time

### Rate Limiting
- The script includes built-in delays to respect LinkedIn's servers
- Avoid running multiple instances simultaneously
- If you encounter issues, wait a few minutes before retrying

## Legal and Ethical Considerations

⚠️ **Important Disclaimers**:

- **Respect LinkedIn's Terms of Service**: This tool is for educational purposes
- **Respect Privacy**: Only scrape public profiles and data you have permission to access  
- **Rate Limiting**: The script includes delays to avoid overwhelming LinkedIn's servers
- **Personal Use**: Intended for personal research and learning, not commercial data harvesting

## Contributing

Feel free to submit issues and pull requests to improve the scraper's functionality and reliability.

## License

This project is for educational purposes. Please respect LinkedIn's Terms of Service and applicable laws when using this tool.
