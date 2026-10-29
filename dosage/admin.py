from django.contrib import admin
from .models import Drug, DrugCategory, DosageCalculation


@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'generic_name', 'category', 'route',
        'adult_dose_min', 'adult_dose_max', 'dose_unit',
        'sex_indication', 'is_active'
    ]
    list_filter = ['category', 'route', 'sex_indication', 'is_active']
    search_fields = ['name', 'generic_name', 'drug_class']
    list_editable = ['is_active']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'generic_name', 'drug_class', 'category', 'route', 'sex_indication', 'is_active')
        }),
        ('Adult Dosage', {
            'fields': ('adult_dose_min', 'adult_dose_max', 'dose_unit', 'max_absolute_dose')
        }),
        ('Pediatric Dosage', {
            'fields': ('pediatric_dose_min', 'pediatric_dose_max', 'pediatric_age_limit')
        }),
        ('Elderly Dosage', {
            'fields': ('elderly_dose_min', 'elderly_dose_max', 'elderly_age_threshold')
        }),
        ('Age Restrictions', {
            'fields': ('min_age', 'max_age')
        }),
        ('Clinical Info', {
            'fields': ('onset_time', 'duration', 'mechanism', 'indications',
                       'contraindications', 'side_effects', 'notes', 'warnings')
        }),
    )


@admin.register(DosageCalculation)
class DosageCalculationAdmin(admin.ModelAdmin):
    list_display = ['patient_age', 'patient_sex', 'patient_weight', 'patient_height', 'calculated_at']
    list_filter = ['patient_sex', 'calculated_at']
    readonly_fields = ['calculated_at']
