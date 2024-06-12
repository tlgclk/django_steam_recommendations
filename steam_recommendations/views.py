from django.shortcuts import render, redirect
from django.http import HttpResponse
from steam_recommendations.models import Game, UserRating
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from .cf_recommender import CF_GameRecommender
import csv
import os
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import pandas as pd

user_ratings_file = 'C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/user_ratings.csv'
game_names_file = 'C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv'
recommender = CF_GameRecommender(user_ratings_file, game_names_file)


def home(request):
    return HttpResponse("Merhaba, Django!")

def game_list(request):
    games = load_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv')
    filtered_games = [game for game in games if int(game['median_playtime']) > 100]
    context = {'games': filtered_games}
    return render(request, 'game_list.html', context)

def load_csv(file_path):
    data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

def test(request):
    return render(request, 'test.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('my_games')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'login.html')
    
def logout_view(request):
    logout(request)
    return redirect('login')

def my_games_view(request):
    user_id = request.user.username  # Giriş yapmış kullanıcı adı
    #user_id = '76561198066328851'

    
    user_ratings = load_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/user_ratings.csv')
    appids = [row['appid'] for row in user_ratings if row['user_id'] == user_id]
    games = load_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv')

    games_with_ratings = []
    for rating in user_ratings:
        if rating['user_id'] == user_id:
            for game in games:
                if str(rating['appid']) == str(game['appid']):
                    games_with_ratings.append({
                        'name': game['name'],
                        'playtime_forever': rating['playtime_forever'],
                        'header_image': game['header_image']
                    })

    paginator = Paginator(games_with_ratings, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        games_html = ""
        for game in page_obj:
            games_html += f'''
            <div class="game-card">
                <img src="{game['header_image']}" alt="{game['name']}" class="game-image">
                <div class="game-title">{game['name']}</div>
                <div class="game-playtime">Playtime: {game['playtime_forever']} minutes</div>
            </div>
            '''
        return JsonResponse({
            'games_html': games_html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
    
    return render(request, 'my_games.html', {'page_obj': page_obj})

def recommendations_view(request):
    games = load_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv')[:10]
    return render(request, 'recommendations.html', {'games': games})


def cf_recommendations_view(request):
    # Load user_id_alias.csv to get the mapping of user_id to user_alias
    user_id_alias_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/user_id_alias.csv')

    # Example user_id, replace this with the actual user ID you're filtering for
    user_id = int(request.user.username)
    active_user_id = user_id
    #active_user_id = 76561198066328851

    # Get user_alias for the active_user_id
    user_alias_row = user_id_alias_df[user_id_alias_df['user_id'] == active_user_id]
    if user_alias_row.empty:
        return render(request, 'cf_recommendations.html', {'game_recommendations': []})

    user_alias = user_alias_row.iloc[0]['user_alias']

    # Load cf_recommendations.csv
    recommendations_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/cf_recommendations.csv')

    # Filter recommendations for the user_alias
    user_recommendations = recommendations_df[recommendations_df['user_alias'] == user_alias]['appid'].tolist()

    # Load all_games.csv
    all_games_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv')

    # Find game details for recommendations
    game_recommendations = []
    for appid in user_recommendations:
        game_details = all_games_df[all_games_df['appid'] == appid]
        if not game_details.empty:
            game_details = game_details.iloc[0]  # Assuming there's only one matching game
            game_recommendations.append({
                'appid': appid,
                'game_name': game_details['name'],
                'genres': game_details['steamspy_tags'],  # Assuming 'steamspy_tags' represents genres
                'release_date': game_details['release_date'],
                'header_image': game_details['header_image']  # Assuming 'header_image' represents image URLs
            })

    context = {'game_recommendations': game_recommendations}
    return render(request, 'cf_recommendations.html', context)

def cf_similarities_view(request):
    user_id = int(request.user.username)
    #user_id = 76561198066328851  # Filtreleme yapılacak olan kullanıcı ID'si
    similarities_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/cf_similarities.csv')
    
    # Filter similarities for the current user_id
    user_similarities_df = similarities_df[similarities_df['user_id'] == user_id]
    
    # Prepare data for template
    similarities = []
    for index, row in user_similarities_df.iterrows():
        similarities.append({
            'user_id': row['user_id'],
            'user_alias': row['user_alias'],
            'sim_user_id': row['sim_user_id'],
            'sim_user_alias': row['sim_user_alias'],
            'similarity_score': row['similarity_score']
        })
    
    context = {'similarities': similarities}
    return render(request, 'cf_similarities.html', context)

def cb_recommendations_view(request):
    # Kullanıcı adını string olarak al
    user_id_str = request.user.username
    
    try:
        # String'i integer'a çevir
        user_id = int(user_id_str)
    except ValueError:
        # Eğer dönüşüm başarısız olursa, hata işleme al
        return render(request, 'cb_recommendations.html', {'game_recommendations': []})

    # Load user_id_alias.csv to get the mapping of user_id to user_alias
    user_id_alias_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/user_id_alias.csv')

    # Get user_alias for the active_user_id
    user_alias_row = user_id_alias_df[user_id_alias_df['user_id'] == user_id]
    if user_alias_row.empty:
        return render(request, 'cb_recommendations.html', {'game_recommendations': []})

    user_alias = user_alias_row.iloc[0]['user_alias']

    # Load cb_recommendations.csv
    recommendations_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/cb_recommendations.csv')

    # Filter recommendations for the user_alias
    user_recommendations = recommendations_df[recommendations_df['user_alias'] == user_alias]['appid'].tolist()

    # Load all_games.csv
    all_games_df = pd.read_csv('C:/Users/tolga/Desktop/Proje/django_steam_csv/steam_recommendations/csv_files/all_games.csv')

    # Find game details for recommendations
    game_recommendations = []
    for appid in user_recommendations:
        game_details = all_games_df[all_games_df['appid'] == appid]
        if not game_details.empty:
            game_details = game_details.iloc[0]  # Assuming there's only one matching game
            game_recommendations.append({
                'appid': appid,
                'game_name': game_details['name'],
                'genres': game_details['steamspy_tags'],  # Assuming 'steamspy_tags' represents genres
                'release_date': game_details['release_date'],
                'header_image': game_details['header_image']  # Assuming 'header_image' represents image URLs
            })

    context = {'game_recommendations': game_recommendations}
    return render(request, 'cb_recommendations.html', context)