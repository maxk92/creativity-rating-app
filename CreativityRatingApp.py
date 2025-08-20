import kivy
import pandas as pd
import numpy as np
import os
import json
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, CardTransition, SwapTransition, WipeTransition, FallOutTransition
from kivy.lang import Builder
kivy.require("1.9.1")
import json
import random

class User:
    def __init__(self):
        self.user_id = ''
        self.gender = 'Not specified'
        self.age = 0
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0

        # Load metadata from CSV
        self.path_metadata = '/home/max/drive/coding/projects/13___creativity/lsa-creativity/data/df_actions/'
        self.ls_matches  = [match.split('.')[0] for match in os.listdir(self.path_metadata)]
        self.metadata = pd.concat([pd.read_csv(self.path_metadata + actions_df+'.csv') for actions_df in self.ls_matches])
        self.path_videos = '/media/max/Elements/Sebastian_Spiele/Bundesliga/'

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
        
    def load_video(self):
        if self.index < len(self.videos):
            video_file = self.videos[self.index]
            action_id = video_file.split('/')[-1].replace('.mp4', '')
            #self.ids.video_player.source = os.path.join(self.path_videos + '3895134/', video_file)
            self.ids.video_player.source = video_file
            self.ids.video_player.state = 'play'

            self.action_id = action_id
            row = self.metadata[self.metadata['id'] == str(self.action_id)]
            
            #self.update_metadata(video_file)
            
            # update metadata to be displayed above video
            self.ids.team_label.text     = str(row.team.values[0])
            self.ids.player_label.text   = str(row.player.values[0])
            self.ids.type_label.text     = str(row.type.values[0])
            self.ids.bodypart_label.text = str(row.iloc[0]["shot_body_part"] if pd.notna(row.iloc[0]["shot_body_part"]) else (row.iloc[0]["pass_body_part"] if pd.notna(row.iloc[0]["pass_body_part"]) else None))
            # set rating slider to 0
            self.ids.rating_slider.value = 0
            # make sure submit button has full opacity
            self.ids.submit_button.opacity = 1
            
            # increase index by 1 for next video to be loaded
            self.index += 1
        else:
            self.ids.info_label.text = "No more videos to rate."
            self.ids.video_player.opacity = 0
            self.ids.submit_button.opacity = .5
            
    
    def submit_rating(self):
        rating = self.ids.rating_slider.value
        #action_id = self.videos[self.index].split('.')[0]

        with open('user_ratings/' + str(App.get_running_app().user.user_id) + '_' + str(self.action_id)+'.json', 'w') as f:
            json.dump({'user_id' : App.get_running_app().user.user_id, 'id': self.action_id, 'action_rating' : rating}, f)

        print(f"Video rated: {rating}/10")  
        print(self.index)
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
