# Adaptive Questionnaire Layout Implementation

## Problem
The questionnaire form was cramped in the top half of the window with all fields using fixed 48dp heights, making it difficult to read labels and creating poor use of screen space.

## Solution
Implemented dynamic height calculation that:
1. Calculates available screen space (total height minus header and navigation buttons)
2. Distributes space evenly among all form fields
3. Respects minimum (55dp) and maximum (80dp) heights for readability
4. Adapts automatically when window is resized

## Implementation Details

### Height Calculation (CreativityRatingApp.py:515-537)

```python
# Count total rows (accounting for grouped fields)
num_rows = 0
processed_groups = set()
for field_config in self.field_configs:
    group = field_config.get('group', None)
    if group:
        if group not in processed_groups:
            num_rows += 1
            processed_groups.add(group)
    else:
        num_rows += 1

# Calculate optimal row height
available_height = self.height - 48 - 60 - 40  # header, buttons, padding
calculated_height = available_height / num_rows
row_height = max(55, min(80, calculated_height))
```

### Key Features

**Dynamic Height Assignment:**
- Each row receives an equal share of available space
- Minimum height: 55dp (ensures readability)
- Maximum height: 80dp (prevents excessive spacing)
- Grouped fields (like birthday) count as one row

**Improved Text Alignment:**
- Labels now use `halign='right'` and `valign='middle'`
- Text inputs have proper padding for vertical centering
- Font sizes adjusted slightly for better readability (height/35 instead of height/40)

**Responsive Resizing:**
- Binds to screen height changes via `_on_height_change()`
- Rebuilds form if height changes by more than 10%
- Automatically recalculates optimal row heights

**ScrollView Enhancement:**
- If fields exceed available space (many fields or small screen), scrolling activates automatically
- Visible scrollbar (bar_width: 10) for user feedback
- Maintains spacing: 2dp between rows for clean appearance

### Layout Structure (rating.kv)

```
QuestionnaireScreen
└── BoxLayout (vertical)
    ├── Label (header, fixed 48dp)
    ├── ScrollView (size_hint_y: 1, takes all remaining space)
    │   └── form_container (dynamic height)
    │       ├── Field Row 1 (calculated height)
    │       ├── Field Row 2 (calculated height)
    │       └── ...
    └── BoxLayout (navigation buttons, fixed 60dp)
```

## Benefits

1. **Full screen utilization**: Form now uses entire window height
2. **Better readability**: Larger, properly spaced fields with improved font sizes
3. **Adaptive**: Works on different screen sizes and resolutions
4. **Scroll when needed**: Automatically enables scrolling for many fields
5. **Consistent spacing**: All fields get equal visual weight

## Example Calculations

**For a 1080p screen (1920x1080):**
- Total height: 1080px
- Available: 1080 - 48 - 60 - 40 = 932px
- With 11 rows: 932 / 11 ≈ 84px → capped at 80px
- Each field gets 80px height (comfortable reading)

**For many fields (20 fields on 1080p):**
- Available: 932px
- With 20 rows: 932 / 20 ≈ 46px → raised to 55px minimum
- Each field gets 55px height (readable minimum)
- Total height exceeds available space → scrolling enabled

## Testing

The layout has been tested to:
- ✓ Properly calculate heights on initialization
- ✓ Adapt when window is resized
- ✓ Handle grouped fields correctly
- ✓ Maintain keyboard navigation
- ✓ Enable scrolling when needed
