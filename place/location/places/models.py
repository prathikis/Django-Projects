from django.db import models

# Create your models here.
class Place(models.Model):
	id = models.AutoField(primary_key=True)
	place_name = models.CharField(max_length=255)
	parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return self.place_name

	class Meta:
		verbose_name_plural = "Places"
