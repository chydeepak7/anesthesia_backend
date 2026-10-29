from django.db import models


class DrugCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, default='💊')

    class Meta:
        verbose_name_plural = "Drug Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Drug(models.Model):
    ROUTE_CHOICES = [
        ('IV', 'Intravenous'),
        ('IM', 'Intramuscular'),
        ('PO', 'Oral'),
        ('SC', 'Subcutaneous'),
        ('IN', 'Intranasal'),
        ('SL', 'Sublingual'),
        ('IT', 'Intrathecal'),
        ('EP', 'Epidural'),
    ]

    SEX_CHOICES = [
        ('both', 'Both'),
        ('male', 'Male Only'),
        ('female', 'Female Only'),
    ]

    category = models.ForeignKey(DrugCategory, on_delete=models.CASCADE, related_name='drugs')
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    drug_class = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=10, choices=ROUTE_CHOICES, default='IV')
    sex_indication = models.CharField(max_length=10, choices=SEX_CHOICES, default='both')

    # Dosage fields
    adult_dose_min = models.FloatField(help_text="Minimum adult dose in mg/kg")
    adult_dose_max = models.FloatField(help_text="Maximum adult dose in mg/kg")
    pediatric_dose_min = models.FloatField(null=True, blank=True, help_text="Minimum pediatric dose in mg/kg")
    pediatric_dose_max = models.FloatField(null=True, blank=True, help_text="Maximum pediatric dose in mg/kg")
    elderly_dose_min = models.FloatField(null=True, blank=True, help_text="Minimum elderly dose (age>65) in mg/kg")
    elderly_dose_max = models.FloatField(null=True, blank=True, help_text="Maximum elderly dose (age>65) in mg/kg")
    dose_unit = models.CharField(max_length=60, default='mg/kg')
    max_absolute_dose = models.FloatField(null=True, blank=True, help_text="Maximum absolute dose in mg regardless of weight")

    # Age restrictions
    min_age = models.IntegerField(default=0, help_text="Minimum age in years")
    max_age = models.IntegerField(null=True, blank=True, help_text="Maximum age in years (null = no limit)")
    pediatric_age_limit = models.IntegerField(default=12, help_text="Age below which pediatric dosing applies")
    elderly_age_threshold = models.IntegerField(default=65, help_text="Age above which elderly dosing applies")

    # Clinical info
    onset_time = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    mechanism = models.TextField(blank=True)
    indications = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    warnings = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_dose_for_patient(self, age, weight=70, ibw=None, lbw=None, bmi=None):
        """
        Calculate dose range for a specific patient.
        Uses IBW/ABW for anesthetic agents per standard practice.
        - BMI < 30: use IBW if IBW < actual weight, else actual weight
        - BMI >= 30 (obese): use Adjusted BW = IBW + 0.4*(TBW - IBW)
        Falls back to actual weight when height not provided.
        """
        if age < self.pediatric_age_limit and self.pediatric_dose_min:
            dose_min = self.pediatric_dose_min
            dose_max = self.pediatric_dose_max
            age_group = 'Pediatric'
        elif age >= self.elderly_age_threshold and self.elderly_dose_min:
            dose_min = self.elderly_dose_min
            dose_max = self.elderly_dose_max
            age_group = 'Elderly'
        else:
            dose_min = self.adult_dose_min
            dose_max = self.adult_dose_max
            age_group = 'Adult'

        # Determine dosing weight
        dose_basis = 'actual'
        dose_basis_label = 'Actual Body Weight'
        dosing_weight = weight

        if ibw is not None and ibw > 0 and bmi is not None:
            if bmi >= 30:
                # Obese: Adjusted Body Weight
                abw = round(ibw + 0.4 * (weight - ibw), 2)
                dosing_weight = max(abw, ibw)  # ABW shouldn't be less than IBW
                dose_basis = 'adjusted'
                dose_basis_label = f'Adjusted BW ({dosing_weight} kg)'
            elif ibw < weight:
                # Not obese, IBW is less than actual → use IBW
                dosing_weight = ibw
                dose_basis = 'ibw'
                dose_basis_label = f'IBW ({ibw} kg)'
            # else IBW >= actual weight (very thin) → use actual weight

        calculated_min = round(dose_min * dosing_weight, 2)
        calculated_max = round(dose_max * dosing_weight, 2)

        if self.max_absolute_dose:
            calculated_min = min(calculated_min, self.max_absolute_dose)
            calculated_max = min(calculated_max, self.max_absolute_dose)

        return {
            'dose_min_per_kg': dose_min,
            'dose_max_per_kg': dose_max,
            'calculated_min_mg': calculated_min,
            'calculated_max_mg': calculated_max,
            'dosing_weight_kg': round(dosing_weight, 2),
            'age_group': age_group,
            'dose_basis': dose_basis,
            'dose_basis_label': dose_basis_label,
        }


class DosageCalculation(models.Model):
    """Stores calculation history."""
    patient_age = models.IntegerField()
    patient_sex = models.CharField(max_length=10)
    patient_weight = models.FloatField(default=70)
    patient_height = models.FloatField(default=170)
    drugs_shown = models.ManyToManyField(Drug, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calc: Age {self.patient_age}, {self.patient_sex}, {self.patient_weight}kg, {self.patient_height}cm"
