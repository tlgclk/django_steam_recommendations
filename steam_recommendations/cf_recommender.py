import pandas as pd
from surprise import Dataset, Reader, KNNBasic
from surprise.model_selection import train_test_split
from surprise import accuracy
from collections import defaultdict
import numpy as np
import time

class CF_GameRecommender:
    def __init__(self, user_ratings_file, game_names_file):
        # Load game names and user ratings data
        self.game_names_df = pd.read_csv(game_names_file)
        self.df = pd.read_csv(user_ratings_file)
        
        # Map appid to game names and user_id to user_alias
        self.appid_to_name = self.game_names_df.set_index('appid')['name'].to_dict()
        self.user_id_alias_map = self.df[['user_id', 'user_alias']].drop_duplicates().set_index('user_id')['user_alias'].to_dict()
        
        # Prepare the data for Surprise library
        reader = Reader(rating_scale=(1, 5))
        dataset = Dataset.load_from_df(self.df[['user_id', 'appid', 'Assuming_Ratings']], reader)
        
        # Split the data into training and testing sets
        self.trainset, self.testset = train_test_split(dataset, test_size=0.25, random_state=42)
        
        # Initialize and train the KNNBasic model
        sim_options = {'name': 'msd', 'user_based': True}
        self.model = KNNBasic(sim_options=sim_options)
        self.model.fit(self.trainset)
        
        # Compute and print accuracy metrics
        predictions = self.model.test(self.testset)
        self.rmse = accuracy.rmse(predictions)
        self.mae = accuracy.mae(predictions)
        print("RMSE:", self.rmse)
        print("MAE:", self.mae)
        
        # Create a dictionary of played games for each user
        self.played_games = self.df.groupby('user_id')['appid'].apply(set).to_dict()

    def get_top_n_recommendations(self, user_id, n=10):
        inner_user_id = self.model.trainset.to_inner_uid(user_id)
        neighbors = self.model.get_neighbors(inner_user_id, k=10)
        neighbors_ratings = defaultdict(list)
        similarity_matrix = self.model.sim
        similarity_scores = similarity_matrix[inner_user_id]
        
        for neighbor in neighbors:
            inner_id = self.model.trainset.to_raw_uid(neighbor)
            neighbor_played_games = self.played_games[inner_id]
            
            for game in neighbor_played_games:
                if game not in self.played_games[user_id]:
                    neighbors_ratings[game].append(self.model.predict(user_id, game).est)
        
        recommendations = [(appid, np.mean(ratings)) for appid, ratings in neighbors_ratings.items()]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n], neighbors, similarity_scores[neighbors]
    

    def recommend(self, user_id, n=10):
        user_alias = self.user_id_alias_map.get(user_id, "Unknown User")
        recommended_items, similar_users, similarity_scores = self.get_top_n_recommendations(user_id, n)
        
        print(f"Recommended items for {user_alias} ({user_id}):")
        for appid, rating in recommended_items:
            game_name = self.appid_to_name.get(appid, "Unknown Game")
            print(f"AppID: {appid}, Game: {game_name}, Predicted Rating: {rating:.2f}")
        
        print(f"\nMost similar users to {user_alias} ({user_id}):")
        for neighbor, similarity_score in zip(similar_users, similarity_scores):
            similar_user_id = self.model.trainset.to_raw_uid(neighbor)
            similar_user_alias = self.user_id_alias_map.get(similar_user_id, "Unknown User")
            print(f"User ID: {similar_user_id}, User Alias: {similar_user_alias}, Similarity: {similarity_score:.4f}")
        
        print("\n<------------------------------->\n")

def calculate_recommendations(user_ratings_file, game_names_file, user_id_alias_file):
    # Load user aliases
    user_id_alias_df = pd.read_csv(user_id_alias_file)
    
    recommendations_data = []
    similarities_data = []
    
    for user_id in user_id_alias_df['user_id']:
        recommender = CF_GameRecommender(user_ratings_file, game_names_file)
        recommended_items, similar_users, similarity_scores = recommender.get_top_n_recommendations(user_id)
        
        user_alias = recommender.user_id_alias_map.get(user_id, "Unknown User")
        
        # Save recommendations
        for appid, rating in recommended_items:
            game_name = recommender.appid_to_name.get(appid, "Unknown Game")
            recommendations_data.append({'user_id': user_id, 'user_alias': user_alias, 'appid': appid, 'game_name': game_name, 'predicted_rating': rating})
        
        # Save similarities
        for neighbor, similarity_score in zip(similar_users, similarity_scores):
            similar_user_id = recommender.model.trainset.to_raw_uid(neighbor)
            similar_user_alias = recommender.user_id_alias_map.get(similar_user_id, "Unknown User")
            similarities_data.append({'user_id': user_id, 'user_alias': user_alias, 'sim_user_id': similar_user_id, 'sim_user_alias': similar_user_alias, 'similarity_score': similarity_score})
    
    # Convert to dataframes
    recommendations_df = pd.DataFrame(recommendations_data)
    similarities_df = pd.DataFrame(similarities_data)
    
    # Save to CSV files
    recommendations_df.to_csv('steam_recommendations/csv_files/cf_recommendations.csv', index=False)
    similarities_df.to_csv('steam_recommendations/csv_files/cf_similarities.csv', index=False)

# This block can be removed if you don't want to run any test within the module itself
if __name__ == "__main__":
    start_time = time.time()
    calculate_recommendations('steam_recommendations/csv_files/user_ratings.csv', 'steam_recommendations/csv_files/all_games.csv', 'steam_recommendations/csv_files/user_id_alias.csv')
    elapsed_time = time.time() - start_time
    print(f"Öneriler ve benzerlikler hesaplandı. Geçen süre: {elapsed_time:.2f} saniye")