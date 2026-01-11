# 🐙⚡ OctoCal

**Never miss an Octopus Energy free electricity session!**

OctoCal automatically scrapes the Octopus Energy website for free electricity slots, creates an iCal calendar file, tracks session history with detailed statistics, and sends notifications via Apprise.

🔗 **Live Calendar with Calendar Reminders**: https://evenwebb.github.io/OctoCal/  
📊 **History & Statistics Page**: https://evenwebb.github.io/OctoCal/history.html

## Features

### Core Functionality
- 🐙 Scrapes https://octopus.energy/free-electricity/ for upcoming free electricity sessions
- 📅 Generates iCal (.ics) calendar file with GMT timezone
- 🔔 Configurable calendar alarms (1 day before, 15 minutes before, etc.)
- 🧹 Auto-cleanup of old sessions (configurable days to keep, default 7 days)
- 📱 Optional Apprise notifications (Discord, Telegram, Email, Slack, and many more)
- 💾 Persistent state tracking to avoid duplicate notifications

### History & Statistics
- 📊 **Complete session history** - Tracks all discovered free electricity sessions
- 📈 **Detailed statistics** - Total sessions, hours, averages, longest/shortest sessions
- 📅 **Monthly breakdown** - Sessions and hours per month with visual charts
- 🎯 **Additional insights** - Best month, day patterns, time patterns, frequency analysis
- 📊 **Interactive bar charts** - Visual representation of sessions per month (last 12 months)
- 🔍 **Lazy-loaded session list** - Efficient display of historic sessions with "Show More"
- 🆔 **Smart deduplication** - Prevents duplicate entries using session codes and timestamps

### Web Interface
- 🌐 **Beautiful GitHub Pages website** - Modern, responsive design with gradient styling
- 📱 **Upcoming sessions display** - See upcoming sessions directly on the main page
- 📊 **Dedicated history page** - Comprehensive statistics and historic session list
- 🔗 **One-click calendar subscription** - Easy integration with Apple Calendar, Google Calendar, etc.
- ⚠️ **Opt-in reminder** - Prominent reminder to sign up for free electricity sessions
- 🐙 **Octopus emoji favicon** - Branded favicon for easy identification

### Automation & Deployment
- ⚙️ **GitHub Actions ready** - Automated hourly scraping with zero maintenance
- 🔄 **Separate scrape/notification intervals** - Reliable notifications with independent timing
- 💾 **Persistent history** - History persists across GitHub Actions deployments
- 🌱 **Seed data support** - Initial history can be seeded from `gh-pages-data/`
- 🔄 **Auto-deployment** - Automatic deployment to GitHub Pages on every run

### Code Quality
- 🎨 Clean, refactored, and optimised code
- 📜 Open source under GNU GPL v3
- 🧪 Modular architecture with separate components

## Two Ways to Use

1. **GitHub Actions + Pages (Recommended)**: Fork the repo, enable Actions, get a public calendar URL that auto-updates hourly
2. **Local/Self-Hosted**: Run on your own machine with full control and custom Apprise notifications

> **Note**: The original OctoCal is live at https://evenwebb.github.io/OctoCal/ if you want to use it without forking!

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

Edit `config.yaml` to customise:

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

## Local Usage (Required for Apprise notification)

Run the scraper locally:

```bash
python main.py
```

The scraper will:
1. Check for new free electricity sessions
2. Update the iCal file in the `output` directory
3. Log all sessions to `output/history.json` for statistics tracking
4. Export upcoming sessions to `output/upcoming_sessions.json`
5. Send notifications based on your configuration
6. Continue running and checking at the configured interval

## GitHub Actions Deployment (Creates iCal file with reminders, no custom Apprise alerts)

The easiest way to use this is via **GitHub Actions** with automatic deployment to **GitHub Pages**. Your calendar will be publicly accessible and auto-update every hour!

### Quick Setup

1. **Fork this repository** on GitHub

2. **Update the HTML file** with your GitHub info (if forking):
   - Edit `gh-pages-src/index.html`
   - Replace `evenwebb` with your GitHub username
   - Replace `OctoCal` with your repository name (or keep it as OctoCal!)

3. **Enable GitHub Pages**:
   - Go to repo Settings → Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `(root)`
   - Save

4. **Run the workflow**:
   - Go to the Actions tab
   - Click "Scrape Octopus Energy Free Electricity"
   - Click "Run workflow"

5. **Access your calendar**:
   - Visit: `https://[your-username].github.io/[your-repo-name]/`
   - Subscribe to the calendar from the webpage!
   - View history and statistics at: `https://[your-username].github.io/[your-repo-name]/history.html`

