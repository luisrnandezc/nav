from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, date
import json


def default_due_date():
    """Return a date 15 days from today."""
    return timezone.now().date() + timedelta(days=15)

def default_follow_date():
    """Return a date 7 days from today."""
    return timezone.now().date() + timedelta(days=7)


class VoluntaryHazardReport(models.Model):
    """
    Voluntary Hazard Report Model for Safety Management System (SMS)
    """

    #region Choices
    ANONYMOUS_CHOICES = [
        ('YES', 'SI'),
        ('NO', 'NO'),
    ]

    ROLE_CHOICES = [
        ('DIRECTOR', 'Dirección'),
        ('OPERATIONS', 'Operaciones'),
        ('GROUND_INSTRUCTOR', 'Instructor de tierra'),
        ('FLIGHT_INSTRUCTOR', 'Instructor de vuelo'),
        ('STUDENT', 'Alumno'),
        ('ADMIN', 'Administrativo'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Analizando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Error'),
    ]

    AREA_CHOICES = [
        ('ADMIN', 'Sede administrativa'),
        ('PLATFORM', 'Plataforma'),
        ('AIRPORT_OFFICE', 'Ofic. Aeropuerto'),
        ('OPERATIONS', 'Operaciones'),
        ('OTHER', 'Otro'),
    ]
    #endregion
    
    #region Fields
    code = models.CharField(
        max_length=100,
        verbose_name="Código",
        help_text="Código de entrada para la BD del SMS",
        blank=True,
        null=True,
        unique=True
    )
    
    is_anonymous = models.CharField(
        max_length=3,
        choices=ANONYMOUS_CHOICES,
        default='NO',
        verbose_name="Anónimo"
    )
    first_name = models.CharField(
        max_length=200, 
        verbose_name="Nombre",
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=200, 
        verbose_name="Apellido",
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        default='',
        verbose_name="Cargo o función",
        blank=True,
        null=True
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha"
    )
    time = models.TimeField(
        default=timezone.localtime,
        verbose_name="Hora",
    )
    area = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        default='OPERATIONS',
        verbose_name="Área"
    )
    description = models.TextField(
        max_length=1000,
        verbose_name="Descripción del peligro"
    )
    is_valid = models.BooleanField(
        default=False,
        verbose_name="Es válido",
    )
    invalidity_reason = models.TextField(
        verbose_name="Motivo de invalidación",
        blank=True,
        null=True
    )
    ai_analysis_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="IA Estatus",
        db_index=True  # Database index for fast queries
    )
    ai_analysis_result = models.JSONField(
        default=dict,
        verbose_name="Resultado del análisis de IA",
        blank=True,
        null=True
    )
    analysis_email_sent = models.BooleanField(
        default=False,
        verbose_name="Email de análisis enviado",
        help_text="Indica si se ha enviado el email de notificación cuando el análisis fue completado",
    )
    is_registered = models.BooleanField(
        default=False,
        verbose_name="Registrado",
    )
    is_processed = models.BooleanField(
        default=False,
        verbose_name="Procesado",
        help_text="Indica si se han creado las MMRs para el reporte",
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Resuelto",
        help_text="Indica si el reporte ha sido resuelto",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
        blank=True,
        null=True
    )
    #endregion

    class Meta:
        verbose_name = "RVP"
        verbose_name_plural = "RVP"
        
    def __str__(self):
        if self.code:
            return "{} - {}".format(self.code, self.area)
        else:
            return "NO REGISTRADO - {}".format(self.area)
    
    def has_ai_analysis(self):
        """Check if this report has a completed AI hazard analysis"""
        return self.ai_analysis_status == 'COMPLETED'


