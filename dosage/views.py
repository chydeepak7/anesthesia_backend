import math
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Drug, DrugCategory, DosageCalculation
from .serializers import (
    DrugCategorySerializer, DrugSerializer,
    DosageQuerySerializer, CalculatedDrugSerializer
)


def calculate_ibw(sex, height_cm):
    """
    Devine formula for Ideal Body Weight.
    Male:   IBW = 50 + 2.3 * (height_in - 60)
    Female: IBW = 45.5 + 2.3 * (height_in - 60)
    Returns None if height <= 152.4 cm (5 ft).
    """
    height_in = height_cm / 2.54
    if height_in <= 60:
        return None
    if sex == 'male':
        return round(50 + 2.3 * (height_in - 60), 2)
    else:
        return round(45.5 + 2.3 * (height_in - 60), 2)


def calculate_lbw(sex, weight_kg, height_cm):
    """
    Janmahasatian formula for Lean Body Weight.
    Male:   LBW = (9270 * weight) / (6680 + 216 * BMI)
    Female: LBW = (9270 * weight) / (8780 + 244 * BMI)
    """
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if sex == 'male':
        return round((9270 * weight_kg) / (6680 + 216 * bmi), 2)
    else:
        return round((9270 * weight_kg) / (8780 + 244 * bmi), 2)


def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif bmi < 25:
        return 'Normal'
    elif bmi < 30:
        return 'Overweight'
    elif bmi < 35:
        return 'Obese I'
    elif bmi < 40:
        return 'Obese II'
    else:
        return 'Obese III (Morbid)'


class DrugCategoryListView(APIView):
    """List all drug categories."""

    def get(self, request):
        categories = DrugCategory.objects.all()
        serializer = DrugCategorySerializer(categories, many=True)
        return Response(serializer.data)


class DrugListView(APIView):
    """List all drugs with optional filtering."""

    def get(self, request):
        drugs = Drug.objects.filter(is_active=True).select_related('category')
        category_id = request.query_params.get('category')
        if category_id:
            drugs = drugs.filter(category_id=category_id)
        serializer = DrugSerializer(drugs, many=True)
        return Response(serializer.data)


class DosageCalculatorView(APIView):
    """
    Core endpoint: given patient age, sex, weight and height,
    return appropriate drugs with calculated dosages.
    Uses IBW/ABW per standard anesthesia dosing practice.
    """

    def post(self, request):
        query_serializer = DosageQuerySerializer(data=request.data)
        if not query_serializer.is_valid():
            return Response(
                {'errors': query_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        age = query_serializer.validated_data['age']
        sex = query_serializer.validated_data['sex']
        weight = query_serializer.validated_data['weight']
        height = query_serializer.validated_data['height']

        # Body composition calculations
        bmi = calculate_bmi(weight, height)
        ibw = calculate_ibw(sex, height)
        lbw = calculate_lbw(sex, weight, height)

        # Filter drugs by age and sex
        drugs = Drug.objects.filter(is_active=True).select_related('category')
        drugs = drugs.filter(min_age__lte=age)
        drugs = drugs.filter(Q(max_age__isnull=True) | Q(max_age__gte=age))
        drugs = drugs.filter(Q(sex_indication='both') | Q(sex_indication=sex))

        # Group by category
        categories = DrugCategory.objects.filter(drugs__in=drugs).distinct()

        result = []
        for category in categories:
            cat_drugs = drugs.filter(category=category)
            serializer = CalculatedDrugSerializer(
                cat_drugs,
                many=True,
                context={'age': age, 'weight': weight, 'ibw': ibw, 'lbw': lbw, 'bmi': bmi}
            )
            result.append({
                'category_id': category.id,
                'category_name': category.name,
                'category_icon': category.icon,
                'category_description': category.description,
                'drugs': serializer.data,
            })

        # Log the calculation
        calc = DosageCalculation.objects.create(
            patient_age=age,
            patient_sex=sex,
            patient_weight=weight,
            patient_height=height,
        )
        calc.drugs_shown.set(drugs)

        return Response({
            'patient': {
                'age': age,
                'sex': sex,
                'weight': weight,
                'height': height,
                'bmi': bmi,
                'bmi_category': bmi_category(bmi),
                'ibw': ibw,
                'lbw': lbw,
                'age_group': self._get_age_group(age),
            },
            'total_drugs': drugs.count(),
            'categories': result,
        })

    def _get_age_group(self, age):
        if age < 1:
            return 'Neonate'
        elif age < 12:
            return 'Pediatric'
        elif age < 18:
            return 'Adolescent'
        elif age < 65:
            return 'Adult'
        else:
            return 'Elderly'


class DrugDetailView(APIView):
    """Get detailed info about a specific drug."""

    def get(self, request, pk):
        try:
            drug = Drug.objects.get(pk=pk, is_active=True)
        except Drug.DoesNotExist:
            return Response({'error': 'Drug not found'}, status=status.HTTP_404_NOT_FOUND)

        age = int(request.query_params.get('age', 30))
        weight = float(request.query_params.get('weight', 70))
        height = float(request.query_params.get('height', 170))
        sex = request.query_params.get('sex', 'male')

        bmi = calculate_bmi(weight, height)
        ibw = calculate_ibw(sex, height)
        lbw = calculate_lbw(sex, weight, height)

        serializer = CalculatedDrugSerializer(
            drug,
            context={'age': age, 'weight': weight, 'ibw': ibw, 'lbw': lbw, 'bmi': bmi}
        )
        return Response(serializer.data)


class HealthCheckView(APIView):
    """Simple health check endpoint."""

    def get(self, request):
        return Response({'status': 'ok', 'message': 'Anesthesia Dosage API is running'})
