import kivy
import pandas as pd
import numpy as np
import os
import json
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, CardTransition, SwapTransition, WipeTransition, FallOutTransition
from kivy.lang import Builder
from kivy.properties import NumericProperty  # <-- minimal neu (für Likert-Werte)
kivy.require("1.9.1")
import json
import random
from pathlib import Path

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

    # --- minimal hinzugefügt: Aliase, damit die KV-Handler funktionieren ---
    def set_user_player_exp(self, years):
        return self.set_player_exp(years)

    def set_user_coach_exp(self, years):
        return self.set_coach_exp(years)

    def set_user_watch_exp(self, years):
        return self.set_watch_exp(years)
    # -----------------------------------------------------------------------

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
        print(App.get_running_app().user.user_id)
        with open('user_data/' + str(App.get_running_app().user.user_id) + '.json', 'w') as f:
            json.dump({'user_id' : App.get_running_app().user.user_id, 'gender': App.get_running_app().user.gender, 'age': App.get_running_app().user.age, 'license': App.get_running_app().user.license}, f)



class VideoPlayerScreen(Screen):
    # <-- minimal neu: drei Properties für die Likert-Werte
    current_rating = NumericProperty(0)           # Creativity
    technical_rating = NumericProperty(0)         # Technical correctness
    aesthetic_rating = NumericProperty(0)         # Aesthetic appeal

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0

        # Load metadata from CSV
        self.path_metadata = '/Users/Esther/Desktop/creativity-rating-app-main/meta_data'
        meta = Path(self.path_metadata)
        csv_paths = sorted(meta.glob("[!.]*.csv"))
        self.ls_matches = [p.stem for p in csv_paths]
        self.metadata = pd.concat([pd.read_csv(p) for p in csv_paths], ignore_index=True)
        self.path_videos = '/Users/Esther/Desktop/creativity-rating-app-main/Videos'

        self.videos = [
            os.path.join(self.path_videos, folder, file)
            for folder in self.ls_matches
            for file in os.listdir(os.path.join(self.path_videos, folder))
            if file.endswith('.mp4')
        ]

        random.seed(42)
        random.shuffle(self.videos)

    # optional: choose a subset of videos
    # videos = videos[:10]

    def on_enter(self, *args):
        self.load_video()

    def previous_video(self, instance):
        pass

    # --- minimal neu: Set-Methoden für alle drei Skalen ---
    def set_likert(self, value):
        self.current_rating = int(value)

    def set_likert_tech(self, value):
        self.technical_rating = int(value)

    def set_likert_aesthetic(self, value):
        self.aesthetic_rating = int(value)

    def reset_likert(self):
        # Buttons der drei Gruppen (falls vorhanden) auf neutral setzen
        for btn_id in ('r_m3', 'r_m2', 'r_m1', 'r_0', 'r_p1', 'r_p2', 'r_p3',
                       't_m3', 't_m2', 't_m1', 't_0', 't_p1', 't_p2', 't_p3',
                       'a_m3', 'a_m2', 'a_m1', 'a_0', 'a_p1', 'a_p2', 'a_p3'):
            if btn_id in self.ids:
                self.ids[btn_id].state = 'normal'
        if 'r_0' in self.ids:
            self.ids.r_0.state = 'down'
        if 't_0' in self.ids:
            self.ids.t_0.state = 'down'
        if 'a_0' in self.ids:
            self.ids.a_0.state = 'down'
        self.current_rating = 0
        self.technical_rating = 0
        self.aesthetic_rating = 0
    # ------------------------------------------------------

    def load_video(self):
        if self.index < len(self.videos):
            video_file = self.videos[self.index]
            action_id = video_file.split('/')[-1].replace('.mp4', '')
            #self.ids.video_player.source = os.path.join(self.path_videos + '3895134/', video_file)
            self.ids.video_player.source = video_file
            self.ids.video_player.state = 'play'

            self.action_id = action_id
            row = self.metadata[self.metadata['id'] == str(self.action_id)]

            # update metadata to be displayed above video
            self.ids.team_label.text     = str(row.team.values[0])
            self.ids.player_label.text   = str(row.player.values[0])
            self.ids.type_label.text     = str(row.type.values[0])
            self.ids.bodypart_label.text = str(row.iloc[0]["shot_body_part"] if pd.notna(row.iloc[0]["shot_body_part"]) else (row.iloc[0]["pass_body_part"] if pd.notna(row.iloc[0]["pass_body_part"]) else None))

            # Likert auf 0 setzen (alle drei)
            self.reset_likert()

            # submit sichtbar
            self.ids.submit_button.opacity = 1

            # nächstes Video
            self.index += 1
        else:
            self.ids.info_label.text = "No more videos to rate."
            self.ids.video_player.opacity = 0
            self.ids.submit_button.opacity = .5


    def submit_rating(self):
        # alle drei Werte mitschreiben
        rating_creativity = self.current_rating
        rating_technical  = self.technical_rating
        rating_aesthetic  = self.aesthetic_rating

        with open('user_ratings/' + str(App.get_running_app().user.user_id) + '_' + str(self.action_id)+'.json', 'w') as f:
            json.dump({
                'user_id' : App.get_running_app().user.user_id,
                'id': self.action_id,
                'action_rating' : rating_creativity,         # bestehendes Feld
                'technical_correctness': rating_technical,    # neu
                'aesthetic_appeal': rating_aesthetic          # neu
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