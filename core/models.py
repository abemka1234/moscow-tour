from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class Place(models.Model):
    name = models.CharField("Название места", max_length=40)
    shortDesc = models.TextField("Краткое описание")
    longDesc = CKEditor5Field("Длинное описание", config_name="default")
    lon = models.DecimalField("Долгота", max_digits=50, decimal_places=20)
    lat = models.DecimalField("Широта", max_digits=50, decimal_places=20)

    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Места"

    def __str__(self):
        return self.name


class PlaceImage(models.Model):
    image = models.ImageField("Изображение", upload_to="places/")
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Привязанное место",
    )
    order = models.PositiveIntegerField("Порядок в списке", default=0, db_index=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Изображение места"
        verbose_name_plural = "Изображения места"

    def __str__(self):
        return self.place.name
        