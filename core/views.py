from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from core.models import Place


def _serialize_place(place, request):
    images = place.images.filter(image__isnull=False).order_by("order", "id")
    image_urls = [request.build_absolute_uri(img.image.url) for img in images]

    return {
        "title": place.name,
        "imgs": image_urls,
        "main_image": image_urls[0] if image_urls else None,
        "short_description": place.shortDesc,
        "long_description": place.longDesc,
        "coordinates": {"lon": place.lon, "lat": place.lat},
    }


def parse_place_details(request, placeId):
    place = get_object_or_404(Place.objects.prefetch_related("images"), pk=placeId)
    return JsonResponse(
        _serialize_place(place, request),
        json_dumps_params={"ensure_ascii": False},
    )


def main_view(request):
    places = Place.objects.all()
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(place.lon), float(place.lat)],
            },
            "properties": {
                "title": place.name,
                "placeId": place.id,
                "detailsUrl": reverse("parse_place_details", args=[place.id]),
            },
        }
        for place in places
    ]
    payload = {"type": "FeatureCollection", "features": features}
    return render(request, "index.html", {"feature": payload})