class Risk(models.Model):
    """
    Risk Model for Safety Management System (SMS)
    """

    #region Choices
    STATUS_CHOICES = [
        ('NOT_EVALUATED', 'No evaluado'),
        ('INTOLERABLE', 'Intolerable'),
        ('TOLERABLE', 'Tolerable'),
        ('ACCEPTABLE', 'Aceptable'),
    ]

    CONDITION_CHOICES = [
        ('UNMITIGATED', 'Sin mitigar'),
        ('MITIGATED', 'Mitigado'),
    ]

    SEVERITY_CHOICES = [
        ('0', '-'),
        ('A', 'A - Catastrófico'),
        ('B', 'B - Peligroso'),
        ('C', 'C - Grave'),
        ('D', 'D - Leve'),
        ('E', 'E - Insignificante'),
    ]

    PROBABILITY_CHOICES = [
        ('0', '-'),
        ('1', '1 - Sumamente improbable'),
        ('2', '2 - Improbable'),
        ('3', '3 - Remota'),
        ('4', '4 - Ocasional'),
        ('5', '5 - Frecuente'),
    ]
    #endregion

    #region Fields
    report = models.ForeignKey(
        VoluntaryHazardReport, 
        on_delete=models.CASCADE, 
        verbose_name="Reporte Voluntario de Peligro",
        related_name="risks"
    )
    description = models.TextField(
        verbose_name="Descripción",
    )
    pre_evaluation_severity = models.CharField(
        max_length=1,
        choices=SEVERITY_CHOICES,
        default='0',
        verbose_name="Severidad pre-mitigación"
    )
    pre_evaluation_probability = models.CharField(
        max_length=1, 
        choices=PROBABILITY_CHOICES,
        default='0',
        verbose_name="Probabilidad pre-mitigación"
    )
    post_evaluation_severity = models.CharField(
        max_length=1, 
        choices=SEVERITY_CHOICES,
        default='0',
        verbose_name="Severidad post-mitigación"
    )
    post_evaluation_probability = models.CharField(
        max_length=1, 
        choices=PROBABILITY_CHOICES,
        default='0',
        verbose_name="Probabilidad post-mitigación"
    )
    post_evaluation_justification = models.TextField(
        blank=True,
        verbose_name="Justificación de la evaluación residual",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_EVALUATED',
        verbose_name="Estatus"
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='UNMITIGATED',
        verbose_name="Condición"
    )
    created_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        verbose_name = "Riesgo"
        verbose_name_plural = "Riesgos"
        
    def __str__(self):
        if self.report.code:
            return "{} - {} - ID: {}".format(self.report.code, self.condition, self.id)
        else:
            return "NO REGISTRADO - {} - ID: {}".format(self.condition, self.id)

    def pre_evaluation(self):
        """Return the risk evaluation before mitigation"""
        return f"{self.pre_evaluation_severity}{self.pre_evaluation_probability}"
    pre_evaluation.short_description = "Pre-evaluación"

    def post_evaluation(self):
        """Return the risk evaluation after mitigation, or '-' if unavailable."""
        if (
            self.post_evaluation_severity == '0'
            or self.post_evaluation_probability == '0'
        ):
            return '-'
        return f"{self.post_evaluation_severity}{self.post_evaluation_probability}"
    post_evaluation.short_description = "Post-evaluación"


