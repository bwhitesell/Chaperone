from django.db import models


class CrimeIncident(models.Model):

    row_id = models.CharField(unique=True, max_length=100, null=False, blank=False)
    crm_cd = models.IntegerField()
    crm_cd_desc = models.TextField()
    date_occ_str = models.CharField(max_length=70)
    time_occ = models.IntegerField()
    premis_desc = models.TextField()
    longitude = models.FloatField()
    latitude = models.FloatField()


class DailyCrimeVolumeManager(models.Manager):
    def get_chart_data(self):
        qs = self.all().order_by('date_occ_str').values_list('date_occ_str', 'volume')
        return [ins[0].replace(' 00:00:00', '') for ins in qs], [ins[1] for ins in qs]


class DailyCrimeVolume(models.Model):
    date_occ_str = models.CharField(max_length=70)
    volume = models.IntegerField()

    objects = DailyCrimeVolumeManager()
