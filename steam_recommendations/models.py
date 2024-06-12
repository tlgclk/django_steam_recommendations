from django.db import models

# Create your models here.
class Game(models.Model):
    appid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    release_date = models.DateField()
    developer = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    steamspy_tags = models.CharField(max_length=255)
    positive_ratings = models.IntegerField()
    negative_ratings = models.IntegerField()
    median_playtime = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField()
    header_image = models.URLField()

    def __str__(self):
        return self.name
    
class UserRating(models.Model):
    appid = models.IntegerField()
    playtime_forever = models.IntegerField()
    playtime_2weeks = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    median_playtime = models.IntegerField()
    Assuming_Ratings = models.IntegerField()
    user_id = models.CharField(max_length=255)
    user_alias = models.CharField(max_length=255)
    
    from django.db import models

class UserAliasMapping(models.Model):
    user_id = models.CharField(max_length=255, unique=True)
    user_alias = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.user_alias
    
class CF_GameRecommendation(models.Model):
    user_id = models.CharField(max_length=255)
    user_alias = models.CharField(max_length=255)
    appid = models.IntegerField()
    game_name = models.CharField(max_length=255)
    predicted_rating = models.FloatField()

    def __str__(self):
        return f"{self.user_alias} - {self.game_name}"

from django.db import models

class UserSimilarity(models.Model):
    user_id = models.CharField(max_length=255)
    user_alias = models.CharField(max_length=255)
    sim_user_id = models.CharField(max_length=255)
    sim_user_alias = models.CharField(max_length=255)
    similarity_score = models.FloatField()

    def __str__(self):
        return f"{self.user_alias} - {self.sim_user_alias} - {self.similarity_score}"
    
from django.db import models

class CB_GameRecommendation(models.Model):
    user_id = models.CharField(max_length=255)
    user_alias = models.CharField(max_length=255)
    appid = models.CharField(max_length=255)
    game_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user_alias} - {self.game_name}"