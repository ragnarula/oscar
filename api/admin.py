from django.contrib import admin
from .models import Device
from django.utils.translation import ugettext_lazy


class DeviceAdmin(admin.ModelAdmin):

    readonly_fields = ('current_state',)
    list_display = ('name', 'host', 'port', 'timeout', 'current_state', 'active')
    save_as = True


class MyAdminSite(admin.AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Oscar Management Interface')

    # Text to put in each page's <h1>.
    site_header = ugettext_lazy('Oscar')

    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Welcome to Oscar')

admin_site = MyAdminSite()
admin_site.register(Device, DeviceAdmin)