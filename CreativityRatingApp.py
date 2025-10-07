import kivy
import pandas as pd
import os
os.environ['KIVY_VIDEO'] = 'ffpyplayer'
import json
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, CardTransition, SwapTransition, WipeTransition, FallOutTransition
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, BooleanProperty
import random
from pathlib import Path
from datetime import datetime
import duckdb
import yaml

kivy.require("1.9.1")

class User:
    def __init__(self):
        self.user_id = ''
        self.gender = 'Not specified'
        self.age = 0
        self.player_exp = 0
        self.coach_exp = 0
        self.watch_exp = 0
        self.license = 'Not specified'
        self.id_part1 = ''
        self.id_part2 = ''
        self.id_part3 = ''

    def set_user_id(self):
        preliminary_input = self.id_part1 + self.id_part2 + self.id_part3

        if preliminary_input == '':
            self.user_id = 'unknown'
        else:
            self.user_id = preliminary_input

    def set_user_age(self, age):
        self.age = age

    def set_player_exp(self, years):
        self.player_exp = years

    def set_coach_exp(self, years):
        self.coach_exp = years

    def set_watch_exp(self, years):
        self.watch_exp = years

    def set_user_player_exp(self, years):
        return self.set_player_exp(years)

    def set_user_coach_exp(self, years):
        return self.set_coach_exp(years)

    def set_user_watch_exp(self, years):
        return self.set_watch_exp(years)

    def set_user_license(self, license):
        self.license = license

    def set_user_gender(self, gender):
        self.gender = gender


class Action:
    def __init__(self, id, video_path, metadata, rating=0):
        self.id = id
        self.video_path = video_path
        self.metadata = metadata
        self.rating = rating


class WelcomeScreen(Screen):
    pass

class QuestionnaireScreen(Screen):

    def gender_clicked(self, instance, value, gender):
        if value == "down":
            App.get_running_app().user.set_user_gender(gender)

    def age_input(self, instance, value):
        App.get_running_app().user.set_user_age(value)

    def player_exp_input(self, instance, value):
        App.get_running_app().user.set_user_player_exp(value)

    def coach_exp_input(self, instance, value):
        App.get_running_app().user.set_user_coach_exp(value)

    def watch_exp_input(self, instance, value):
        App.get_running_app().user.set_user_watch_exp(value)

    def id_input_1(self, instance, value):
        App.get_running_app().user.id_part1 = value.lower()
        App.get_running_app().user.set_user_id()

    def id_input_2(self, instance, value):
        App.get_running_app().user.id_part2 = value.lower()
        App.get_running_app().user.set_user_id()

    def id_input_3(self, instance, value):
        if len(str(value)) == 1:
            value = '0' + str(value)
        else:
            value = str(value)
        App.get_running_app().user.id_part3 = value
        App.get_running_app().user.set_user_id()

    def license_clicked(self, instance, value, license):
        if value == "down":
            App.get_running_app().user.set_user_license(license)

    def save_user_data(self):
        user = App.get_running_app().user
        os.makedirs('user_data', exist_ok=True)

        ts = datetime.now().astimezone()
        filename = f"{user.user_id}_{ts.strftime('%Y%m%d_%H%M%S')}.json"
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


