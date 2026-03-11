"""URL configuration and API views for the email automation project."""

import csv
import io
import os
import threading

from django.http import FileResponse, JsonResponse
from django.urls import path
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from campaign_runner import run_campaign
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    parser_classes = (MultiPartParser,)

    @action(detail=False, methods=["post"])
    def upload(self, request):
        """Upload a CSV file of leads."""
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=400)

        try:
            content = file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            created = 0
            for row in reader:
                try:
                    Lead.objects.create(**row)
                    created += 1
                except Exception:
                    # Skip duplicates or invalid rows.
                    continue
            return Response({"created": created})
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=["post"])
    def start_campaign(self, request):
        """Start a campaign in a background thread."""

        def task():
            run_campaign()

        threading.Thread(target=task, daemon=True).start()
        return Response({"status": "campaign started"})


def frontend_view(request):
    """Serve the simple frontend page."""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(open(frontend_path, "rb"), content_type="text/html")
    return JsonResponse({"error": "Frontend not found"}, status=404)


urlpatterns = [
    path("api/leads/", LeadViewSet.as_view({"get": "list", "post": "create"})),
    path("api/leads/upload/", LeadViewSet.as_view({"post": "upload"})),
    path("api/campaign/start/", LeadViewSet.as_view({"post": "start_campaign"})),
    path("", frontend_view),
]
