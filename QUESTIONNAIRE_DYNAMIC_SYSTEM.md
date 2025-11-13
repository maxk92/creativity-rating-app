# Dynamic Questionnaire System Implementation

## Overview

The questionnaire screen is now fully configurable via `config.yaml`, allowing researchers to add, remove, or modify demographic questions without touching any code.

## Changes Made

### 1. Added Configuration Structure to config.yaml

Added new `questionnaire_fields` section with 13 pre-configured fields:

**Demographic Fields:**
- Gender (multiple choice: M/F/D)
- Age (numeric input)
- **Nationality (text input)** ← NEW FIELD

**Soccer Experience:**
- Player experience (numeric - years)
- Coach experience (numeric - years)
- Watch experience (numeric - years)

**License:**
- Coaching license (multiple choice: None/B/A/Pro)

**User ID Generation Fields:**
- Mother's initials (text, 2 chars max)
- Father's initials (text, 2 chars max)
- Number of siblings (numeric)
- Birthday (grouped: day/month/year - all numeric)

### 2. Updated User Class (CreativityRatingApp.py)

- Added `self.data = {}` dictionary to store all field responses
- Added `self.nationality = ''` field
- Maintains backward compatibility with legacy field names

### 3. Implemented Dynamic Form Builder (QuestionnaireScreen)

**New Methods:**
- `build_questionnaire_form()`: Dynamically creates widgets based on config
- `_set_field_value()`: Handles field value changes and updates User object

**Updated Methods:**
- `__init__()`: Loads config and stores field configurations
- `on_enter()`: Builds form on first entry
- `_build_focus_order()`: Collects dynamically created widgets for keyboard navigation
- `save_user_data()`: Saves both legacy fields and all dynamic field data

**Removed Methods:**
- Old callback methods (gender_clicked, age_input, etc.) replaced by unified `_set_field_value()`

### 4. Updated UI Layout (rating.kv)

- Replaced hardcoded form widgets with ScrollView containing `form_container`
- Form is now populated dynamically at runtime
- Navigation buttons remain static at bottom

## Field Configuration Options

Each field in `config.yaml` supports:

```yaml
- active: true/false              # Whether to display this field
  type: "multiple_choice" | "text" | "numeric"
  field_name: "internal_name"     # Used for data storage (no spaces)
  title: "Display Label"           # Shown to user (optional)
  hint_text: "Placeholder text"   # For text/numeric inputs
  options: ["Option1", "Option2"] # For multiple_choice only
  max_length: 2                   # For text only
  required_for_user_id: true      # Used in ID generation
  group: "group_name"             # Group related fields in one row
```

## Adding New Fields

To add a new field (e.g., "Education Level"):

1. Open `config.yaml`
2. Add a new entry to `questionnaire_fields`:

```yaml
- active: true
  type: "multiple_choice"
  field_name: "education"
  title: "Highest Education Level:"
  options: ["High School", "Bachelor", "Master", "PhD"]
```

3. Run the app - the field appears automatically
4. Data is automatically saved in user_data JSON files

## Benefits

1. **No code changes needed** to modify questionnaire
2. **Easy to customize** for different studies
3. **Automatic data handling** - fields are saved to JSON
4. **Keyboard navigation** works automatically with dynamic fields
5. **Backward compatible** - existing user data files still work

## Example: Nationality Field

The nationality field was added by simply adding this to config.yaml:

```yaml
- active: true
  type: "text"
  field_name: "nationality"
  title: ""
  hint_text: "Enter your nationality"
```

No Python code changes required!

## Data Storage

Field data is stored in two places:

1. **User.data dictionary**: All field responses (field_name → value)
2. **Legacy fields**: Specific attributes (age, gender, etc.) for backward compatibility

Both are saved to `user_data/{user_id}.json` with format:

```json
{
  "user_id": "abc123",
  "gender": "M",
  "age": 25,
  "nationality": "German",
  "player_exp": 10,
  "saved_at": "2025-11-13T10:30:00"
}
```
