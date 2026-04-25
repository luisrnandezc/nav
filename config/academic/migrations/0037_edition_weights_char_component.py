# Generated manually for grading refactor: weights on SubjectEdition, component as string on StudentGrade.

import django.core.validators
from decimal import Decimal

from django.db import migrations, models


def backfill_edition_weights(apps, schema_editor):
    SubjectEdition = apps.get_model('academic', 'SubjectEdition')
    Component = apps.get_model('academic', 'SubjectEditionGradingComponent')
    for se in SubjectEdition.objects.all():
        theory = Component.objects.filter(subject_edition_id=se.pk, code='theory').first()
        practical = Component.objects.filter(subject_edition_id=se.pk, code='practical').first()
        tw = theory.weight if theory else Decimal('1')
        pw = practical.weight if practical else Decimal('0')
        SubjectEdition.objects.filter(pk=se.pk).update(theory_weight=tw, practical_weight=pw)


def backfill_grade_component_codes(apps, schema_editor):
    StudentGrade = apps.get_model('academic', 'StudentGrade')
    Component = apps.get_model('academic', 'SubjectEditionGradingComponent')
    for g in StudentGrade.objects.iterator():
        comp = Component.objects.filter(pk=g.component_id).first()
        code = comp.code if comp else 'theory'
        StudentGrade.objects.filter(pk=g.pk).update(component_code=code)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0036_alter_subjecteditiongradingcomponent_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectedition',
            name='theory_weight',
            field=models.DecimalField(
                decimal_places=3,
                default=Decimal('1'),
                help_text='Solo teoría: 1.0. Con evaluación práctica: 0.8.',
                max_digits=4,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('1')),
                ],
                verbose_name='Peso teoría',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subjectedition',
            name='practical_weight',
            field=models.DecimalField(
                decimal_places=3,
                default=Decimal('0'),
                help_text='Sin práctica: 0. Con práctica: 0.2.',
                max_digits=4,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0')),
                    django.core.validators.MaxValueValidator(Decimal('1')),
                ],
                verbose_name='Peso práctica',
            ),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_edition_weights, noop_reverse),
        migrations.RemoveConstraint(
            model_name='studentgrade',
            name='unique_student_grade_per_component_test_type',
        ),
        migrations.AddField(
            model_name='studentgrade',
            name='component_code',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Componente'),
        ),
        migrations.RunPython(backfill_grade_component_codes, noop_reverse),
        migrations.RemoveField(
            model_name='studentgrade',
            name='component',
        ),
        migrations.RenameField(
            model_name='studentgrade',
            old_name='component_code',
            new_name='component',
        ),
        migrations.AlterField(
            model_name='studentgrade',
            name='component',
            field=models.CharField(
                choices=[('theory', 'Teoría'), ('practical', 'Práctica')],
                max_length=16,
                verbose_name='Componente',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentgrade',
            constraint=models.UniqueConstraint(
                fields=('subject_edition', 'student', 'component', 'test_type'),
                name='unique_student_grade_per_edition_component_test_type',
                violation_error_message='Ya existe una nota para este estudiante, edición, componente y tipo de examen',
            ),
        ),
        migrations.RemoveConstraint(
            model_name='subjecteditiongradingcomponent',
            name='unique_grading_component_kind_per_edition',
        ),
        migrations.RemoveConstraint(
            model_name='subjecteditiongradingcomponent',
            name='unique_grading_component_code_per_edition',
        ),
        migrations.DeleteModel(
            name='SubjectEditionGradingComponent',
        ),
    ]
