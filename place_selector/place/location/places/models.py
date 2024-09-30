from django.db import models

class Place(models.Model):
	id = models.AutoField(primary_key=True)
	place_name = models.CharField(max_length=255)
	parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
	parent_name = models.CharField(max_length=255, null=True, blank=True)

	def save(self, *args, **kwargs):
		if self.parent:
			self.parent_name = self.parent.place_name
		else:
			self.parent_name = None
		super().save(*args, **kwargs)

	def __str__(self):
		return self.place_name

	class Meta:
		verbose_name_plural = "Places"