### How It Works

- **Automatic scraping**: Runs every hour via GitHub Actions cron schedule
- **No config needed**: Automatically uses `config.yaml.example`
- **GitHub Pages**: Deploys to `gh-pages` branch with a beautiful webpage
- **History persistence**: Downloads existing history from `gh-pages` branch before scraping
- **Seed data**: Uses `gh-pages-data/history.json` if available for initial history
- **One-click subscribe**: Users can add the calendar to Apple Calendar, Google Calendar, etc.
- **Statistics tracking**: Automatically logs all sessions and calculates statistics

### Default Settings for GitHub Actions

When running on GitHub Actions, the script automatically:
- Uses `config.yaml.example` (no need to create `config.yaml`)
- Runs in single-run mode (scrape once and exit)
- Sets calendar alarms for 1 day before and 15 minutes before
- Disables Apprise notifications (use calendar alarms instead)
- Loads existing history from `gh-pages` branch or `gh-pages-data/` seed
- Logs all discovered sessions to `history.json`
- Exports upcoming sessions to `upcoming_sessions.json` for web display
- Preserves history between deployments (no data loss)

### Command Line Options

```bash
# Run once and exit (useful for cron jobs)
python main.py --single-run

# Use a different config file
python main.py --config my-config.yaml

# Combine options
python main.py --single-run --config my-config.yaml
```

## Project Structure

**Application Code:**
- `main.py` - Main entry point, configuration loader, and monitoring loop
- `octopus_scraper.py` - Web scraper for Octopus Energy website
- `session_parser.py` - Parser for session date/time strings
- `ical_generator.py` - iCal file generator
- `notifier.py` - Apprise notification handler
- `history_logger.py` - History tracking, statistics calculation, and session management

**Web Pages:**
- `gh-pages-src/index.html` - Main landing page with upcoming sessions and calendar links
- `gh-pages-src/history.html` - History page with statistics, charts, and session lists

**Configuration:**
- `config.yaml` - Your settings (copy from config.yaml.example)

**Data:**
- `gh-pages-data/history.json` - Seed data for initial history (committed to repo)
- `output/` - Generated iCal files, logs, state, and runtime history data

## Output

- **iCal file**: `output/octopus_free_electricity.ics` - Import into your calendar app
- **History file**: `output/history.json` - Complete session history with metadata
- **Upcoming sessions**: `output/upcoming_sessions.json` - JSON file for web display
- **Log file**: `output/octopus_scraper.log` - Application logs
- **State file**: `output/state.json` - Tracks seen sessions and sent notifications

## History & Statistics

OctoCal automatically tracks all discovered free electricity sessions and provides comprehensive statistics:

### Statistics Calculated
- **Total sessions** - Count of all historic sessions
- **Total hours** - Sum of all free electricity hours
- **Average duration** - Mean session length
- **Longest/shortest sessions** - Session duration extremes
- **Monthly breakdown** - Sessions and hours per month
- **Yearly totals** - Sessions and hours for the current year
- **Best month** - Month with most sessions
- **Most hours month** - Month with most free hours
- **Day patterns** - Most common day of week for sessions
- **Time patterns** - Most common start time
- **Frequency** - Average sessions per month

### Visualizations
- **Bar chart** - Sessions per month for the last 12 months (using Chart.js)
- **Monthly table** - Detailed breakdown of sessions and hours by month
- **Session list** - Chronological list of all historic sessions with lazy loading

### Accessing History
- Visit the **History & Statistics** page: `https://[your-username].github.io/[your-repo-name]/history.html`
- Or click the "📊 View Session History & Stats" button on the main page
- History updates automatically with each GitHub Actions run

### History Data Format
Sessions are stored in JSON format with the following structure:
```json
{
  "sessions": [
    {
      "session_str": "Free Electricity '24 Event 15 25/10/25",
      "start_time": "2025-10-25T11:00:00+00:00",
      "end_time": "2025-10-25T14:00:00+00:00",
      "duration_hours": 3.0,
      "discovered_at": "2026-01-11T16:57:26.650200",
      "code": "FREE_ELECTRICITY_EVENT_15_251025"
    }
  ],
  "last_updated": "2026-01-11T16:57:35.596021"
}
```

### Backfilling History
If you have access to the Octopus Energy API, you can backfill historic sessions:
1. Sessions discovered via API can include a `code` field for better deduplication
2. The history logger automatically handles deduplication using session codes or timestamps
3. History persists across GitHub Actions runs via the `gh-pages-data/` seed directory
