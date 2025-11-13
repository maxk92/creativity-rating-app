# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Kivy-based desktop application for collecting subjective ratings of soccer actions from video clips. The app was designed for a research study on creativity assessment in soccer, allowing users to rate creativity, technical correctness, and aesthetic appeal of soccer plays. It can be adapted for other video rating studies.

## Running the Application

```bash
# Activate virtual environment
source venv/bin/activate  # or .venv/bin/activate

# Run the app
python3 CreativityRatingApp.py
```

## Testing and Development

```bash
# Check Python syntax for the main app
python3 -m py_compile CreativityRatingApp.py

# Run CSV export script (also runs automatically on app shutdown)
python3 write_ratings2csv.py
```

## Architecture

### Core Classes and Screens

The app uses Kivy's screen manager pattern with the following flow:

1. **WelcomeScreen** - Initial instructions screen
2. **LoginScreen** - Checks if user has participated before; validates returning users by user_id
3. **QuestionnaireScreen** - Collects demographic data and generates anonymous user_id
4. **VideoPlayerScreen** - Main rating interface with video playback and dynamically generated rating scales

### User ID Generation

The app generates anonymous user IDs from demographic information using the formula:
```
[mother_initials][father_initials][day+month][cross_sum(year) × (siblings+1)]
```

Implementation in `User.set_user_id()` at CreativityRatingApp.py:181.

### Dynamic Rating Scale System

A key architectural feature is the **dynamic rating scale generation system**:

- Rating scales are configured in `config.yaml` under the `rating_scales` section
- Each scale can be `discrete` (toggle buttons), `slider`, or `text` input
- `VideoPlayerScreen.build_rating_scales()` (CreativityRatingApp.py:863) dynamically generates the UI widgets at runtime based on active scales
- Scales are stored in `self.scale_values` dictionary with scale titles as keys
- Screen proportions can be adjusted in `config.yaml` under `screen_dimensions` to accommodate different numbers of scales

**Optional vs Required Scales:**
- Each scale can be marked with `required_to_proceed: true/false`
- Only required scales must be completed for submit button to enable
- Optional scales can be skipped, but values are saved if provided
- When "Action not Recognized" is pressed, all scales become optional
- Implementation: `self.required_scales` list tracks required scale titles (CreativityRatingApp.py:984-987)
- Validation checks only required scales in `set_scale_value()` (CreativityRatingApp.py:1193-1204)

This design allows researchers to easily add/remove/modify rating dimensions and control which are mandatory vs optional, all without touching code.

### Dynamic Questionnaire System

Similarly, the **questionnaire screen is fully configurable**:

- Questionnaire fields are configured in `config.yaml` under the `questionnaire_fields` section
- Each field can be `multiple_choice` (toggle buttons), `text` input, or `numeric` input
- Fields can be grouped (e.g., birthday fields with day/month/year)
- `QuestionnaireScreen.build_questionnaire_form()` (CreativityRatingApp.py:502) dynamically generates the form at runtime
- Field values are stored in `User.data` dictionary and legacy fields (for backward compatibility)
- Fields can be marked with `required_for_user_id: true` to indicate they're used in ID generation

**Adaptive Layout:**
- Form automatically calculates optimal field heights to use full screen space
- Available height is divided evenly among fields (min: 55dp, max: 80dp per field)
- Automatically enables scrolling if many fields exceed screen space
- Responds to window resize events by recalculating layout (CreativityRatingApp.py:718)

This allows researchers to easily customize demographics collection by editing config.yaml instead of modifying code. For example, nationality was added simply by adding a configuration entry.

### Data Flow and Persistence

**User Data:**
- Collected in `QuestionnaireScreen`
- Saved to `user_data/{user_id}.json` when user proceeds to video screen
- Format includes: user_id, gender, age, license, experience fields, saved_at timestamp

**Rating Data:**
- Collected in `VideoPlayerScreen`
- Saved immediately after each video rating to `user_ratings/{user_id}_{action_id}.json`
- Contains: user_id, action_id, action_not_recognized flag, and all scale values
- Scale values are stored with sanitized keys (title converted to lowercase with underscores)

**Video Tracking:**
- On `VideoPlayerScreen.__init__()`, the app loads all videos from the configured directory
- Filters out videos already rated by current user by checking existing files in `user_ratings/`
- Also filters out videos that have reached the minimum required ratings (`min_ratings_per_video` in config.yaml)
- This ensures users only see unrated videos and prevents over-rating popular clips

### Database Integration

The app uses DuckDB to store and retrieve soccer event metadata:
- Database path configured in `config.yaml`
- Expected schema: `events` table with columns: id, team, player, jersey_number, type, body_part, start_x, start_y, end_x, end_y
- Video filenames (without .mp4 extension) must match the `id` column
- Metadata is loaded once during `VideoPlayerScreen.__init__()` for all available videos
- The app gracefully handles missing metadata by showing placeholder text

