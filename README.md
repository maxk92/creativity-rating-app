# Creativity Rating App

A Kivy-based desktop application for collecting subjective ratings of soccer actions from video clips. The app was designed to rate creativity, technical correctness, and aesthetic appeal of soccer plays, but can be adapted for other video rating studies.

## Features

-   **User Demographics Collection**: Captures rater background information (gender, age, experience, coaching license)
-   **Multi-dimensional Rating**: Three 7-point Likert scales for creativity, technical correctness, and aesthetic appeal
-   **Video Playback**: Built-in video player with loop functionality
-   **Metadata Display**: Shows action metadata (team, player, action type, body part used)
-   **Progress Tracking**: Automatically skips already-rated videos per user
-   **Data Persistence**: Saves user data and ratings as JSON files
-   **User ID Generation**: Creates unique anonymous IDs from demographic information

## Requirements

-   Python 3.8+
-   Linux or macOS (tested on both)
-   FFmpeg (for video playback)

## Installation

### Quick Setup (Recommended)

The easiest way to set up the app on a new machine:

``` bash
git clone https://github.com/maxk92/creativity-rating-app.git
cd creativity-rating-app
./setup.sh
```

The setup script will:
- Check your Python version (requires 3.8+)
- Detect and optionally install FFmpeg if missing
- Create a virtual environment
- Install all Python dependencies
- Create necessary directories
- Verify the installation

### Manual Setup

If you prefer to set up manually:

#### 1. Clone or Download the Repository

``` bash
git clone https://github.com/maxk92/creativity-rating-app.git
cd creativity-rating-app
```

#### 2. Install System Dependencies

**Ubuntu/Debian:**

``` bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv ffmpeg
```

**macOS:**

``` bash
brew install python ffmpeg
```

#### 3. Create Virtual Environment

``` bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

#### 4. Install Python Dependencies

``` bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Create Directories

``` bash
mkdir -p user_data user_ratings backup/user_data backup/user_ratings output
```

## Configuration

The app uses three YAML configuration files:

### 1. config.yaml (Main Configuration)

Specifies data paths and screen layout:

``` yaml
paths:
  db_path: "/path/to/your/database.duckdb"  # DuckDB database with event metadata
  video_path: "/path/to/your/videos/"       # Directory containing .mp4 files

settings:
  min_ratings_per_video: 2  # Stop showing videos after N ratings collected
  questionnaire_fields_file: "questionnaire_fields.yaml"  # External questionnaire config
  rating_scales_file: "rating_scales.yaml"  # External rating scales config
  display_metadata: true  # Show metadata (team, player, etc.) at top
  display_pitch: true  # Show pitch visualization next to video
  video_playback_mode: "loop"  # "loop" or "once" - video playback behavior

screen_dimensions:
  metadata_display_height: 0.08   # Proportional heights (must sum to 1.0)
  video_player_height: 0.46
  control_buttons_height: 0.08
  rating_scales_height: 0.38      # Adjust when adding/removing scales
```

### 2. questionnaire_fields.yaml

Defines demographic questions and fields. Fully customizable without code changes. See file for examples.

### 3. rating_scales.yaml

Defines rating dimensions and scales. Supports discrete (buttons), slider, and text input types. Fully customizable without code changes. See file for examples.

**Important Notes:**
- The `video_path` should contain `.mp4` video files
- Video filenames (without extension) must match the `id` column in the database
- The database must have an `events` table with columns: `id`, `team`, `player`, `type`, `shot_body_part`, `pass_body_part`
- When adding/removing rating scales, adjust `screen_dimensions.rating_scales_height` in config.yaml

### Database Structure

The app expects a DuckDB database with an `events` table:

``` sql
CREATE TABLE events (
    id VARCHAR PRIMARY KEY,           -- Matches video filename (without .mp4)
    team VARCHAR,                     -- Team name
    player VARCHAR,                   -- Player name
    type VARCHAR,                     -- Action type (e.g., "Shot", "Pass")
    shot_body_part VARCHAR,           -- Body part for shots
    pass_body_part VARCHAR            -- Body part for passes
);
```

## Usage

### Running the App

``` bash
python3 CreativityRatingApp.py
```

### Workflow

1.  **Welcome Screen**: Introduction and instructions
2.  **Questionnaire Screen**:
    -   Enter demographic information
    -   Provide parent name initials and birth information for anonymous ID generation
3.  **Video Rating Screen**:
    -   Watch videos (they loop automatically)
    -   Rate on three dimensions using 7-point scales
    -   Or mark action as "not recognized"
    -   Submit rating to proceed to next video

### User ID Generation

User IDs are generated from: - First two letters of mother's given name - First two letters of father's given name - Number of siblings - Birthday (day, month, year)

**Formula**: `[mother_initials][father_initials][day+month][cross_sum(year)×(siblings+1)]`

**Example**: - Mother: Mary → "ma" - Father: John → "jo" - Siblings: 2 - Birthday: June 15, 1995 - Result: `majo2172` (ma + jo + 21 + 24×3)

### Output Files

**User Data**: `user_data/{user_id}_{timestamp}.json`

``` json
{
  "user_id": "majo2172",
  "gender": "F",
  "age": 29,
  "license": "B",
  "player_exp": 10,
  "coach_exp": 2,
  "watch_exp": 20,
  "saved_at": "2025-10-09T14:30:00"
}
```

