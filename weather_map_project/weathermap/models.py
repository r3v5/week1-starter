from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.country}"