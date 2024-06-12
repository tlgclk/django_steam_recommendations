from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import time

class CB_GameRecommender:
    def __init__(self, game_descriptions_file, user_recommendations_file, user_alias, user_ratings_file):
        # Load game descriptions data
        self.game_descriptions_df = pd.read_csv(game_descriptions_file)
        self.game_descriptions_df.set_index('appid', inplace=True)
        self.game_descriptions_df['description'] = self.game_descriptions_df['description'].fillna('')
        
        # Load user recommendations for the specified user
        self.user_recommendations_df = pd.read_csv(user_recommendations_file)
        self.cf_recommendations = self.user_recommendations_df[self.user_recommendations_df['user_alias'] == user_alias]['appid'].tolist()

        # Load user ratings data
        self.user_ratings_df = pd.read_csv(user_ratings_file)
        
        # Set user_alias as an attribute of the class
        self.user_alias = user_alias

        # Create TF-IDF matrix
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.game_descriptions_df['description'])

        # Calculate cosine similarity matrix
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)

    def recommend_games(self):
        # Content-Based recommendation algorithm
        cb_recommendations = []
        for appid in self.cf_recommendations:
            idx = self.game_descriptions_df.index.get_loc(appid)
            sim_scores = list(enumerate(self.cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:11]  # Select top 10 most similar games
            game_indices = [i[0] for i in sim_scores]
            cb_recommendations.extend(self.game_descriptions_df.iloc[game_indices].index.tolist())

        # Remove duplicates and limit to top 10
        cb_recommendations = list(set(cb_recommendations))[:10]

        # Exclude user's played games from CB recommendations
        user_games = self.user_ratings_df[self.user_ratings_df['user_alias'] == self.user_alias]['appid'].tolist()
        final_recommendations = [appid for appid in cb_recommendations if appid not in user_games]

        return final_recommendations

if __name__ == "__main__":
    # Load user data
    user_id_alias_df = pd.read_csv('recom_final/user_id_alias.csv')

    # Load existing recommendation file or create a new DataFrame
    try:
        cb_recommendations_df = pd.read_csv('steam_recommendations/csv_files/cb_recommendations.csv')
    except FileNotFoundError:
        cb_recommendations_df = pd.DataFrame(columns=['user_id', 'user_alias', 'appid', 'game_name'])

    # Calculate recommendations for all users and add the results
    new_recommendations = []

    total_users = len(user_id_alias_df)

    for index, row in user_id_alias_df.iterrows():
        start_time = time.time()
        user_id = row['user_id']
        user_alias = row['user_alias']
        
        # Initialize the CB_GameRecommender class
        recommender = CB_GameRecommender('team_recommendations/csv_files/all_games.csv', 'team_recommendations/csv_files/cf_recommendations.csv', user_alias, 'team_recommendations/csv_files/user_ratings.csv')
        
        # Get recommendations
        final_recommendations = recommender.recommend_games()
        
        # Add recommendations to the new list
        for appid in final_recommendations:
            game_name = recommender.game_descriptions_df.loc[appid, 'name']
            new_recommendations.append({
                'user_id': user_id,
                'user_alias': user_alias,
                'appid': appid,
                'game_name': game_name
            })
        
        # Print progress and elapsed time
        elapsed_time = time.time() - start_time
        print(f"User {user_alias} recommendations calculated. ({index + 1}/{total_users}), Elapsed time: {elapsed_time:.2f} seconds")

    # Convert new recommendations to a DataFrame
    new_recommendations_df = pd.DataFrame(new_recommendations)

    # Merge with existing recommendations
    cb_recommendations_df = pd.concat([cb_recommendations_df, new_recommendations_df], ignore_index=True)

    # Save the results to a CSV file (without overwriting existing content)
    cb_recommendations_df.to_csv('team_recommendations/csv_files/cb_recommendations.csv', index=False)

    print("Recommendations successfully saved to cb_recommendations.csv.")
