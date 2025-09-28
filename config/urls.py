from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView

from .schema import schema

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("graphql/", AsyncGraphQLView.as_view(schema=schema), name="graphql"),
    path("graphql/", csrf_exempt(AsyncGraphQLView.as_view(schema=schema)), name="graphql"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa

urlpatterns = DebugToolbarSetup.do_urls(urlpatterns)