### Matplotlib Integration

The app uses matplotlib to draw soccer pitch visualizations showing action trajectories:
- Uses non-interactive 'Agg' backend (set via `matplotlib.use('Agg')` before importing pyplot)
- Figures are saved to BytesIO buffer as PNG images (CreativityRatingApp.py:1166)
- Buffer is loaded as Kivy CoreImage and displayed via Kivy Image widget (CreativityRatingApp.py:1171-1173)
- This approach avoids kivy-garden dependency and is more reliable across platforms
- All figures are properly closed with `plt.close(fig)` to prevent memory leaks

### Keyboard Navigation System

The app implements custom keyboard navigation using focusable widget classes:

- **FocusableButton**, **FocusableToggleButton**, **FocusableTextInput** - Custom widget classes with visual focus indicators (blue border)
- Each screen maintains a `focusable_widgets` list and handles Tab/Shift+Tab navigation
- Enter/Space activates focused widgets
- Implementation details in CreativityRatingApp.py:37-153 (widget classes) and per-screen `_on_keyboard_down()` handlers

This is crucial because the app runs in fullscreen mode without mouse interaction.

## Configuration

The configuration is split across three YAML files for better readability:

### config.yaml (Main Configuration)

```yaml
paths:
  db_path: "/path/to/database.duckdb"  # DuckDB database with event metadata
  video_path: "/path/to/videos/"       # Directory containing .mp4 files

settings:
  min_ratings_per_video: 2  # Stop showing videos after N ratings collected
  questionnaire_fields_file: "questionnaire_fields.yaml"  # External file for questionnaire config
  rating_scales_file: "rating_scales.yaml"  # External file for rating scales config
  modality: "video"  # "video" or "image" - determines media type
  display_metadata: true  # Show metadata (team, player, type, etc.) at top of video screen
  display_pitch: true  # Show pitch visualization next to video (when false, video is centered)
  video_playback_mode: "loop"  # "loop" = video repeats automatically, "once" = plays once and cannot be restarted

screen_dimensions:
  metadata_display_height: 0.08   # Proportional heights (must sum to 1.0)
  video_player_height: 0.46
  control_buttons_height: 0.08
  rating_scales_height: 0.38      # Increase this if adding more scales
```

### questionnaire_fields.yaml (Questionnaire Configuration)

```yaml
- active: true/false
  type: "multiple_choice"  # or "text" or "numeric"
  field_name: "gender"      # Internal name (no spaces)
  title: "Please select your gender"  # Label/prompt
  options: ["M", "F", "D"]  # For multiple_choice only
  hint_text: "Enter your age"  # For text/numeric only
  max_length: 2  # For text only
  required_for_user_id: true  # Whether field is used in user ID generation
  group: "birthday"  # Optional: group related fields in one row
```

### rating_scales.yaml (Rating Scales Configuration)

```yaml
- active: true/false
  type: "discrete"  # or "slider" or "text"
  title: "Scale Name"
  label_low: "left label"
  label_high: "right label"
  values: [1, 2, 3, 4, 5, 6, 7]  # for discrete only
  # slider_min/max: for slider type only
  required_to_proceed: true  # Whether user must provide input (default: true)
                              # When "action not recognized" is pressed, all scales become optional
```

**Important:** When adding/removing rating scales, adjust `screen_dimensions.rating_scales_height` in config.yaml to ensure scales fit properly on screen.

## Adapting the Application

### Adding/Modifying Questionnaire Fields

Edit `questionnaire_fields.yaml` only - no code changes needed:
1. Add new field entry with `active: true`
2. Specify field_name (internal), type, title/hint_text, and any options
3. The app will automatically generate widgets, save data, and handle user ID generation for marked fields

### Adding/Modifying Rating Scales

Edit `rating_scales.yaml` only - no code changes needed:
1. Add new scale entry with `active: true`
2. Adjust `screen_dimensions.rating_scales_height` in config.yaml if necessary
3. The app will automatically generate widgets and save new dimensions to JSON

### Customizing Video Display

Control what's displayed on the video rating screen via `config.yaml`:

**display_metadata (true/false):**
- When `true`: Shows metadata bar at top (team, player, type, body part, jersey number)
- When `false`: Hides metadata bar and allocates that space to the video area
- Useful when metadata is not relevant to your study

**display_pitch (true/false):**
- When `true`: Shows pitch visualization next to video (65/35 split)
- When `false`: Hides pitch visualization and centers video to use full width
- When disabled, video automatically expands to use available horizontal space
- Useful for non-soccer studies or when spatial context is not needed

**Example configurations:**

