from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from strawberry.django.views import GraphQLView

from .schema import schema

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", GraphQLView.as_view(schema=schema, graphiql=True), name="graphql"),
    path("accounts/", include("allauth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa

urlpatterns = DebugToolbarSetup.do_urls(urlpatterns)
