# 🐙⚡ OctoCal

**Never miss an Octopus Energy free electricity session!**

OctoCal automatically scrapes the Octopus Energy website for free electricity slots, creates an iCal calendar file, and sends notifications via Apprise.

🔗 **Live Calendar**: https://evenwebb.github.io/OctoCal/

## Features

- 🐙 Scrapes https://octopus.energy/free-electricity/ for upcoming free electricity sessions
- 📅 Generates iCal (.ics) calendar file with GMT timezone
- 🔔 Configurable calendar alarms (1 day before, 15 minutes before, etc.)
- 🧹 Auto-cleanup of old sessions (configurable days to keep, default 7 days)
- 📱 Optional Apprise notifications (Discord, Telegram, Email, Slack, and many more)
- ⚙️ GitHub Actions ready - automated hourly scraping with zero maintenance
- 🌐 Beautiful GitHub Pages website for easy calendar subscription
- 🔄 Separate scrape/notification intervals for reliable notifications
- 💾 Persistent state tracking to avoid duplicate notifications
- 🎨 Clean, refactored, and optimized code
- 📜 Open source under GNU GPL v3

## Two Ways to Use

1. **GitHub Actions + Pages (Recommended)**: Fork the repo, enable Actions, get a public calendar URL that auto-updates hourly
2. **Local/Self-Hosted**: Run on your own machine with full control and custom notifications

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the example configuration:
```bash
cp config.yaml.example config.yaml
```

4. Edit `config.yaml` and configure your settings:
   - Add your Apprise notification URL(s)
   - Adjust notification timing
   - Set check interval

## Configuration

Edit `config.yaml` to customize:

- **Scraper settings**: URL and check interval
- **iCal settings**: Output directory, filename, timezone
- **Notifications**: Apprise URLs, timing (upcoming hours, start/end notifications)
- **Logging**: Log level and file location

### Apprise URLs

Apprise supports many notification services. Examples:

- **Discord**: `discord://webhook_id/webhook_token`
- **Telegram**: `tgram://bot_token/chat_id`
- **Email**: `mailto://user:password@domain.com`
- **Slack**: `slack://token_a/token_b/token_c`

See [Apprise documentation](https://github.com/caronc/apprise) for more services.

## GitHub Actions Deployment (Recommended)

The easiest way to use this is via **GitHub Actions** with automatic deployment to **GitHub Pages**. Your calendar will be publicly accessible and auto-update every hour!

### Quick Setup

1. **Fork this repository** on GitHub

2. **Update the HTML file** with your GitHub info (if forking):
   - Edit `gh-pages-src/index.html`
   - Replace `evenwebb` with your GitHub username
   - Replace `OctoCal` with your repository name (or keep it as OctoCal!)
   - Replace `brass-okapi-797` with your Octopus Energy referral code (or remove the referral section)

3. **Enable GitHub Pages**:
   - Go to repo Settings → Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `(root)`
   - Save

4. **Run the workflow**:
   - Go to Actions tab
   - Click "Scrape Octopus Energy Free Electricity"
   - Click "Run workflow"

5. **Access your calendar**:
   - Visit: `https://[your-username].github.io/[your-repo-name]/`
   - Subscribe to the calendar from the webpage!

> **Note**: The original OctoCal is live at https://evenwebb.github.io/OctoCal/ if you just want to use it without forking!

### How It Works

- **Automatic scraping**: Runs every hour via GitHub Actions cron schedule
- **No config needed**: Automatically uses `config.yaml.example`
- **GitHub Pages**: Deploys to `gh-pages` branch with a beautiful webpage
- **One-click subscribe**: Users can add the calendar to Apple Calendar, Google Calendar, etc.

### Default Settings for GitHub Actions

When running on GitHub Actions, the script automatically:
- Uses `config.yaml.example` (no need to create `config.yaml`)
- Runs in single-run mode (scrape once and exit)
- Sets calendar alarms for 1 day before and 15 minutes before
- Disables Apprise notifications (use calendar alarms instead)

## Local Usage

Run the scraper locally:

```bash
python main.py
```

The scraper will:
1. Check for new free electricity sessions
2. Update the iCal file in the `output` directory
3. Send notifications based on your configuration
4. Continue running and checking at the configured interval

### Command Line Options

```bash
# Run once and exit (useful for cron jobs)
python main.py --single-run

# Use a different config file
python main.py --config my-config.yaml

# Combine options
python main.py --single-run --config my-config.yaml
```

### Running as a Service

For continuous operation, consider running as a systemd service (Linux) or using a process manager like `supervisor`.

## Project Structure

**Application Code (don't edit these):**
- `main.py` - Main entry point, configuration loader, and monitoring loop
- `octopus_scraper.py` - Web scraper for Octopus Energy website
- `session_parser.py` - Parser for session date/time strings
- `ical_generator.py` - iCal file generator
- `notifier.py` - Apprise notification handler

**Configuration (edit this):**
- `config.yaml` - Your settings (copy from config.yaml.example)

**Output:**
- `output/` - Generated iCal files, logs, and state

## Output

- **iCal file**: `output/octopus_free_electricity.ics` - Import into your calendar app
- **Log file**: `output/octopus_scraper.log` - Application logs
- **State file**: `output/state.json` - Tracks seen sessions and sent notifications

## License

MIT
