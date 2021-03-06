from django.contrib import admin
from .models import Vendor, NegotiatedPrice, InventoryRecord

admin.site.register(Vendor)

admin.site.register(NegotiatedPrice)


class InventoryRecordAdmin(admin.ModelAdmin):
    def queryset(self, request):
        return InventoryRecord.objects.all().prefetch_related('school', 'material')

    readonly_fields = ('school', 'material')
    list_display = ('school', 'material', 'qty_onsite',
        'qty_to_student_home', 'qty_to_student_class',
        'qty_lost_stolen', 'qty_unusable', 'qty_reallocated')

admin.site.register(InventoryRecord, InventoryRecordAdmin)
