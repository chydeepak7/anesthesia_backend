from rest_framework import serializers
from .models import Drug, DrugCategory, DosageCalculation


class DrugCategorySerializer(serializers.ModelSerializer):
    drug_count = serializers.SerializerMethodField()

    class Meta:
        model = DrugCategory
        fields = ['id', 'name', 'description', 'icon', 'drug_count']

    def get_drug_count(self, obj):
        return obj.drugs.filter(is_active=True).count()


class DrugSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)

    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'drug_class',
            'category', 'category_name', 'category_icon',
            'route', 'route_display', 'sex_indication',
            'adult_dose_min', 'adult_dose_max',
            'pediatric_dose_min', 'pediatric_dose_max',
            'elderly_dose_min', 'elderly_dose_max',
            'dose_unit', 'max_absolute_dose',
            'min_age', 'max_age', 'pediatric_age_limit', 'elderly_age_threshold',
            'onset_time', 'duration', 'mechanism',
            'indications', 'contraindications', 'side_effects',
            'notes', 'warnings',
        ]


class DosageQuerySerializer(serializers.Serializer):
    age = serializers.IntegerField(min_value=0, max_value=120)
    sex = serializers.ChoiceField(choices=['male', 'female'])
    weight = serializers.FloatField(min_value=1, max_value=300, default=70)
    height = serializers.FloatField(min_value=30, max_value=250, default=170)


class CalculatedDrugSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    calculated_dose = serializers.SerializerMethodField()

    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'drug_class',
            'category', 'category_name', 'category_icon',
            'route', 'route_display',
            'dose_unit', 'onset_time', 'duration',
            'mechanism', 'indications', 'contraindications',
            'side_effects', 'notes', 'warnings',
            'calculated_dose',
        ]

    def get_calculated_dose(self, obj):
        age = self.context.get('age', 30)
        weight = self.context.get('weight', 70)
        ibw = self.context.get('ibw')
        lbw = self.context.get('lbw')
        bmi = self.context.get('bmi')
        return obj.get_dose_for_patient(age, weight, ibw=ibw, lbw=lbw, bmi=bmi)
