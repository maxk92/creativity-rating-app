# Quick Setup Guide

## One-Command Setup

After cloning the repository to a new machine:

```bash
./setup.sh
```

That's it! The script handles everything automatically.

## What the Setup Script Does

1. **Checks Python version** (requires 3.8+)
2. **Checks for FFmpeg** (offers to install if missing)
3. **Creates virtual environment** (`venv/`)
4. **Upgrades pip** to latest version
5. **Installs all Python dependencies** from `requirements.txt`
6. **Creates necessary directories** (`user_data/`, `user_ratings/`, `backup/`, `output/`)
7. **Verifies configuration files** exist
8. **Tests Python syntax** of main app

## After Setup

1. **Configure your paths** in `config.yaml`:
   ```yaml
   paths:
     db_path: "/path/to/your/database.duckdb"
     video_path: "/path/to/your/videos/"
   ```

2. **Customize questionnaire** (optional):
   - Edit `questionnaire_fields.yaml`

3. **Customize rating scales** (optional):
   - Edit `rating_scales.yaml`

4. **Run the app**:
   ```bash
   source venv/bin/activate  # Activate virtual environment
   python3 CreativityRatingApp.py
   ```

## Troubleshooting

### Setup script fails

**Permission denied:**
```bash
chmod +x setup.sh
./setup.sh
```

**Python version too old:**
- Install Python 3.8 or higher
- Update `.python-version` file if needed

**FFmpeg not found:**
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

### Virtual environment issues

If you encounter virtual environment problems, recreate it:
```bash
rm -rf venv
./setup.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Dependencies Overview

**System Requirements:**
- Python 3.8+ (recommended: 3.12+)
- FFmpeg (for video playback)

**Python Packages (auto-installed):**
- Kivy 2.3.1 - GUI framework
- ffpyplayer 4.5.3 - Video playback
- DuckDB 1.4.0 - Database
- pandas 2.3.3 - Data manipulation
- PyYAML 6.0.3 - Config parsing
- matplotlib 3.7.2+ - Pitch visualization
- mplsoccer 1.6.0+ - Soccer pitch drawing

See `requirements.txt` for complete list.

## Using on a New Machine

1. **Clone the repository:**
   ```bash
   git clone https://github.com/maxk92/creativity-rating-app.git
   cd creativity-rating-app
   ```

2. **Run setup:**
   ```bash
   ./setup.sh
   ```

3. **Configure:**
   - Update paths in `config.yaml`
   - Adjust questionnaire/scales if needed

4. **Start rating:**
   ```bash
   source venv/bin/activate
   python3 CreativityRatingApp.py
   ```

## Keeping Setup Simple

The repository includes:
- ✅ `requirements.txt` - Pinned dependency versions
- ✅ `.python-version` - Recommended Python version
- ✅ `setup.sh` - Automated setup script
- ✅ Configuration files with sensible defaults

Just clone and run `./setup.sh` - everything else is automatic!
