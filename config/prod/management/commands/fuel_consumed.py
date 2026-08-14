from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from prod.services import get_fuel_consumed


EVALUATION_CHOICES = ('0-100', '100-120', '120-170', 'all')


class Command(BaseCommand):
    help = 'Calculate flight hours and fuel consumed by flight evaluations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            required=True,
            help='Inclusive starting date in YYYY-MM-DD format.',
        )
        parser.add_argument(
            '--end',
            required=True,
            help='Inclusive ending date in YYYY-MM-DD format.',
        )
        parser.add_argument(
            '--evaluations',
            nargs='+',
            choices=EVALUATION_CHOICES,
            default=['all'],
            help='Evaluation groups to include (default: all).',
        )
        parser.add_argument(
            '--aircraft',
            default='all',
            help='Aircraft registration, or "all" (default: all).',
        )

    def handle(self, *args, **options):
        start_date = self._parse_date(options['start'], '--start')
        end_date = self._parse_date(options['end'], '--end')
        evaluation_types = options['evaluations']
        if 'all' in evaluation_types:
            if len(evaluation_types) > 1:
                raise CommandError('"all" cannot be combined with evaluation groups.')
            evaluation_types = None

        try:
            report = get_fuel_consumed(
                start_date=start_date,
                end_date=end_date,
                evaluation_types=evaluation_types,
                aircraft_registration=options['aircraft'],
            )
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc

        aircraft = report.aircraft or 'All aircraft'
        evaluations = ', '.join(report.evaluation_types)
        self.stdout.write(f'Period: {report.start_date} to {report.end_date} (inclusive)')
        self.stdout.write(f'Aircraft: {aircraft}')
        self.stdout.write(f'Evaluations: {evaluations}')
        self.stdout.write(f'Evaluation count: {report.evaluation_count}')
        self.stdout.write(f'Flight hours: {report.flight_hours:.1f}')
        self.stdout.write(f'Fuel consumed: {report.fuel_liters:.1f} L')
        self.stdout.write(f'Fuel cost: ${report.fuel_cost_usd:.2f} USD')

    @staticmethod
    def _parse_date(value, option_name):
        parsed = parse_date(value)
        if parsed is None:
            raise CommandError(f'{option_name} must use YYYY-MM-DD format.')
        return parsed
