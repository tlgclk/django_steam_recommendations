import json
import requests
import time
import pandas as pd
import numpy as np
import os
import warnings

#warnings.filterwarnings("ignore")


class UserRatingsUpdater:
    def __init__(self, api_key, game_play_median_file, user_ratings_file, user_id_alias_file, max_requests=8, wait_time=10):
        self.api_key = api_key
        self.game_play_median_file = game_play_median_file
        self.user_ratings_file = user_ratings_file
        self.user_id_alias_file = user_id_alias_file
        self.max_requests = max_requests
        self.wait_time = wait_time
        self.base_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&format=json'
        
        self.columns = [
            'appid', 
            'playtime_forever', 
            'playtime_2weeks', 
            'name', 
            'median_playtime', 
            'Assuming_Ratings', 
            'user_id',
            'user_alias'
        ]
        
        self.game_play_median = pd.read_csv(self.game_play_median_file)
        self.load_user_ratings()
        self.load_user_ids()

    def load_user_ids(self):
        try:
            self.user_ids_df = pd.read_csv(self.user_id_alias_file)
            if 'user_alias' not in self.user_ids_df.columns:
                self.user_ids_df['user_alias'] = [f'user{i}' for i in range(len(self.user_ids_df))]
            self.user_ids = list(zip(self.user_ids_df['user_id'], self.user_ids_df['user_alias']))
        except FileNotFoundError:
            self.user_ids_df = pd.DataFrame(columns=['user_id', 'user_alias'])
            self.user_ids = []

    def load_user_ratings(self):
        if not os.path.exists(self.user_ratings_file):
            self.user_ratings = pd.DataFrame(columns=self.columns)
            self.user_ratings.to_csv(self.user_ratings_file, index=False)
            self.max_alias_index = 0
        else:
            self.user_ratings = pd.read_csv(self.user_ratings_file)
            if 'user_alias' not in self.user_ratings.columns:
                self.user_ratings['user_alias'] = None
            self.max_alias_index = self.user_ratings['user_alias'].apply(lambda x: int(x[4:]) if pd.notna(x) else -1).max() + 1

    def save_user_ratings(self):
        self.user_ratings.to_csv(self.user_ratings_file, index=False)

    def user_id_exists(self, user_id):
        if user_id in self.user_ratings['user_id'].values:
            print(f"User ID {user_id} exists in user_ratings.")
            return True
        else:
            return False
        
    def save_user_ids(self, new_user_id, new_user_alias):
        if not self.user_ratings['user_id'].isin([new_user_id]).any():
            new_user_ids_df = pd.DataFrame([[new_user_id, new_user_alias]], columns=['user_id', 'user_alias'])
            new_user_ids_df.to_csv(self.user_id_alias_file, mode='a', header=False, index=False)
        else:
            print(f"User ID {new_user_id} already exists in user_ids.")
        

    def add_new_user_id(self, new_user_id):
        if new_user_id in self.user_ids_df['user_id'].values:
            print(f"User ID {new_user_id} already exists.")
            return
        if new_user_id in self.user_ratings['user_id'].values:
            print(f"User ID {new_user_id} already exists in user_ratings.")
            return
        else:
            new_user_alias = f'user{self.max_alias_index}'
            self.user_ids_df = pd.concat([self.user_ids_df, pd.DataFrame([[new_user_id, new_user_alias]], columns=['user_id', 'user_alias'])], ignore_index=True)
            self.max_alias_index += 1
            self.save_user_ids(new_user_id, new_user_alias)
            self.update_user_ratings_for_user(new_user_id, new_user_alias)

      
    def update_user_ratings_for_user(self, user_id, user_alias):
        if not self.user_ids_df[self.user_ids_df['user_id'] == user_id].empty:
            url = self.base_url.format(self.api_key, user_id)
            df_col = self.get_df(url)
            if not df_col.empty:
                df_col = self.get_ratings(df_col)
                df_col['user_id'] = user_id
                df_col['user_alias'] = user_alias
                self.user_ratings = pd.concat([self.user_ratings, df_col], ignore_index=True)
                self.save_user_ratings()
        else:
            print(f"User ID {user_id} does not exist in user_ids.")

    def get_df(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'response' in data and 'games' in data['response']:
                df = pd.DataFrame(data['response']['games'])
                no_zero = df.loc[df['playtime_forever'] != 0]
                df_col = pd.merge(no_zero, self.game_play_median, on="appid")
                return df_col
            else:
                print(f"No games found for URL: {url}")
                return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return pd.DataFrame()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return pd.DataFrame()

    def get_ratings(self, df_col):
        df_col['Assuming_Ratings'] = 0
        for i in range(len(df_col)):
            if df_col['playtime_forever'][i] >= df_col['median_playtime'][i]:
                df_col['Assuming_Ratings'][i] = 5
            elif df_col['median_playtime'][i] > df_col['playtime_forever'][i] >= df_col['median_playtime'][i] * 0.8:
                df_col['Assuming_Ratings'][i] = 4
            elif df_col['median_playtime'][i] * 0.8 > df_col['playtime_forever'][i] >= df_col['median_playtime'][i] * 0.5:
                df_col['Assuming_Ratings'][i] = 3
            elif df_col['median_playtime'][i] * 0.5 > df_col['playtime_forever'][i] >= df_col['median_playtime'][i] * 0.1:
                df_col['Assuming_Ratings'][i] = 2
            elif df_col['median_playtime'][i] * 0.1 > df_col['playtime_forever'][i]:
                df_col['Assuming_Ratings'][i] = 1
        return df_col

    def update_user_ratings(self):
        df_user_links = pd.DataFrame(columns=['Links'])
        df_user_links['Links'] = [self.base_url.format(self.api_key, user_id) for user_id, _ in self.user_ids]
        df_col_text_ = pd.DataFrame(columns=self.columns)

        request_count = 0

        for i, (user_id, user_alias) in enumerate(self.user_ids):
            if not self.user_id_exists(user_id):
                df_col = self.get_df(df_user_links['Links'][i])
                if not df_col.empty:
                    df_col = self.get_ratings(df_col)
                    df_col['user_id'] = user_id
                    df_col['user_alias'] = user_alias
                    df_col_text_ = pd.concat([df_col_text_, df_col], ignore_index=True)
                request_count += 1
                if request_count % self.max_requests == 0:
                    print(f"{self.max_requests} isteğe ulaşıldı, {self.wait_time} saniye bekleniyor...")
                    time.sleep(self.wait_time)

        if not df_col_text_.empty:
            self.user_ratings = pd.concat([self.user_ratings, df_col_text_], ignore_index=True)
            self.save_user_ratings()


if __name__ == "__main__":
    api_key = '12342C69B72B036F8E660D95F28DF431'
    game_play_median_file = 'steam_recommendations/csv_files/all_games.csv'
    user_ratings_file = 'steam_recommendations/csv_files/user_ratings.csv'
    user_id_alias_file = 'steam_recommendations/csv_files/user_id_alias.csv'

    updater = UserRatingsUpdater(api_key, game_play_median_file, user_ratings_file, user_id_alias_file)
    updater.update_user_ratings()