**Rating Data**: `user_ratings/{user_id}_{action_id}.json`

``` json
{
  "user_id": "majo2172",
  "id": "action_12345",
  "action_rating": 6,
  "technical_correctness": 5,
  "aesthetic_appeal": 7,
  "action_not_recognized": false
}
```

### Using Images Instead of Videos

The app supports displaying static images by converting them to short videos:

``` bash
# Edit the configuration at the top of the script
# IMAGE_DURATION: how long to show the image (default: 2s)
# BLACK_DURATION: how long to show black screen (default: 2s)
# INPUT_FOLDER: path to your images
# OUTPUT_FOLDER: where to save the videos

./convert_images_to_videos.sh
```

The script:
- Converts JPG, PNG, BMP, TIFF, WEBP images to MP4 videos
- Shows each image for a configurable duration
- Followed by a black screen for a configurable duration
- Maintains proper aspect ratio with padding
- Uses the same filename with .mp4 extension

After conversion, update `config.yaml` to point `video_path` to the output folder.

## Adapting to Other Use Cases

### 1. Different Rating Dimensions

Edit `rating_scales.yaml` to add/modify rating scales:
- Change `title`, `label_low`, `label_high` for existing scales
- Add new scales by copying an existing scale block
- Set `active: false` to disable a scale without deleting it
- Choose scale `type`: "discrete" (buttons), "slider", or "text"
- Mark scales as `required_to_proceed: true/false`

No code changes needed!

### 2. Different Questionnaire Fields

Edit `questionnaire_fields.yaml` to add/modify demographic questions:
- Add new fields by copying an existing field block
- Choose field `type`: "multiple_choice", "text", or "numeric"
- Set `active: false` to disable a field without deleting it
- Mark fields with `required_for_user_id: true` if used in ID generation
- Group related fields with the `group` property

No code changes needed!

### 3. Different Video Sources

The app works with any `.mp4` videos. To use without metadata:

1.  Place videos in the configured `video_path`
2.  Modify `VideoPlayerScreen.__init__()` to skip database loading
3.  Update `load_video()` to handle missing metadata gracefully (already has fallback)

### 4. Different Metadata Fields

To display different metadata:

1.  Update the database schema with your columns
2.  Modify the SQL query in `VideoPlayerScreen.__init__()`
3.  Update `load_video()` to display your custom fields
4.  Edit `rating.kv` to add/remove metadata labels

### 5. Change Language

Replace text strings in `rating.kv` and popup messages in `CreativityRatingApp.py`:

-   Button labels: `text: 'Submit Rating'` → `text: 'Bewertung abgeben'`
-   Hints: `hint_text: 'Enter your age'` → `hint_text: 'Alter eingeben'`
-   Popup messages in `submit_rating()` and `confirm_back_to_questionnaire()`

## Troubleshooting

### Video Playback Issues

If videos don't play:

``` bash
# Check FFmpeg installation
ffmpeg -version

# Reinstall ffpyplayer
pip uninstall ffpyplayer
pip install ffpyplayer
```

### Database Connection Errors

-   Verify `db_path` in `config.yaml` points to a valid DuckDB file
-   Ensure the `events` table exists with required columns
-   Check file permissions

### "No videos to rate" Message

-   Ensure `.mp4` files exist in `video_path`
-   Check that video filenames match database IDs
-   Verify the user hasn't already rated all videos (check `user_ratings/` folder)

### App Crashes on Startup

-   Check Python version: `python3 --version` (should be 3.8+)
-   Verify all dependencies installed: `pip list`
-   Look for error messages in the console output

## File Structure

```
creativity-rating-app/
├── CreativityRatingApp.py         # Main application logic
├── rating.kv                       # UI layout definition
├── config.yaml                     # Main configuration (paths, settings)
├── questionnaire_fields.yaml       # Questionnaire fields configuration
├── rating_scales.yaml              # Rating scales configuration
├── write_ratings2csv.py            # Data export and backup script
├── setup.sh                        # Automated setup script
├── convert_images_to_videos.sh     # Image to video conversion script
├── requirements.txt                # Python dependencies
├── .python-version                 # Recommended Python version
├── README.md                       # This file
├── CLAUDE.md                       # Developer documentation
├── user_data/                      # Generated user demographics
├── user_ratings/                   # Generated rating data
├── backup/                         # Auto-backup of JSON files
└── output/                         # CSV exports and logs
```

## Technical Details

### Dependencies

-   **Kivy 2.3.1**: Cross-platform GUI framework
-   **ffpyplayer 4.5.3**: Video playback backend
-   **DuckDB 1.4.0**: Embedded analytical database
-   **pandas 2.3.3**: Data manipulation
-   **PyYAML 6.0.3**: Configuration file parsing
-   **matplotlib 3.7.2+**: Pitch visualization (uses Agg backend)
-   **mplsoccer 1.6.0+**: Soccer pitch drawing

### Architecture

-   **User Class**: Manages demographic data and ID generation
-   **WelcomeScreen**: Initial instructions
-   **QuestionnaireScreen**: Collects user information
-   **VideoPlayerScreen**: Main rating interface with video playback
-   **RatingApp**: Application controller with screen management

## License

\[Add your license information here\]

## Contact

maxklemp92\@gmail.com

## Acknowledgments

This app was developed for a research study on creativity assessment in soccer. It uses StatsBomb event data and video footage for rating collection.