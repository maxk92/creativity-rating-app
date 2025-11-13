"""
Creativity Rating App
A Kivy application for rating the creativity, technical correctness, and aesthetic appeal
of soccer actions from video clips.
"""

import kivy
import pandas as pd
import os
os.environ['KIVY_VIDEO'] = 'ffpyplayer'  # Use ffpyplayer for video playback
import json
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.image import Image as KivyImage
from kivy.properties import NumericProperty, BooleanProperty, StringProperty, DictProperty
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, Line
import random
from datetime import datetime
import duckdb
import yaml
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import mplsoccer
from io import BytesIO

kivy.require("1.9.1")

# Set window to fullscreen
Window.fullscreen = 'auto'

class FocusableToggleButton(ToggleButton):
    """
    ToggleButton with keyboard focus support and visual feedback.
    Shows a border when focused to indicate it's the active element.
    """
    focus = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_rect = None
        self.focus_color = None
        self.bind(focus=self.on_focus)

    def on_focus(self, instance, value):
        """Add visual feedback when button gains/loses focus."""
        if value:  # Gained focus
            with self.canvas.after:
                self.focus_color = Color(0, 0.5, 1, 1)  # Blue focus border
                self.focus_rect = Line(rectangle=(self.x, self.y, self.width, self.height), width=3)
            self.bind(pos=self._update_focus_rect, size=self._update_focus_rect)
        else:  # Lost focus
            if self.focus_rect:
                self.canvas.after.remove(self.focus_color)
                self.canvas.after.remove(self.focus_rect)
                self.unbind(pos=self._update_focus_rect, size=self._update_focus_rect)
                self.focus_rect = None
                self.focus_color = None

    def _update_focus_rect(self, *args):
        """Update focus rectangle position and size when widget moves/resizes."""
        if self.focus_rect:
            self.focus_rect.rectangle = (self.x, self.y, self.width, self.height)


class FocusableButton(Button):
    """
    Button with keyboard focus support and visual feedback.
    Shows a border when focused to indicate it's the active element.
    """
    focus = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_rect = None
        self.focus_color = None
        self.bind(focus=self.on_focus)

    def on_focus(self, instance, value):
        """Add visual feedback when button gains/loses focus."""
        if value:  # Gained focus
            with self.canvas.after:
                self.focus_color = Color(0, 0.5, 1, 1)  # Blue focus border
                self.focus_rect = Line(rectangle=(self.x, self.y, self.width, self.height), width=3)
            self.bind(pos=self._update_focus_rect, size=self._update_focus_rect)
        else:  # Lost focus
            if self.focus_rect:
                self.canvas.after.remove(self.focus_color)
                self.canvas.after.remove(self.focus_rect)
                self.unbind(pos=self._update_focus_rect, size=self._update_focus_rect)
                self.focus_rect = None
                self.focus_color = None

    def _update_focus_rect(self, *args):
        """Update focus rectangle position and size when widget moves/resizes."""
        if self.focus_rect:
            self.focus_rect.rectangle = (self.x, self.y, self.width, self.height)


class FocusableTextInput(TextInput):
    """
    TextInput with keyboard focus support that doesn't consume Tab key.
    Allows Tab to be used for navigation instead of text insertion.
    """
    # Note: TextInput already has a 'focus' property, so we don't need to add it

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_rect = None
        self.focus_color = None
        self.bind(focus=self.on_focus_change)

    def on_focus_change(self, instance, value):
        """Add visual feedback when input gains/loses focus."""
        if value:  # Gained focus
            with self.canvas.after:
                self.focus_color = Color(0, 0.5, 1, 1)  # Blue focus border
                self.focus_rect = Line(rectangle=(self.x, self.y, self.width, self.height), width=3)
            self.bind(pos=self._update_focus_rect, size=self._update_focus_rect)
        else:  # Lost focus
            if self.focus_rect:
                self.canvas.after.remove(self.focus_color)
                self.canvas.after.remove(self.focus_rect)
                self.unbind(pos=self._update_focus_rect, size=self._update_focus_rect)
                self.focus_rect = None
                self.focus_color = None

    def _update_focus_rect(self, *args):
        """Update focus rectangle position and size when widget moves/resizes."""
        if self.focus_rect:
            self.focus_rect.rectangle = (self.x, self.y, self.width, self.height)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        """Override to prevent Tab from being consumed by TextInput."""
        key = keycode[1]

        # Don't consume Tab or Shift+Tab - let parent handle it for navigation
        if key == 'tab':
            return False

        # Don't consume Enter/Space when we want them for navigation
        # But allow normal Enter for text input in multiline mode
        if key in ('enter', 'numpadenter') and not self.multiline:
            return False

        # For all other keys, use default TextInput behavior
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


class User:
    """
    Stores demographic and experience data for a user/rater.
    User ID is constructed from parent name initials, birthdate, birth year, and siblings.
    Formula: mother_initials + father_initials + (day+month) + (cross_sum_of_year * (siblings+1))
    """
    def __init__(self):
        self.user_id = ''
        self.data = {}  # Stores all questionnaire field responses
        # Legacy fields for backward compatibility
        self.gender = 'Not specified'
        self.age = 0
        self.nationality = ''
        self.player_exp = 0
        self.coach_exp = 0
        self.watch_exp = 0
        self.license = 'Not specified'
        # User ID components
        self.mother_initials = ''  # First two letters of mother's given name
        self.father_initials = ''  # First two letters of father's given name
        self.siblings = 0          # Number of siblings
        self.birth_day = 0         # Day of birth
        self.birth_month = 0       # Month of birth
        self.birth_year = 0        # Year of birth

    def _calculate_cross_sum(self, number):
        """Calculate the cross sum (sum of digits) of a number."""
        return sum(int(digit) for digit in str(abs(number)))

    def set_user_id(self):
        """
        Generate user_id from components.
        Format: mother_initials + father_initials + (day+month) + (cross_sum_year * (siblings+1))
        """
        if not self.mother_initials or not self.father_initials:
            self.user_id = 'unknown'
            return

        # Calculate day+month sum
        date_sum = self.birth_day + self.birth_month

        # Calculate cross sum of birth year
        year_cross_sum = self._calculate_cross_sum(self.birth_year)

        # Calculate final component: cross_sum * (siblings + 1)
        sibling_factor = year_cross_sum * (self.siblings + 1)

        # Concatenate all parts
        self.user_id = f"{self.mother_initials}{self.father_initials}{date_sum}{sibling_factor}"

    def set_user_age(self, age):
        self.age = age

    def set_player_exp(self, years):
        self.player_exp = years

    def set_coach_exp(self, years):
        self.coach_exp = years

    def set_watch_exp(self, years):
        self.watch_exp = years

    def set_user_license(self, license):
        self.license = license

    def set_user_gender(self, gender):
        self.gender = gender