class RiskEvaluationReport(models.Model):
    """
    Risk evaluation report associated with a processed voluntary hazard report.

    A RER documents every consequence (Risk instance) selected while processing
    the VHR. One risk is selected as the worst consequence and supplies the
    initial matrix index. Its initial and residual evaluations remain on that
    selected Risk, while every mitigation action and its evidence is documented
    by the RER.
    """

    #region Choices
    HAZARD_SOURCE_CHOICES = [
        ('VHR', 'Reporte Voluntario de Peligro'),
        ('ROS', 'Reporte Obligatorio de Suceso'),
        ('INT_AUD', 'Auditoría Interna'),
        ('EXT_AUD', 'Auditoría Externa'),
    ]

    HAZARD_TYPE_CHOICES = [
        ('ENV', 'Ambiental'),
        ('TEC', 'Técnico'),
        ('ORG', 'Organizacional'),
        ('HUM', 'Humano'),
    ]

    ANALYSIS_STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('PENDING', 'Pendiente de análisis'),
        ('PROCESSING', 'Analizando'),
        ('READY_FOR_REVIEW', 'Listo para revisión'),
        ('FAILED', 'Error en el análisis'),
        ('REVIEWED', 'Revisado'),
    ]
    #endregion

    #region Fields
    report = models.OneToOneField(
        VoluntaryHazardReport,
        on_delete=models.CASCADE,
        verbose_name="Reporte Voluntario de Peligro",
        related_name="risk_evaluation_report",
    )
    selected_risk = models.ForeignKey(
        Risk,
        on_delete=models.RESTRICT,
        verbose_name="Riesgo de referencia",
        related_name="risk_evaluation_reports",
        help_text="Peor consecuencia seleccionada para el índice de riesgo inicial.",
    )
    registration_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de registro",
    )
    sms_user_fullname = models.CharField(
        max_length=200,
        verbose_name="Coordinador de SMS",
    )
    dir_user_fullname = models.CharField(
        max_length=200,
        verbose_name="Director",
    )
    hazard_description = models.TextField(
        max_length=300,
        verbose_name="Descripción del peligro",
    )
    hazard_source = models.CharField(
        max_length=10,
        choices=HAZARD_SOURCE_CHOICES,
        default='VHR',
        verbose_name="Fuente del peligro",
    )
    hazard_type = models.CharField(
        max_length=3,
        choices=HAZARD_TYPE_CHOICES,
        verbose_name="Tipo de peligro",
    )
    hazard_area = models.CharField(
        max_length=20,
        choices=VoluntaryHazardReport.AREA_CHOICES,
        verbose_name="Área del peligro",
    )
    hazard_causes = models.TextField(
        max_length=1000,
        verbose_name="Posibles causas",
    )
    defenses = models.TextField(
        max_length=500,
        verbose_name="Defensas existentes",
    )
    analysis_status = models.CharField(
        max_length=20,
        choices=ANALYSIS_STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Estado del análisis residual",
        db_index=True,
    )
    analysis_error = models.TextField(
        blank=True,
        verbose_name="Error del análisis residual",
    )
    analysis_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Inicio del análisis residual",
    )
    analysis_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Finalización del análisis residual",
    )
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de revisión",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="reviewed_risk_evaluation_reports",
        verbose_name="Revisado por",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )
    #endregion

    class Meta:
        verbose_name = "Registro de Evaluación de Riesgos"
        verbose_name_plural = "Registros de Evaluación de Riesgos"

    def __str__(self):
        report_code = self.report.code or f"RVP {self.report_id}"
        return f"RER - {report_code}"

    def clean(self):
        super().clean()
        if (
            self.report_id
            and self.selected_risk_id
            and self.selected_risk.report_id != self.report_id
        ):
            raise ValidationError({
                'selected_risk': (
                    'El riesgo seleccionado debe pertenecer al reporte '
                    'voluntario asociado con este RER.'
                )
            })


class MitigationAction(models.Model):
    """
    Mitigation Action Model for Safety Management System (SMS)
    """

    #region Choices
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Completado'),
        ('EXPIRED', 'Expirado'),
    ]
    #endregion

    #region Fields
    risk = models.ForeignKey(
        Risk, 
        on_delete=models.CASCADE, 
        verbose_name="Riesgo",
        related_name="mitigation_actions"
    )
    description = models.TextField(
        verbose_name="Descripción",
    )
    status=models.CharField(
        max_length=9,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estatus",
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Responsable",
        related_name="responsible_for_mitigation_actions",
        limit_choices_to=Q(role='STAFF') | Q(role='INSTRUCTOR'),
        blank=True,
        null=True,
        help_text="Solo usuarios con rol de Staff o Instructor pueden ser asignados como responsables"
    )
    follow_date = models.DateField(
        default=default_follow_date,
        verbose_name="Fecha de seguimiento"
    )
    due_date = models.DateField(
        default=default_due_date,
        verbose_name="Fecha límite"
    )
    notes = models.TextField(
        verbose_name="Notas",
        blank=True,
        null=True
    )
    created_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        verbose_name = "MMR"
        verbose_name_plural = "MMR"
        
    def __str__(self):
        if self.risk.report.code:
            return "{} - {}".format(self.risk.report.code, self.status)
        else:
            return "NO REGISTRADO - {}".format(self.status)


class MitigationActionEvidence(models.Model):
    """Mitigation Action Evidence Model for Safety Management System (SMS)
    
    This Evidence instances will serve to close a specific Mitigation Action.
    Each MitigationAction can have only ONE evidence."""

    #region Fields
    mitigation_action = models.OneToOneField(
        MitigationAction, 
        on_delete=models.CASCADE, 
        verbose_name="MMR",
        related_name="evidence"
    )
    description = models.TextField(
        verbose_name="Descripción",
    )
    created_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de actualización"
    )
    #endregion

    class Meta:
        verbose_name = "Evidencia MMR"
        verbose_name_plural = "Evidencias MMR"
        
    def __str__(self):
        if self.mitigation_action.risk.report.code:
            return "{} - Evidencia {}".format(self.mitigation_action.risk.report.code, self.id)
        else:
            return "REPORTE NO REGISTRADO - Evidencia {}".format(self.id)