```yaml
# Standard soccer rating with all visualizations
display_metadata: true
display_pitch: true

# Simple video rating without metadata or pitch
display_metadata: false
display_pitch: false  # Video takes full screen space

# Show metadata but not pitch (useful for event types without spatial data)
display_metadata: true
display_pitch: false
```

### Customizing Video Playback

Control video playback behavior via `config.yaml`:

**video_playback_mode (loop/once):**
- **"loop"** (default): Video plays in continuous loop
  - Video automatically restarts when it reaches the end
  - User can pause/play at any time
  - Suitable for rating tasks where users need time to observe details

- **"once"**: Video plays once and cannot be restarted
  - Video automatically plays when loaded
  - After reaching the end, video stops and cannot be replayed
  - User cannot manually restart the video
  - Video controls (play/pause/seek bar) are hidden in this mode
  - Uses plain Video widget without controls for cleaner interface
  - Suitable for studies requiring single exposure to stimuli
  - Implementation: When user attempts to restart, the video is immediately stopped

**Example configurations:**

```yaml
# Allow users to watch videos repeatedly (default)
video_playback_mode: "loop"

# Show video only once (e.g., for first impression ratings)
video_playback_mode: "once"
```

**Use cases for "once" mode:**
- First impression studies where repeat viewing would bias results
- Time-constrained rating tasks
- Studies requiring spontaneous reactions
- Preventing over-analysis of stimuli

### Changing Video Sources

Videos must be .mp4 files in the configured `video_path`. To use without metadata:
1. Place videos in directory specified in config.yaml
2. The app handles missing metadata gracefully (see VideoPlayerScreen.load_video():1127)

### Changing Language

All user-facing strings are in `rating.kv` and popup messages in `CreativityRatingApp.py`:
- Button labels: search for `text: ` in rating.kv
- Hints: search for `hint_text: ` in rating.kv
- Popup messages: search for `Popup(` in CreativityRatingApp.py

## Data Export and Backup

### Automatic Export on Shutdown

When the app closes, `RatingApp.on_stop()` (CreativityRatingApp.py:1255) automatically runs `write_ratings2csv.py`, which:

1. Loads all JSON files from `user_data/` and `user_ratings/`
2. Generates CSV exports in `output/`:
   - `ratings.csv` - All individual ratings with timestamps
   - `mean_ratings.csv` - Aggregated mean/std per action (dynamically detects scale columns)
   - `users.csv` - All user demographic data
   - `rating_log.txt` - Summary statistics
3. Creates backup copies of all JSON files in `backup/user_data/` and `backup/user_ratings/`

The export script dynamically detects scale columns by excluding metadata columns (user_id, id, action_not_recognized, file_created_at, filename), making it compatible with any rating scale configuration.

## File Structure

```
CreativityRatingApp.py        # Main application logic and screen classes
rating.kv                      # Kivy UI layout definitions
config.yaml                    # Main configuration (paths, settings, screen layout)
questionnaire_fields.yaml      # Questionnaire fields configuration
rating_scales.yaml             # Rating scales configuration
write_ratings2csv.py           # Data export and backup script
requirements.txt               # Python dependencies
user_data/                     # Generated user demographics (JSON)
user_ratings/                  # Generated rating data (JSON)
backup/                        # Auto-backup of JSON files
output/                        # CSV exports and logs
```

## Dependencies

Key dependencies (see requirements.txt for full list):
- **Kivy 2.3.1** - GUI framework
- **ffpyplayer 4.5.3** - Video playback (requires FFmpeg system package)
- **DuckDB 1.4.0** - Embedded database for metadata
- **pandas 2.3.3** - Data manipulation for exports
- **PyYAML 6.0.3** - Configuration file parsing
- **matplotlib 3.7.2+** - For pitch visualization (uses Agg backend to export PNG to BytesIO)
- **mplsoccer 1.6.0+** - Soccer pitch drawing

Note: The app uses matplotlib's non-interactive 'Agg' backend and saves figures to memory buffers, which are then displayed as Kivy Image widgets. This approach avoids the need for kivy-garden dependencies.

## Common Issues

**Virtual environment not working / "No module named kivy":**

If you get "No module named kivy" even after activating the venv, the virtual environment may be corrupted. Fix it by recreating:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Video playback not working:**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check that `os.environ['KIVY_VIDEO'] = 'ffpyplayer'` is set before Kivy imports (line 10)

**Database connection errors:**
- Verify `db_path` in config.yaml points to valid DuckDB file
- Check that `events` table exists with required columns

**"No videos to rate" message:**
- Verify .mp4 files exist in `video_path`
- Check that video filenames match database IDs (without .mp4 extension)
- Check if user has already rated all videos (look in `user_ratings/`)
- Check if all videos have reached `min_ratings_per_video` threshold
