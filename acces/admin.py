from django.contrib import admin
from .models import Acces, Badge, Porte

admin.site.register([Badge, Porte])


@admin.register(Acces)
class AccesAdmin(admin.ModelAdmin):
    list_display = ['date', 'porte', 'uid_lu', 'autorise', 'raison']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
