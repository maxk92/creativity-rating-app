# Optional Rating Scales Feature

## Overview

Rating scales can now be configured as optional or required. Users only need to complete required scales to proceed to the next video, making it possible to collect primary ratings while offering optional supplementary ratings.

## Configuration

Added `required_to_proceed` field to each rating scale in `config.yaml`:

```yaml
rating_scales:
  - active: true
    type: "discrete"
    title: "Creativity"
    required_to_proceed: true    # Required - user must rate this
    
  - active: true
    type: "discrete"
    title: "Aesthetic Appeal"
    required_to_proceed: false   # Optional - user can skip this
```

**Default behavior:** If `required_to_proceed` is not specified, it defaults to `true` (required).

## Implementation

### 1. Track Required Scales (CreativityRatingApp.py:959, 984-987)

```python
self.required_scales = []  # Store titles of required scales

# During initialization, extract required scale titles
self.required_scales = [
    scale.get('title') for scale in self.scale_configs
    if scale.get('required_to_proceed', True)
]
```

### 2. Updated Validation Logic (CreativityRatingApp.py:1193-1204)

```python
def set_scale_value(self, scale_title, value):
    """Set value and check if user can submit."""
    self.scale_values[scale_title] = value
    
    # Check only REQUIRED scales
    if self.action_not_recognized:
        self.has_any_rating = True
    else:
        self.has_any_rating = all(
            self.scale_values.get(title) is not None and 
            self.scale_values.get(title) != ''
            for title in self.required_scales  # Only check required
        )
```

### 3. Action Not Recognized Bypass (rating.kv:317)

When "Action not Recognized" button is pressed:
- `action_not_recognized` flag is set to `True`
- Triggers validation through `set_scale_value()`
- Always allows submission regardless of filled scales

## Behavior

**Required Scales (required_to_proceed: true):**
- ✅ Must have a value for submit button to enable
- ❌ Cannot proceed without rating these scales
- Visual: No special indicator (all scales look the same)

**Optional Scales (required_to_proceed: false):**
- ✅ Can be left empty
- ✅ User can proceed even without rating
- ✅ If provided, values are saved normally
- Visual: No special indicator (all scales look the same)

**"Action Not Recognized" Button:**
- ✅ Always allows submission
- ✅ Bypasses all scale requirements
- ✅ Works as before

## Example Use Cases

### 1. Primary + Secondary Ratings
```yaml
# Primary rating - required
- title: "Creativity"
  required_to_proceed: true

# Secondary ratings - optional
- title: "Technical Skill"
  required_to_proceed: false
- title: "Comments"
  type: "text"
  required_to_proceed: false
```

### 2. Core Metric + Experimental Scales
```yaml
# Core established metric
- title: "Overall Quality"
  required_to_proceed: true

# Experimental new metric being tested
- title: "Innovativeness"
  required_to_proceed: false
```

### 3. Fast Rating Mode
```yaml
# Only require one quick rating
- title: "Like/Dislike"
  required_to_proceed: true
  values: [1, 2, 3, 4, 5]

# Detailed optional feedback
- title: "Detailed Comments"
  type: "text"
  required_to_proceed: false
```

## Benefits

1. **Flexible data collection**: Gather essential data while offering optional depth
2. **Reduced rater fatigue**: Users don't feel obligated to complete every scale
3. **A/B testing**: Can test new scales without forcing participation
4. **Faster completion**: Users who want to rate quickly can skip optional fields
5. **Backward compatible**: Defaults to required (existing behavior)

## Current Configuration

In your config.yaml:
- **Creativity**: Required
- **Technical Correctness**: Required
- **Aesthetic Appeal**: Optional
- **Overall Quality**: Optional

This allows users to provide core creativity ratings quickly while optionally adding aesthetic and quality assessments.