class WelcomeScreen(Screen):
    """Initial welcome screen of the app with keyboard support."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard_bound = False

    def on_enter(self, *args):
        """Called when screen is displayed. Set up keyboard and focus Next button."""
        if not self._keyboard_bound:
            Window.bind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = True

        # Focus the Next button automatically
        if 'btn_next' in self.ids:
            self.ids.btn_next.focus = True
            print("[KEYBOARD NAV] WelcomeScreen: Next button focused")

    def on_leave(self, *args):
        """Called when leaving screen. Clean up keyboard binding."""
        if self._keyboard_bound:
            Window.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = False

        # Remove focus
        if 'btn_next' in self.ids:
            self.ids.btn_next.focus = False

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        """Handle keyboard input."""
        # Only handle keyboard events when this screen is active
        if App.get_running_app().root.current != 'welcome':
            return False

        # Get key name from scancode
        from kivy.core.window import Keyboard
        keycode = Keyboard.keycode_to_string(Window._system_keyboard, key)

        print(f"[KEYBOARD NAV] WelcomeScreen key pressed: {keycode}")

        if keycode in ('enter', 'numpadenter', 'spacebar', 'space'):
            # Activate the Next button
            if 'btn_next' in self.ids:
                print("[KEYBOARD NAV] WelcomeScreen: Activating Next button")
                self.ids.btn_next.dispatch('on_release')
            return True

        return False

class LoginScreen(Screen):
    """
    Screen for checking if user has participated before.
    If yes, prompts for user_id and validates it exists in user_data.
    If no, shows message before proceeding to questionnaire.
    Supports keyboard navigation via Tab key.
    """
    has_participated = BooleanProperty(None, allownone=True)  # None=not selected, True=Yes, False=No
    user_id_input = StringProperty('')  # User's typed user_id
    user_id_exists = BooleanProperty(False)  # Whether the user_id exists in user_data

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focusable_widgets = []
        self.current_focus_index = -1
        self._keyboard_bound = False

    def participation_clicked(self, instance, value, participated):
        """Handle participation button click."""
        if value == "down":
            self.has_participated = participated

    def user_id_input_changed(self, instance, value):
        """Handle user_id input and check if it exists in user_data."""
        self.user_id_input = value.lower()  # Convert to lowercase

        # Check if user_data file exists for this user_id
        if self.user_id_input:
            try:
                user_data_files = os.listdir('user_data')
                user_ratings_files = os.listdir('user_ratings')
                # Check if any file starts with this user_id followed by underscore
                self.user_id_exists = any(
                    f.startswith(f"{self.user_id_input}_")
                    for f in user_ratings_files
                )
            except FileNotFoundError:
                self.user_id_exists = False
        else:
            self.user_id_exists = False

    def on_enter(self, *args):
        """Called when screen is displayed. Set up keyboard and focus order."""
        if not self._keyboard_bound:
            Window.bind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = True

        self._build_focus_order()
        print(f"[KEYBOARD NAV] LoginScreen: Initialized with {len(self.focusable_widgets)} focusable widgets")
        # Set initial focus to first widget
        if self.focusable_widgets:
            self.set_focus(0)

    def on_leave(self, *args):
        """Called when leaving screen. Clean up keyboard binding."""
        if self._keyboard_bound:
            Window.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = False

    def _build_focus_order(self):
        """Build ordered list of focusable widgets based on screen layout."""
        self.focusable_widgets = [
            # Participation toggle buttons
            self.ids.get('btn_participated_yes'),
            self.ids.get('btn_participated_no'),
            # User ID input (if shown)
            self.ids.get('input_user_id'),
            # Navigation buttons
            self.ids.get('btn_back'),
            self.ids.get('btn_next')
        ]
        # Filter out None values
        self.focusable_widgets = [w for w in self.focusable_widgets if w is not None]

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        """Handle keyboard input."""
        # Only handle keyboard events when this screen is active
        if App.get_running_app().root.current != 'login':
            return False

        # Get key name from scancode
        from kivy.core.window import Keyboard
        keycode = Keyboard.keycode_to_string(Window._system_keyboard, key)

        print(f"[KEYBOARD NAV] LoginScreen key pressed: {keycode}")

        if keycode == 'tab':
            # Tab moves focus forward, Shift+Tab moves backward
            if 'shift' in modifiers:
                self.focus_previous()
            else:
                self.focus_next()
            return True

        elif keycode in ('enter', 'numpadenter', 'spacebar', 'space'):
            # Activate currently focused widget
            self.activate_focused_widget()
            return True

        return False

    def focus_next(self):
        """Move focus to next widget."""
        if not self.focusable_widgets:
            return
        self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_widgets)
        self.set_focus(self.current_focus_index)

    def focus_previous(self):
        """Move focus to previous widget."""
        if not self.focusable_widgets:
            return
        self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_widgets)
        self.set_focus(self.current_focus_index)

    def set_focus(self, index):
        """Set focus to widget at given index."""
        if not self.focusable_widgets or index < 0 or index >= len(self.focusable_widgets):
            return

        # Remove focus from all widgets
        for widget in self.focusable_widgets:
            if widget:
                widget.focus = False

        # Set focus to target widget
        self.current_focus_index = index
        widget = self.focusable_widgets[index]
        if widget:
            widget.focus = True
            print(f"[KEYBOARD NAV] LoginScreen: Focus set to widget {index}")

    def activate_focused_widget(self):
        """Activate (click) the currently focused widget."""
        if self.current_focus_index < 0 or self.current_focus_index >= len(self.focusable_widgets):
            return

        widget = self.focusable_widgets[self.current_focus_index]
        if not widget:
            return

        print(f"[KEYBOARD NAV] LoginScreen: Activating widget")

        # Handle different widget types
        if isinstance(widget, ToggleButton):
            # Handle group behavior manually
            if widget.group:
                for other_widget in self.focusable_widgets:
                    if (isinstance(other_widget, ToggleButton) and
                        other_widget.group == widget.group and
                        other_widget != widget):
                        other_widget.state = 'normal'
            widget.state = 'down'

        elif isinstance(widget, Button):
            widget.dispatch('on_release')

    def proceed_next(self):
        """Handle Next button click."""
        if self.has_participated is None:
            # User hasn't selected Yes/No yet
            Popup(
                title="Selection Required",
                content=Label(text="Please indicate whether you have participated before."),
                size_hint=(0.6, 0.3)
            ).open()
            return

        if self.has_participated:
            # User has participated - check if user_id is valid
            if not self.user_id_input:
                Popup(
                    title="User ID Required",
                    content=Label(text="Please enter your user ID."),
                    size_hint=(0.6, 0.3)
                ).open()
                return

            if not self.user_id_exists:
                Popup(
                    title="User ID Not Found",
                    content=Label(text="This user ID was not found in our records.\nPlease check your ID or select 'No' if this is your first time."),
                    size_hint=(0.6, 0.4)
                ).open()
                return

            # Valid returning user - set user_id and go to video player
            App.get_running_app().user.user_id = self.user_id_input
            App.get_running_app().root.current = 'videoplayer'
        else:
            # New user - go to questionnaire
            App.get_running_app().root.current = 'questionnaire'

class QuestionnaireScreen(Screen):
    """
    Screen for collecting user demographic and experience information.
    Dynamically builds form based on config.yaml questionnaire_fields.
    Supports keyboard navigation via Tab key.
    """
    user_id_confirmed = BooleanProperty(False)  # Track whether user_id has been displayed
    display_user_id = StringProperty('')  # Store user_id for display

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focusable_widgets = []  # Will be populated in on_enter
        self.current_focus_index = -1
        self._keyboard_bound = False
        self.field_configs = []  # Will store active field configurations
        self.field_widgets = {}  # Will store references to field widgets

        # Load configuration from YAML file
        try:
            with open('config.yaml', 'r') as file:
                config_data = yaml.safe_load(file)

            # Load questionnaire fields configuration
            all_fields = config_data.get('questionnaire_fields', [])
            # Filter only active fields
            self.field_configs = [field for field in all_fields if field.get('active', False)]

        except FileNotFoundError:
            print("[ERROR] config.yaml file not found.")
        except KeyError as e:
            print(f"[ERROR] Missing key in config.yaml: {e}.")

    def build_questionnaire_form(self):
        """
        Dynamically build questionnaire form widgets based on configuration.
        Called after the .kv file is loaded to populate the form_container.
        Calculates optimal widget heights to fill available screen space.
        """
        if 'form_container' not in self.ids:
            print("[ERROR] form_container not found in .kv file")
            return

        container = self.ids.form_container
        container.clear_widgets()

        # Count total number of rows we'll create
        # (accounts for grouped fields being in one row)
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
        # Available space = screen height - header (48dp) - nav buttons (60dp) - padding
        # Minimum row height = 55dp for readability
        # Maximum row height = 80dp to prevent excessive spacing
        if num_rows > 0:
            available_height = self.height - 48 - 60 - 40  # header, buttons, padding
            calculated_height = available_height / num_rows
            row_height = max(55, min(80, calculated_height))
        else:
            row_height = 60

        for idx, field_config in enumerate(self.field_configs):
            field_type = field_config.get('type', 'text')
            field_name = field_config.get('field_name', f'field_{idx}')
            title = field_config.get('title', '')
            hint_text = field_config.get('hint_text', '')
            max_length = field_config.get('max_length', None)
            group = field_config.get('group', None)

            if field_type == 'multiple_choice':
                # Create a row with label and toggle buttons
                row = BoxLayout(size_hint_y=None, height=row_height, spacing=10, padding=[5, 5])

                if title:
                    label = Label(
                        text=title,
                        font_size=self.height/45,
                        size_hint_x=0.4,
                        halign='right',
                        valign='middle',
                        text_size=(None, None)
                    )
                    label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
                    row.add_widget(label)

                # Create button container
                button_container = BoxLayout(size_hint_x=0.6 if title else 1.0, spacing=5)

                options = field_config.get('options', [])
                group_name = f'group_{field_name}'

                self.field_widgets[field_name] = []
                for option in options:
                    btn = FocusableToggleButton(
                        text=str(option),
                        font_size=self.height/45
                    )
                    btn.group = group_name
                    btn.bind(state=lambda inst, val, fn=field_name, opt=option:
                            self._set_field_value(fn, opt) if val == 'down' else None)
                    button_container.add_widget(btn)
                    self.field_widgets[field_name].append(btn)

                row.add_widget(button_container)
                container.add_widget(row)

            elif field_type in ('text', 'numeric'):
                # Handle grouped fields (like birthday with multiple inputs)
                if group:
                    # Check if we need to create a new group row
                    group_key = f'group_row_{group}'
                    if group_key not in self.field_widgets:
                        # Create new group row
                        row = BoxLayout(size_hint_y=None, height=row_height, spacing=5, padding=[5, 5])

                        # Find the first field in this group to get the title
                        first_field = next((f for f in self.field_configs if f.get('group') == group and f.get('title')), None)
                        if first_field and first_field.get('title'):
                            label = Label(
                                text=first_field.get('title'),
                                font_size=self.height/45,
                                size_hint_x=0.25,
                                halign='right',
                                valign='middle',
                                text_size=(None, None)
                            )
                            label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
                            row.add_widget(label)

                        self.field_widgets[group_key] = row
                        container.add_widget(row)
                    else:
                        row = self.field_widgets[group_key]

                    # Add input to group row
                    text_input = FocusableTextInput(
                        hint_text=hint_text,
                        font_size=self.height/45,
                        multiline=False,
                        input_filter='int' if field_type == 'numeric' else None,
                        padding=[10, 5]  # Minimal vertical padding
                    )
                    if max_length:
                        text_input.bind(text=lambda inst, val, ml=max_length:
                                      setattr(inst, 'text', val[:ml]) if len(val) > ml else None)

                    text_input.bind(text=lambda inst, val, fn=field_name:
                                  self._set_field_value(fn, val))
                    row.add_widget(text_input)
                    self.field_widgets[field_name] = text_input
                else:
                    # Single text input
                    text_input = FocusableTextInput(
                        hint_text=hint_text,
                        font_size=self.height/45,
                        size_hint_y=None,
                        height=row_height - 10,  # Slightly smaller to account for padding
                        multiline=False,
                        input_filter='int' if field_type == 'numeric' else None,
                        padding=[10, 5]  # Minimal vertical padding
                    )
                    if max_length:
                        text_input.bind(text=lambda inst, val, ml=max_length:
                                      setattr(inst, 'text', val[:ml]) if len(val) > ml else None)

                    text_input.bind(text=lambda inst, val, fn=field_name:
                                  self._set_field_value(fn, val))
                    container.add_widget(text_input)
                    self.field_widgets[field_name] = text_input

    def _set_field_value(self, field_name, value):
        """Set the value for a specific field and update User object."""
        user = App.get_running_app().user
        user.data[field_name] = value

        # Update legacy fields for backward compatibility
        if field_name == 'gender':
            user.set_user_gender(value)
        elif field_name == 'age':
            user.set_user_age(value)
        elif field_name == 'nationality':
            user.nationality = value
        elif field_name == 'player_exp':
            user.set_player_exp(value)
        elif field_name == 'coach_exp':
            user.set_coach_exp(value)
        elif field_name == 'watch_exp':
            user.set_watch_exp(value)
        elif field_name == 'license':
            user.set_user_license(value)
        elif field_name == 'mother_initials':
            user.mother_initials = value[:2].lower() if value else ''
            user.set_user_id()
        elif field_name == 'father_initials':
            user.father_initials = value[:2].lower() if value else ''
            user.set_user_id()
        elif field_name == 'siblings':
            try:
                user.siblings = int(value) if value else 0
            except ValueError:
                user.siblings = 0
            user.set_user_id()
        elif field_name == 'birth_day':
            try:
                user.birth_day = int(value) if value else 0
            except ValueError:
                user.birth_day = 0
            user.set_user_id()
        elif field_name == 'birth_month':
            try:
                user.birth_month = int(value) if value else 0
            except ValueError:
                user.birth_month = 0
            user.set_user_id()
        elif field_name == 'birth_year':
            try:
                user.birth_year = int(value) if value else 0
            except ValueError:
                user.birth_year = 0
            user.set_user_id()

    def on_enter(self, *args):
        """Called when screen is displayed. Set up keyboard and focus order."""
        if not self._keyboard_bound:
            Window.bind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = True

        # Build form on first entry or when height changes
        if not hasattr(self, '_form_built'):
            # Bind to height changes to rebuild form with correct proportions
            self.bind(height=self._on_height_change)
            self.build_questionnaire_form()
            self._form_built = True
            self._last_height = self.height

        self._build_focus_order()
        print(f"[KEYBOARD NAV] QuestionnaireScreen: Initialized with {len(self.focusable_widgets)} focusable widgets")
        # Set initial focus to first widget
        if self.focusable_widgets:
            self.set_focus(0)

    def _on_height_change(self, instance, height):
        """Rebuild form when screen height changes significantly."""
        if not hasattr(self, '_last_height'):
            self._last_height = height
            return

        # Only rebuild if height changed significantly (more than 10%)
        if abs(height - self._last_height) / self._last_height > 0.1:
            print(f"[INFO] Screen height changed from {self._last_height} to {height}, rebuilding form")
            self._last_height = height
            self.build_questionnaire_form()
            self._build_focus_order()

    def on_leave(self, *args):
        """Called when leaving screen. Clean up keyboard binding."""
        if self._keyboard_bound:
            Window.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard_bound = False

    def _build_focus_order(self):
        """Build ordered list of focusable widgets based on dynamic form layout."""
        if self.user_id_confirmed:
            # Confirmation panel - only buttons
            self.focusable_widgets = [
                self.ids.get('btn_back_to_form'),
                self.ids.get('btn_proceed_video')
            ]
        else:
            # Main form panel - collect all dynamically created widgets
            self.focusable_widgets = []

            # Add all field widgets in order
            for field_name, widget in self.field_widgets.items():
                # Skip group rows
                if field_name.startswith('group_row_'):
                    continue

                if isinstance(widget, list):
                    # Multiple choice - add all buttons
                    self.focusable_widgets.extend(widget)
                else:
                    # Single widget
                    self.focusable_widgets.append(widget)

            # Add navigation buttons
            back_btn = self.ids.get('btn_back')
            next_btn = self.ids.get('btn_next')
            if back_btn:
                self.focusable_widgets.append(back_btn)
            if next_btn:
                self.focusable_widgets.append(next_btn)

        # Filter out None values
        self.focusable_widgets = [w for w in self.focusable_widgets if w is not None]

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        """Handle keyboard input. Called before focused widget receives the key."""
        # Only handle keyboard events when this screen is active
        if App.get_running_app().root.current != 'questionnaire':
            return False

        # Get key name from scancode
        from kivy.core.window import Keyboard
        keycode = Keyboard.keycode_to_string(Window._system_keyboard, key)

        print(f"[KEYBOARD NAV] Key pressed: {keycode}, modifiers: {modifiers}")

        if keycode == 'tab':
            # Tab moves focus forward, Shift+Tab moves backward
            if 'shift' in modifiers:
                print("[KEYBOARD NAV] Moving focus backward")
                self.focus_previous()
            else:
                print("[KEYBOARD NAV] Moving focus forward")
                self.focus_next()
            return True  # Consume event

        elif keycode in ('enter', 'numpadenter', 'spacebar', 'space'):
            # Activate currently focused widget
            print(f"[KEYBOARD NAV] Activation key detected: {keycode}")
            self.activate_focused_widget()
            return True  # Consume event

        return False  # Don't consume other keys

    def focus_next(self):
        """Move focus to next widget."""
        if not self.focusable_widgets:
            return

        self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_widgets)
        self.set_focus(self.current_focus_index)

    def focus_previous(self):
        """Move focus to previous widget."""
        if not self.focusable_widgets:
            return

        self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_widgets)
        self.set_focus(self.current_focus_index)

    def set_focus(self, index):
        """Set focus to widget at given index."""
        if not self.focusable_widgets or index < 0 or index >= len(self.focusable_widgets):
            return

        # Remove focus from all widgets
        for widget in self.focusable_widgets:
            if widget:
                widget.focus = False

        # Set focus to target widget
        self.current_focus_index = index
        widget = self.focusable_widgets[index]
        if widget:
            widget.focus = True
            print(f"[KEYBOARD NAV] Focus set to widget {index}: {widget} (id: {widget.id if hasattr(widget, 'id') else 'no id'})")

    def activate_focused_widget(self):
        """Activate (click) the currently focused widget."""
        if self.current_focus_index < 0 or self.current_focus_index >= len(self.focusable_widgets):
            return

        widget = self.focusable_widgets[self.current_focus_index]
        if not widget:
            return

        print(f"[KEYBOARD NAV] Activating widget: {widget}, type: {type(widget)}")

        # Handle different widget types
        if isinstance(widget, ToggleButton):
            print(f"[KEYBOARD NAV] ToggleButton current state: {widget.state}, group: {widget.group}")

            # Handle group behavior manually
            if widget.group:
                # Deselect all other buttons in the same group
                for other_widget in self.focusable_widgets:
                    if (isinstance(other_widget, ToggleButton) and
                        other_widget.group == widget.group and
                        other_widget != widget):
                        print(f"[KEYBOARD NAV] Deselecting {other_widget.group} button")
                        other_widget.state = 'normal'

            # Toggle or set the focused button to 'down'
            widget.state = 'down'
            print(f"[KEYBOARD NAV] ToggleButton new state: {widget.state}")

        elif isinstance(widget, Button):
            print(f"[KEYBOARD NAV] Regular button - dispatching on_release")
            # For regular buttons, trigger the on_release event
            widget.dispatch('on_release')
        # TextInput doesn't need activation - user types directly

    # Note: Field value callbacks are now handled by _set_field_value method

    def show_user_id_confirmation(self):
        """
        Display the user_id confirmation panel without saving data yet.
        Data will only be saved when user clicks 'Understood. Proceed'.
        """
        user = App.get_running_app().user
        self.display_user_id = user.user_id
        self.user_id_confirmed = True
        # Rebuild focus order for confirmation panel
        self._build_focus_order()
        if self.focusable_widgets:
            self.set_focus(0)

    def back_to_form(self):
        """Go back to the questionnaire form to allow editing."""
        self.user_id_confirmed = False
        # Rebuild focus order for form panel
        self._build_focus_order()
        if self.focusable_widgets:
            self.set_focus(0)

    def save_user_data(self):
        """
        Save user demographic data to a timestamped JSON file.
        Creates user_data directory if it doesn't exist.
        Saves both legacy fields and all dynamic field data.
        """
        try:
            user = App.get_running_app().user
            os.makedirs('user_data', exist_ok=True)

            ts = datetime.now().astimezone()
            filename = f"{user.user_id}.json"
            path = os.path.join('user_data', filename)

            # Build data dict with legacy fields and all dynamic fields
            data = {
                'user_id': user.user_id,
                'gender': user.gender,
                'age': user.age,
                'nationality': user.nationality,
                'license': user.license,
                'player_exp': user.player_exp,
                'coach_exp': user.coach_exp,
                'watch_exp': user.watch_exp,
                'saved_at': ts.isoformat(timespec='seconds')
            }

            # Add all dynamic field data
            data.update(user.data)

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[INFO] User data saved: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save user data: {e}")

    def proceed_to_video(self):
        """Save data and navigate to video player screen after user confirms they memorized their ID."""
        self.save_user_data()
        App.get_running_app().root.current = 'videoplayer'


class VideoPlayerScreen(Screen):
    """
    Main screen for video playback and rating collection.
    Displays soccer action videos with customizable rating scales.
    Allows marking actions as "not recognized".
    """
    # Dynamic rating storage - keys are scale titles, values are the ratings
    scale_values = DictProperty({})
    action_not_recognized = BooleanProperty(False)
    has_any_rating = BooleanProperty(False)

    # Screen dimension properties (configurable via config.yaml)
    metadata_display_height = NumericProperty(0.08)
    video_player_height = NumericProperty(0.56)
    control_buttons_height = NumericProperty(0.08)
    rating_scales_height = NumericProperty(0.28)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0  # Current video index
        self.scale_configs = []  # Will store active scale configurations
        self.scale_widgets = {}  # Will store references to scale widget groups
        self.required_scales = []  # Will store titles of scales that are required

        try:
            # Load configuration from YAML file
            with open('config.yaml', 'r') as file:
                config_data = yaml.safe_load(file)

            db_path = config_data['paths']['db_path']
            self.path_videos = config_data['paths']['video_path']
            min_ratings_per_video = config_data['settings']['min_ratings_per_video']

            # Load screen dimensions configuration
            screen_dims = config_data.get('screen_dimensions', {})
            self.metadata_display_height = screen_dims.get('metadata_display_height', 0.08)
            self.video_player_height = screen_dims.get('video_player_height', 0.56)
            self.control_buttons_height = screen_dims.get('control_buttons_height', 0.08)
            self.rating_scales_height = screen_dims.get('rating_scales_height', 0.28)

            # Load rating scales configuration
            all_scales = config_data.get('rating_scales', [])
            # Filter only active scales
            self.scale_configs = [scale for scale in all_scales if scale.get('active', False)]

            # Track which scales are required for proceeding
            # Default to required if not specified
            self.required_scales = [
                scale.get('title') for scale in self.scale_configs
                if scale.get('required_to_proceed', True)
            ]

            # Initialize scale_values dictionary with None for each active scale
            for scale in self.scale_configs:
                self.scale_values[scale['title']] = None

        except FileNotFoundError:
            print("[ERROR] config.yaml file not found.")
        except KeyError as e:
            print(f"[ERROR] Missing key in config.yaml: {e}.")

        # Get list of all MP4 files in the video directory
        try:
            all_videos = [f for f in os.listdir(self.path_videos) if f.lower().endswith('.mp4')]
        except FileNotFoundError:
            print(f"[ERROR] Video directory not found: {self.path_videos}")
            all_videos = []

        
        user_id = App.get_running_app().user.user_id or 'unknown'
        
        # Get list of videos already rated by this user
        videos_rated_by_user = [f.replace('.json', '').replace(user_id+'_', '') for f in os.listdir('user_ratings') if user_id+'_' in f]
        # Filter out already rated videos
        unrated_videos = [v for v in all_videos if v.replace('.mp4', '') not in videos_rated_by_user]
        
        # count number of ratings per id
        rated_ids = [f.split('_')[1].replace('.json', '') for f in os.listdir('user_ratings') if f.endswith('.json')]
        rating_counts = pd.Series(rated_ids).value_counts()
        
        # get ids with more than N ratings
        videos_fullyrated = rating_counts[rating_counts >= min_ratings_per_video].index.tolist()

        self.videos = [v for v in unrated_videos if v.replace('.mp4', '') not in videos_fullyrated]
                    
        # Shuffle videos for randomization (currently disabled for pilot phase)
        random.shuffle(self.videos)

        # Load metadata from DuckDB database
        try:
            conn = duckdb.connect(db_path)

            # Convert list of video filenames to event IDs (removing .mp4 extension)
            event_id_str = ', '.join(f"'{event_id.replace('.mp4', '')}'" for event_id in self.videos)

            # Fetch metadata for all actions from included videos
            if event_id_str:  # Prevents empty "IN ()" clause
                query = f"SELECT * FROM events WHERE id IN ({event_id_str})"
                df_actions = conn.execute(query).fetchdf()
            else:
                # Create empty DataFrame with expected columns if no videos found
                df_actions = pd.DataFrame(columns=["id", "team", "player", "jersey_number", "type", "body_part", "start_x", "start_y", "end_x", "end_y"])

            self.metadata = df_actions

            # Close database connection to prevent resource leak
            conn.close()
        except Exception as e:
            print(f"[ERROR] Failed to load metadata from database: {e}")
            # Create empty DataFrame as fallback
            self.metadata = pd.DataFrame(columns=["id", "team", "player", "jersey_number", "type", "body_part", "start_x", "start_y", "end_x", "end_y"])

    def build_rating_scales(self):
        """
        Dynamically build rating scale widgets based on configuration.
        Called after the .kv file is loaded to populate the scales_container.
        """
        if 'scales_container' not in self.ids:
            print("[ERROR] scales_container not found in .kv file")
            return

        container = self.ids.scales_container
        container.clear_widgets()

        # Calculate size_hint_y for each scale based on number of active scales
        num_scales = len(self.scale_configs)
        if num_scales == 0:
            return

        # Allocate space proportionally for each scale
        scale_height = 1.0 / num_scales

        for idx, scale_config in enumerate(self.scale_configs):
            scale_type = scale_config.get('type', 'discrete')
            title = scale_config.get('title', f'Scale {idx+1}')
            label_low = scale_config.get('label_low', '')
            label_high = scale_config.get('label_high', '')

            # Create container for this scale
            scale_box = BoxLayout(
                orientation='vertical',
                size_hint_y=scale_height,
                padding=[10, 5, 10, 5]
            )

            # Add gray background
            with scale_box.canvas.before:
                Color(100/255, 100/255, 100/255, 1)
                rect = Rectangle(pos=scale_box.pos, size=scale_box.size)
                scale_box.bind(pos=lambda inst, val, r=rect: setattr(r, 'pos', val),
                              size=lambda inst, val, r=rect: setattr(r, 'size', val))

            # Top row: Title (25%) | Scale widgets (75%)
            top_row = BoxLayout(size_hint_y=0.7, spacing=10)

            # Title label on the left (25% width)
            title_label = Label(
                text=f'{title}:',
                font_size=self.height/40,
                size_hint_x=0.2,
                halign='right',
                valign='middle',
                text_size=(None, None)
            )
            title_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
            top_row.add_widget(title_label)

            # Scale widgets container (75% width)
            scale_widget_box = BoxLayout(size_hint_x=0.8, spacing=6)

            if scale_type == 'discrete':
                # Discrete scale with toggle buttons
                values = scale_config.get('values', [1, 2, 3, 4, 5, 6, 7])
                group_name = f'scale_{idx}'
                self.scale_widgets[title] = []

                for value in values:
                    btn = ToggleButton(
                        text=str(value),
                        group=group_name
                    )
                    btn.bind(state=lambda inst, val, t=title, v=value:
                            self.set_scale_value(t, v) if val == 'down' else None)
                    scale_widget_box.add_widget(btn)
                    self.scale_widgets[title].append(btn)

            elif scale_type == 'slider':
                # Slider scale
                slider_min = scale_config.get('slider_min', 0)
                slider_max = scale_config.get('slider_max', 100)

                slider = Slider(
                    min=slider_min,
                    max=slider_max,
                    value=(slider_min + slider_max) / 2,
                    orientation='horizontal'
                )

                slider.bind(value=lambda inst, val, t=title: self.set_scale_value(t, val))

                scale_widget_box.add_widget(slider)
                self.scale_widgets[title] = [slider]

            elif scale_type == 'text':
                # Text input
                text_input = TextInput(
                    multiline=False,
                    hint_text='Enter your response...'
                )
                text_input.bind(text=lambda inst, val, t=title: self.set_scale_value(t, val))
                scale_widget_box.add_widget(text_input)
                self.scale_widgets[title] = [text_input]

            # Add scale widgets to top row
            top_row.add_widget(scale_widget_box)
            scale_box.add_widget(top_row)

            # Bottom row: Empty spacer (20%) | Low/High labels (80%)
            bottom_row = BoxLayout(size_hint_y=0.3, spacing=10)

            # Empty spacer on the left (20% width to align with title)
            bottom_row.add_widget(Label(text='', size_hint_x=0.2))

            # Labels container (80% width to align with scale widgets)
            labels_box = BoxLayout(size_hint_x=0.8)

            # Low label - aligned to the left edge
            low_label = Label(
                text=label_low,
                font_size=self.height/75,
                halign='left',
                valign='middle',
                padding=(5, 0)
            )
            low_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
            labels_box.add_widget(low_label)

            # Spacer in the middle
            labels_box.add_widget(Label(text=''))

            # High label - aligned to the right edge
            high_label = Label(
                text=label_high,
                font_size=self.height/75,
                halign='right',
                valign='middle',
                padding=(0, 5)
            )
            high_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
            labels_box.add_widget(high_label)

            bottom_row.add_widget(labels_box)
            scale_box.add_widget(bottom_row)

            container.add_widget(scale_box)

    def set_scale_value(self, scale_title, value):
        """Set the value for a specific scale and update has_any_rating property."""
        self.scale_values[scale_title] = value
        # Update has_any_rating - require only REQUIRED scales to have values
        # or if action_not_recognized is True
        if self.action_not_recognized:
            self.has_any_rating = True
        else:
            self.has_any_rating = all(
                self.scale_values.get(title) is not None and self.scale_values.get(title) != ''
                for title in self.required_scales
            )

    def on_enter(self, *args):
        """Called when this screen is displayed. Builds scales and loads the first/next video."""
        # Build rating scales on first entry
        if not hasattr(self, '_scales_built'):
            self.build_rating_scales()
            self._scales_built = True
        self.load_video()

    def previous_video(self, instance):
        """Placeholder for going back to previous video (not implemented)."""
        pass

    def confirm_back_to_questionnaire(self):
        """Show confirmation dialog before navigating back to questionnaire."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='Are you sure you want to go back?\nAny unsaved ratings will be lost.'))

        button_layout = BoxLayout(spacing=10, size_hint_y=0.3)

        popup = Popup(title='Confirm Navigation', content=content, size_hint=(0.7, 0.4))

        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_release=popup.dismiss)

        confirm_btn = Button(text='Go Back')
        confirm_btn.bind(on_release=lambda x: self._navigate_back(popup))

        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(confirm_btn)
        content.add_widget(button_layout)

        popup.open()

    def _navigate_back(self, popup):
        """Navigate back to questionnaire and close popup."""
        popup.dismiss()
        App.get_running_app().root.current = 'questionnaire'

    def reset_scales(self):
        """
        Reset all rating scale widgets to their default state and clear all ratings.
        Called before loading a new video.
        """
        # Reset each scale based on its type
        for title, widgets in self.scale_widgets.items():
            scale_config = next((s for s in self.scale_configs if s['title'] == title), None)
            if not scale_config:
                continue

            scale_type = scale_config.get('type', 'discrete')

            if scale_type == 'discrete':
                # Reset all toggle buttons to 'normal' state
                for btn in widgets:
                    btn.state = 'normal'
            elif scale_type == 'slider':
                # Reset slider to middle value
                slider = widgets[0]
                slider_min = scale_config.get('slider_min', 0)
                slider_max = scale_config.get('slider_max', 100)
                slider.value = (slider_min + slider_max) / 2
            elif scale_type == 'text':
                # Clear text input
                widgets[0].text = ''

        # Reset all scale values to None
        for title in self.scale_values.keys():
            self.scale_values[title] = None

        # Reset has_any_rating flag
        self.has_any_rating = False

        # Reset "action not recognized" button
        if 'btn_notrec' in self.ids:
            self.ids.btn_notrec.state = 'normal'
        self.action_not_recognized = False




    def load_video(self):
        """
        Load the next unrated video for the current user.
        Skips videos that have already been rated. Displays metadata about the action
        (team, player, type, body part). When all videos are rated, displays a message.
        """
        while self.index < len(self.videos):
            video_file = self.videos[self.index]
            action_id = os.path.splitext(os.path.basename(video_file))[0]

            # Load video and start playback
            self.ids.video_player.source = os.path.join(self.path_videos, video_file)
            self.ids.video_player.state = 'play'

            # Load and display metadata for this action
            self.action_id = action_id
            row = self.metadata[self.metadata['id'] == str(self.action_id)]

            if not row.empty:
                self.ids.team_label.text = str(row.team.values[0])
                self.ids.player_label.text = str(row.player.values[0])
                self.ids.jerseynumber_label.text = f"Number: {str(row.jersey_number.values[0])}"
                self.ids.type_label.text = str(row.type.values[0])

                self.ids.bodypart_label.text = str(row.bodypart.values[0]) 
                # Store trajectory coordinates as instance variables
                self.start_x = row.start_x.values[0]
                self.start_y = row.start_y.values[0]
                self.end_x = row.end_x.values[0]
                self.end_y = row.end_y.values[0]
            else:
                # Display placeholder text if no metadata found
                self.ids.team_label.text = 'No Team'
                self.ids.player_label.text = 'No Player'
                self.ids.type_label.text = 'No Type'
                self.ids.bodypart_label.text = ''

                # Default coordinates if no metadata
                self.start_x = 10
                self.start_y = 10
                self.end_x = 90
                self.end_y = 10

            # Clear previous plot
            self.ids.plot_container.clear_widgets()

            # Create pitch and draw trajectory
            pitch = mplsoccer.Pitch(pitch_type="statsbomb", pitch_color="grass")
            fig, ax = pitch.draw(figsize=(6, 4))

            # Make figure background transparent/black
            fig.patch.set_facecolor('black')
            fig.patch.set_alpha(1)

            # Draw arrow from start to end position
            pitch.arrows(self.start_x, self.start_y, self.end_x, self.end_y,
                        ax=ax, color="blue", width=2, headwidth=10, headlength=5)

            # Optionally add markers at start and end
            ax.plot(self.start_x, self.start_y, 'o', color='blue', markersize=10, label='Start')

            # Remove white padding
            fig.tight_layout(pad=0)
            fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

            # Save figure to BytesIO buffer as PNG
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
            buf.seek(0)

            # Create Kivy Image from buffer
            core_image = CoreImage(buf, ext='png')
            kivy_image = KivyImage(texture=core_image.texture)
            self.ids.plot_container.add_widget(kivy_image)

            plt.close(fig)  # Prevent memory leak

            self.reset_scales()
            self.ids.submit_button.opacity = 1
            self.index += 1
            return

        # All videos have been rated
        self.ids.info_label.text = "No more videos to rate."
        self.ids.video_player.opacity = 0
        self.ids.submit_button.opacity = .5


    def submit_rating(self):
        """
        Save the current ratings to a JSON file and load the next video.
        Validates that all ratings are provided or 'not recognized' is checked.
        """
        # Check if ALL scales have values (not None and not empty string)
        has_all_ratings = all(
            value is not None and value != ''
            for value in self.scale_values.values()
        )

        # Block submission if not all ratings given and action not marked as unrecognized
        if not has_all_ratings and not self.action_not_recognized:
            Popup(
                title="Incomplete Ratings",
                content=Label(text="Please provide ratings for all scales or mark the action as not recognized."),
                size_hint=(0.6, 0.3)
            ).open()
            return

        try:
            os.makedirs('user_ratings', exist_ok=True)

            # Build rating data with dynamic scale values
            rating_data = {
                'user_id': App.get_running_app().user.user_id,
                'id': self.action_id,
                'action_not_recognized': self.action_not_recognized
            }

            # Add each scale's value to the rating data
            for title, value in self.scale_values.items():
                # Use title as key (sanitized for JSON compatibility)
                key = title.lower().replace(' ', '_')
                rating_data[key] = value

            # Save rating data to a JSON file named: {user_id}_{action_id}.json
            filename = os.path.join('user_ratings', f"{App.get_running_app().user.user_id}_{self.action_id}.json")
            with open(filename, 'w') as f:
                json.dump(rating_data, f, indent=2)

            # Print ratings for debugging
            ratings_str = ', '.join(f"{title}: {value}" for title, value in self.scale_values.items())
            print(f"Ratings -> {ratings_str}")

            self.load_video()
        except Exception as e:
            print(f"[ERROR] Failed to save rating: {e}")
            Popup(
                title="Error",
                content=Label(text=f"Failed to save rating: {e}"),
                size_hint=(0.6, 0.3)
            ).open()



class RatingApp(App):
    """
    Main application class for the Creativity Rating App.
    Manages the User object and creates the screen manager with three screens:
    welcome, questionnaire, and videoplayer.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = User()  # Create a User instance shared across all screens

    def build(self):
        """Build and return the main screen manager with all screens."""
        screen_manager = ScreenManager(transition=FadeTransition())

        screen_manager.add_widget(WelcomeScreen(name = "welcome"))
        screen_manager.add_widget(LoginScreen(name="login"))
        screen_manager.add_widget(QuestionnaireScreen(name="questionnaire"))
        screen_manager.add_widget(VideoPlayerScreen(name="videoplayer"))

        return screen_manager

    def on_stop(self):
        """
        Called when the application is terminated.
        Triggers the write_ratings2csv script to export data and create log file.
        """
        try:
            import write_ratings2csv
            print("[INFO] Exporting ratings and generating log file...")
        except Exception as e:
            print(f"[ERROR] Failed to run write_ratings2csv: {e}")


if __name__ == '__main__':
    RatingApp().run()
