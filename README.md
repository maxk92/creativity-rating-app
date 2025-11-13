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

### 1. Clone or Download the Repository

``` bash
git clone https://github.com/maxk92/creativity-rating-app.git
cd creativity-rating-app
```

### 2. Install System Dependencies

**Ubuntu/Debian:**

``` bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv ffmpeg
```

**macOS:**

``` bash
brew install python ffmpeg
```

### 3. Create Virtual Environment

``` bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 4. Install Python Dependencies

``` bash
pip install -r requirements.txt
```

## Configuration

### config.yaml

The app uses a `config.yaml` file to specify data paths. Create or modify this file in the app's root directory:

``` yaml
paths:
  # Path to DuckDB database containing event metadata
  db_path: "/path/to/your/database.duckdb"

  # Path to directory containing video files (.mp4)
  video_path: "/path/to/your/videos/"
```

**Important Notes:** - The `video_path` should contain `.mp4` video files - Video filenames (without extension) must match the `id` column in the database - The database must have an `events` table with columns: `id`, `team`, `player`, `type`, `shot_body_part`, `pass_body_part`

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

## Adapting to Other Use Cases

### 1. Different Rating Dimensions

Edit `rating.kv` to modify the rating scales:

-   Search for sections labeled `Creativity Rating`, `Technical Correctness Rating`, and `Aesthetic Appeal Rating`
-   Modify the `Label` text properties to change dimension names and scale labels
-   Update corresponding methods in `CreativityRatingApp.py` (`set_likert`, `set_likert_tech`, `set_likert_aesthetic`)

### 2. Different Number of Rating Points

To change from 7-point to another scale:

1.  In `rating.kv`: Add/remove `ToggleButton` widgets in each rating section
2.  In `CreativityRatingApp.py`: Update `reset_likert()` to include new button IDs
3.  Update the button group names and values accordingly

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
├── CreativityRatingApp.py    # Main application logic
├── rating.kv                  # UI layout definition
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── user_data/                 # Generated user demographics
└── user_ratings/              # Generated rating data
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