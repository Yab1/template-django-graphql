from django.contrib import admin

from .models import Child, GrandChild, GrandParent

admin.site.register(GrandParent)
admin.site.register(GrandChild)
admin.site.register(Child)
