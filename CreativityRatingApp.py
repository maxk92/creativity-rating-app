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
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, CardTransition, SwapTransition, WipeTransition, FallOutTransition
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.core.window import Window
import random
from pathlib import Path
from datetime import datetime
import duckdb
import yaml
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import mplsoccer

kivy.require("1.9.1")

# Set window to fullscreen
Window.fullscreen = 'auto'

class User:
    """
    Stores demographic and experience data for a user/rater.
    User ID is constructed from parent name initials, birthdate, birth year, and siblings.
    Formula: mother_initials + father_initials + (day+month) + (cross_sum_of_year * (siblings+1))
    """
    def __init__(self):
        self.user_id = ''
        self.gender = 'Not specified'
        self.age = 0
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
    """Initial welcome screen of the app."""
    pass

class LoginScreen(Screen):
    """
    Screen for checking if user has participated before.
    If yes, prompts for user_id and validates it exists in user_data.
    If no, shows message before proceeding to questionnaire.
    """
    has_participated = BooleanProperty(None, allownone=True)  # None=not selected, True=Yes, False=No
    user_id_input = StringProperty('')  # User's typed user_id
    user_id_exists = BooleanProperty(False)  # Whether the user_id exists in user_data

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
                # Check if any file starts with this user_id followed by underscore
                self.user_id_exists = any(
                    f.startswith(f"{self.user_id_input}_")
                    for f in user_data_files
                )
            except FileNotFoundError:
                self.user_id_exists = False
        else:
            self.user_id_exists = False

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
    Captures gender, age, soccer experience (as player, coach, watcher), and license info.
    """
    user_id_confirmed = BooleanProperty(False)  # Track whether user_id has been displayed
    display_user_id = StringProperty('')  # Store user_id for display

    def gender_clicked(self, instance, value, gender):
        """Handle gender button click (when button is pressed down)."""
        if value == "down":
            App.get_running_app().user.set_user_gender(gender)

    def age_input(self, instance, value):
        App.get_running_app().user.set_user_age(value)

    def player_exp_input(self, instance, value):
        App.get_running_app().user.set_player_exp(value)

    def coach_exp_input(self, instance, value):
        App.get_running_app().user.set_coach_exp(value)

    def watch_exp_input(self, instance, value):
        App.get_running_app().user.set_watch_exp(value)

    def mother_initials_input(self, instance, value):
        """Handle mother's initials input (first two letters, converted to lowercase)."""
        user = App.get_running_app().user
        user.mother_initials = value[:2].lower()  # Take only first 2 characters
        user.set_user_id()

    def father_initials_input(self, instance, value):
        """Handle father's initials input (first two letters, converted to lowercase)."""
        user = App.get_running_app().user
        user.father_initials = value[:2].lower()  # Take only first 2 characters
        user.set_user_id()

    def siblings_input(self, instance, value):
        """Handle number of siblings input."""
        user = App.get_running_app().user
        try:
            user.siblings = int(value) if value else 0
        except ValueError:
            user.siblings = 0
        user.set_user_id()

    def birth_day_input(self, instance, value):
        """Handle birth day input."""
        user = App.get_running_app().user
        try:
            user.birth_day = int(value) if value else 0
        except ValueError:
            user.birth_day = 0
        user.set_user_id()

    def birth_month_input(self, instance, value):
        """Handle birth month input."""
        user = App.get_running_app().user
        try:
            user.birth_month = int(value) if value else 0
        except ValueError:
            user.birth_month = 0
        user.set_user_id()

    def birth_year_input(self, instance, value):
        """Handle birth year input."""
        user = App.get_running_app().user
        try:
            user.birth_year = int(value) if value else 0
        except ValueError:
            user.birth_year = 0
        user.set_user_id()

    def license_clicked(self, instance, value, license):
        if value == "down":
            App.get_running_app().user.set_user_license(license)

    def show_user_id_confirmation(self):
        """
        Display the user_id confirmation panel without saving data yet.
        Data will only be saved when user clicks 'Understood. Proceed'.
        """
        user = App.get_running_app().user
        self.display_user_id = user.user_id
        self.user_id_confirmed = True

    def back_to_form(self):
        """Go back to the questionnaire form to allow editing."""
        self.user_id_confirmed = False

    def save_user_data(self):
        """
        Save user demographic data to a timestamped JSON file.
        Creates user_data directory if it doesn't exist.
        """
        try:
            user = App.get_running_app().user
            os.makedirs('user_data', exist_ok=True)

            ts = datetime.now().astimezone()
            filename = f"{user.user_id}.json"
            path = os.path.join('user_data', filename)

            with open(path, 'w') as f:
                json.dump({
                    'user_id': user.user_id,
                    'gender': user.gender,
                    'age': user.age,
                    'license': user.license,
                    'player_exp': user.player_exp,
                    'coach_exp': user.coach_exp,
                    'watch_exp': user.watch_exp,
                    'saved_at': ts.isoformat(timespec='seconds')
                }, f)
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
    Displays soccer action videos and collects ratings on three dimensions:
    creativity, technical correctness, and aesthetic appeal.
    Also allows marking actions as "not recognized".
    """
    # Kivy properties for tracking ratings (7-point Likert scale: 1-7)
    current_rating = NumericProperty(None, allownone=True)       # Creativity
    technical_rating = NumericProperty(None, allownone=True)     # Technical correctness
    aesthetic_rating = NumericProperty(None, allownone=True)     # Aesthetic appeal
    action_not_recognized = BooleanProperty(False)               # Action not recognized

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0  # Current video index

        try:
            # Load configuration from YAML file
            with open('config.yaml', 'r') as file:
                config_data = yaml.safe_load(file)

            db_path = config_data['paths']['db_path']
            self.path_videos = config_data['paths']['video_path']
            min_ratings_per_video = config_data['settings']['min_ratings_per_video']
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
        rated_ids = [f.split('_')[1].replace('.json', '') for f in os.listdir('user_ratings')]
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


    def on_enter(self, *args):
        """Called when this screen is displayed. Loads the first/next video."""
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

    def set_likert(self, value):
        """Set the creativity rating value."""
        self.current_rating = int(value)

    def set_likert_tech(self, value):
        """Set the technical correctness rating value."""
        self.technical_rating = int(value)

    def set_likert_aesthetic(self, value):
        """Set the aesthetic appeal rating value."""
        self.aesthetic_rating = int(value)

    def reset_likert(self):
        """
        Reset all rating buttons to their default state and clear all ratings.
        Called before loading a new video.
        """
        for btn_id in (
                'r_m3', 'r_m2', 'r_m1', 'r_0', 'r_p1', 'r_p2', 'r_p3',
                't_m3', 't_m2', 't_m1', 't_0', 't_p1', 't_p2', 't_p3',
                'a_m3', 'a_m2', 'a_m1', 'a_0', 'a_p1', 'a_p2', 'a_p3',
                'btn_notrec'
        ):
            if btn_id in self.ids:
                self.ids[btn_id].state = 'normal'

        self.current_rating = None
        self.technical_rating = None
        self.aesthetic_rating = None
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

            # Add canvas to Kivy
            canvas = FigureCanvasKivyAgg(fig)
            self.ids.plot_container.add_widget(canvas)

            plt.close(fig)  # Prevent memory leak

            self.reset_likert()
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
        Validates that either a creativity rating is provided or 'not recognized' is checked.
        """
        # Block submission if no creativity rating is given and action not marked as unrecognized
        if self.current_rating is None and not self.action_not_recognized:
            Popup(
                title="No Selection",
                content=Label(text="Please rate the creativity or mark the action as not recognized."),
                size_hint=(0.6, 0.3)
            ).open()
            return

        try:
            os.makedirs('user_ratings', exist_ok=True)

            rating_creativity = self.current_rating
            rating_technical  = self.technical_rating
            rating_aesthetic  = self.aesthetic_rating

            # Save rating data to a JSON file named: {user_id}_{action_id}.json
            filename = os.path.join('user_ratings', f"{App.get_running_app().user.user_id}_{self.action_id}.json")
            with open(filename, 'w') as f:
                json.dump({
                    'user_id' : App.get_running_app().user.user_id,
                    'id': self.action_id,
                    'action_rating' : rating_creativity,
                    'technical_correctness': rating_technical,
                    'aesthetic_appeal': rating_aesthetic,
                    'action_not_recognized': self.action_not_recognized
                }, f)

            print(f"Ratings -> creativity: {rating_creativity}, technical: {rating_technical}, aesthetic: {rating_aesthetic}")
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