class VideoPlayerScreen(Screen):
    current_rating = NumericProperty(None, allownone=True)       # Creativity
    technical_rating = NumericProperty(None, allownone=True)     # Technical correctness
    aesthetic_rating = NumericProperty(None, allownone=True)     # Aesthetic appeal
    action_not_recognized = BooleanProperty(False)                          # Action not recognized

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0

        with open('config.yaml', 'r') as file:
            config_data = yaml.safe_load(file)
       
        db_path = config_data['paths']['db_path']
        self.path_videos = config_data['paths']['video_path']

        self.videos = [f for f in os.listdir(self.path_videos) if f.lower().endswith('.mp4')]
        # allow nested folder structure for videos
        #base = os.path.abspath(self.path_videos)
        #for root, dirs, files in os.walk(self.path_videos):
        #    if os.path.abspath(root) == base:
        #        continue
        #    for f in files:
        #        if f.lower().endswith('.mp4'):
        #            self.videos.append(os.path.join(root, f))

        random.seed(42)
        ########################################################
        #### !!!! wieder rein, wenn Pilotierung vorbei !!!! ####
        ########################################################
        
        #random.shuffle(self.videos)

        # Load metadata from CSV
        #self.path_metadata = '/Users/Esther/Desktop/creativity-rating-app-main/meta_data'
        #meta = Path(self.path_metadata)
        #csv_paths = sorted(meta.glob("[!.]*.csv"))
        #self.ls_matches = [p.stem for p in csv_paths]
        #self.metadata = pd.concat([pd.read_csv(p) for p in csv_paths], ignore_index=True)
    
        # Load metadata from DB
        conn = duckdb.connect(db_path)

        # Convert list of match ids to comma-separated string
        event_id_str = ', '.join(f"'{event_id.replace('.mp4', '')}'" for event_id in self.videos)

        # fetch df for all actions from included videos
        if event_id_str:  # << verhindert "IN ()"
            query = f"SELECT * FROM events WHERE id IN ({event_id_str})"
            df_actions = conn.execute(query).fetchdf()
        else:
            # leeres DF mit den Spalten, die später verwendet werden
            df_actions = pd.DataFrame(columns=["id", "team", "player", "type", "shot_body_part", "pass_body_part"])

        self.metadata = df_actions


    def on_enter(self, *args):
        self.load_video()

    def previous_video(self, instance):
        pass

    def set_likert(self, value):
        self.current_rating = int(value)

    def set_likert_tech(self, value):
        self.technical_rating = int(value)

    def set_likert_aesthetic(self, value):
        self.aesthetic_rating = int(value)

    def reset_likert(self):
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

    def _rated_file_path(self, action_id: str) -> str:
        user_id = App.get_running_app().user.user_id or 'unknown'
        return os.path.join('user_ratings', f'{user_id}_{action_id}.json')

    def _is_rated(self, action_id: str) -> bool:
        return os.path.exists(self._rated_file_path(action_id))

    def load_video(self):
        while self.index < len(self.videos):
            video_file = self.videos[self.index]
            action_id = os.path.splitext(os.path.basename(video_file))[0]

            user_id = App.get_running_app().user.user_id or 'unknown'
            rated_path = os.path.join('user_ratings', f'{user_id}_{action_id}.json')
            if os.path.exists(rated_path):
                print(f"[INFO] Already rated by {user_id}: {action_id} — skipping.")
                self.index += 1
                continue

            self.ids.video_player.source = os.path.join(self.path_videos, video_file)
            self.ids.video_player.state = 'play'

            self.action_id = action_id
            row = self.metadata[self.metadata['id'] == str(self.action_id)]

            if not row.empty:
                self.ids.team_label.text = str(row.team.values[0])
                self.ids.player_label.text = str(row.player.values[0])
                self.ids.type_label.text = str(row.type.values[0])
                self.ids.bodypart_label.text = str(
                    row.iloc[0]["shot_body_part"] if pd.notna(row.iloc[0]["shot_body_part"])
                    else (row.iloc[0]["pass_body_part"] if pd.notna(row.iloc[0]["pass_body_part"]) else '')
                )
            else:
                self.ids.team_label.text = 'No Team'
                self.ids.player_label.text = 'No Player'
                self.ids.type_label.text = 'No Type'
                self.ids.bodypart_label.text = ''

            self.reset_likert()
            self.ids.submit_button.opacity = 1
            self.index += 1
            return

        self.ids.info_label.text = "No more videos to rate."
        self.ids.video_player.opacity = 0
        self.ids.submit_button.opacity = .5


    def submit_rating(self):

        # Sperren des Submit Buttons, wenn keine Kreativität angegeben oder keiner der unteren Buttons angeklickt ist
        if self.current_rating is None and not self.action_not_recognized:
            Popup(
                title="no selection",
                size_hint=(0.6, 0.3)
            ).open()
            return

        os.makedirs('user_ratings', exist_ok=True)

        rating_creativity = self.current_rating
        rating_technical  = self.technical_rating
        rating_aesthetic  = self.aesthetic_rating

        with open('user_ratings/' + str(App.get_running_app().user.user_id) + '_' + str(self.action_id)+'.json', 'w') as f:
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



class RatingApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = User()

    def build(self):
        screen_manager = ScreenManager(transition=FadeTransition())

        screen_manager.add_widget(WelcomeScreen(name = "welcome"))
        screen_manager.add_widget(QuestionnaireScreen(name="questionnaire"))
        screen_manager.add_widget(VideoPlayerScreen(name="videoplayer"))

        return screen_manager


if __name__ == '__main__':
    RatingApp().run()