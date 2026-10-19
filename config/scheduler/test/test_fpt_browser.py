"""Run with RUN_FPT_BROWSER_TESTS=1 after installing requirements-test.txt.

Uses a disposable Django live-server database and real Chromium, including CSRF
and the shipped calendar JavaScript. Normal backend runs need no browser install.
"""

import os
import re
from datetime import date
from unittest import skipUnless

from django.contrib.auth.models import Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, tag

from scheduler.models import FPTPeriod, FPTSession
from .factories import UserFactory


@tag('browser')
@skipUnless(os.environ.get('RUN_FPT_BROWSER_TESTS') == '1', 'Enable RUN_FPT_BROWSER_TESTS to run Chromium regressions')
class FPTBrowserTests(StaticLiveServerTestCase):
    host = '127.0.0.1'

    def setUp(self):
        from playwright.sync_api import sync_playwright, expect
        self.expect = expect
        self.manager = UserFactory(role='STAFF')
        self.viewer = UserFactory(role='STAFF')
        self.student = UserFactory(role='STUDENT', first_name='Student', last_name='Test')
        self.instructor = UserFactory(role='INSTRUCTOR')
        self.manager.user_permissions.add(Permission.objects.get(codename='manage_fpt_schedule'))
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_fpt_schedule'))
        self.period = FPTPeriod.objects.create(start_date=date(2026, 11, 2), end_date=date(2026, 11, 15), is_active=True)
        FPTSession.objects.create(period=self.period, date=self.period.start_date, start_hour=10,
                                  student=self.student, instructor=self.instructor, category='HVI')
        self.cookies = {}
        for key, user in [('manager', self.manager), ('viewer', self.viewer)]:
            client = Client()
            client.force_login(user)
            self.cookies[key] = client.cookies['sessionid'].value
        self.playwright = sync_playwright().start()
        self.addCleanup(self.playwright.stop)
        options = {'headless': True}
        if os.environ.get('FPT_BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['FPT_BROWSER_EXECUTABLE']
        self.browser = self.playwright.chromium.launch(**options)
        self.addCleanup(self.browser.close)
        self.context = self.new_context('manager')
        self.page = self.context.new_page()

    def new_context(self, role, **options):
        context = self.browser.new_context(**options)
        context.add_cookies([{'name': 'sessionid', 'value': self.cookies[role], 'domain': self.host, 'path': '/'}])
        self.addCleanup(context.close)
        return context

    def open_calendar(self, page=None):
        page = page or self.page
        page.goto(self.live_server_url + '/scheduler/fpt/')
        self.expect(page.locator('#calendar-grid')).to_have_attribute('aria-busy', 'false')
        self.expect(page.locator('#page-message')).not_to_have_class(re.compile('fpt-error'))

    def open_existing(self, page=None):
        (page or self.page).get_by_role('button', name=re.compile(r'02 nov\. 2026, 10:00:')).click()

    def save(self, page=None):
        page = page or self.page
        page.get_by_role('button', name='Guardar', exact=True).click()
        self.expect(page.locator('#session-dialog')).not_to_be_visible()
        self.expect(page.locator('#page-message')).to_have_text('Sesión guardada.')

    def test_book_reschedule_pay_and_lock(self):
        self.open_calendar()
        self.page.get_by_role('button', name='02 nov. 2026, 08:00: Libre', exact=True).click()
        self.page.get_by_label('Estudiante registrado', exact=True).select_option(str(self.student.pk))
        self.page.get_by_label('Instructor registrado', exact=True).select_option(str(self.instructor.pk))
        self.page.get_by_label('Categoría', exact=True).select_option('ENT')
        self.save()
        self.page.get_by_role('button', name=re.compile(r'02 nov\. 2026, 08:00:')).click()
        self.page.get_by_label('Hora de inicio', exact=True).select_option('14')
        self.page.get_by_label('Estado de pago', exact=True).select_option('paid')
        self.page.get_by_label('Estudiante', exact=True).select_option('external')
        self.page.get_by_label('Nombre del estudiante externo', exact=True).fill('Alumno informal')
        self.save()
        paid = self.page.get_by_role('button', name=re.compile(r'02 nov\. 2026, 14:00:'))
        self.expect(paid).to_contain_text('Reservado, pagado')
        self.expect(paid).to_contain_text('Alumno informal')
        self.page.get_by_role('button', name='02 nov. 2026, 08:00: Libre', exact=True).click()
        self.page.get_by_label('Tipo', exact=True).select_option('locked')
        self.save()
        self.expect(self.page.get_by_role('button', name=re.compile(r'02 nov\. 2026, 08:00:'))).to_contain_text('Bloqueado')

    def test_two_open_dialogs_cannot_revert_payment_and_can_reload(self):
        self.open_calendar()
        other = self.context.new_page()
        self.open_calendar(other)
        self.open_existing()
        self.open_existing(other)
        self.page.get_by_label('Estado de pago', exact=True).select_option('paid')
        self.save()
        other.get_by_label('Notas (opcional)', exact=True).fill('Unsaved notes')
        other.get_by_role('button', name='Guardar', exact=True).click()
        self.expect(other.get_by_role('alert')).to_contain_text('Otro usuario modificó')
        self.expect(other.get_by_label('Notas (opcional)', exact=True)).to_have_value('Unsaved notes')
        other.get_by_role('button', name='Recargar datos actuales', exact=True).click()
        self.expect(other.get_by_label('Estado de pago', exact=True)).to_have_value('paid')
        self.expect(other.get_by_label('Notas (opcional)', exact=True)).to_have_value('')

    def test_viewer_gets_details_without_booking_or_management_controls(self):
        viewer = self.new_context('viewer').new_page()
        self.open_calendar(viewer)
        self.expect(viewer.locator('#new-period')).to_have_count(0)
        self.expect(viewer.locator('td.fpt-free button')).to_have_count(0)
        self.open_existing(viewer)
        self.expect(viewer.get_by_role('dialog')).to_contain_text('Student Test')
        self.expect(viewer.locator('#session-form')).to_have_count(0)

    def test_mobile_delete_label_back_style_and_dialog_fit(self):
        mobile = self.new_context('manager', viewport={'width': 390, 'height': 844}).new_page()
        self.open_calendar(mobile)
        style = mobile.locator('.back-button .button').evaluate('el => ({background: getComputedStyle(el).backgroundColor, padding: getComputedStyle(el).padding, width: el.getBoundingClientRect().width})')
        self.assertEqual(style['background'], 'rgba(0, 0, 0, 0)')
        self.assertEqual(style['padding'], '8px 15px')
        self.assertLess(style['width'], 160)
        self.assertTrue(mobile.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth'))
        self.open_existing(mobile)
        self.expect(mobile.locator('#delete-session')).to_have_text('Eliminar')
        self.assertTrue(mobile.locator('#delete-session').evaluate('el => el.scrollWidth <= el.clientWidth'))
        self.assertTrue(mobile.locator('#session-dialog').evaluate('el => el.getBoundingClientRect().width <= document.documentElement.clientWidth'))
        mobile.locator('#delete-session').click()
        self.expect(mobile.locator('#delete-dialog')).to_be_visible()
        mobile.locator('#confirm-delete').click()
        self.expect(mobile.locator('#page-message')).to_have_text('Eliminación completada.')

    def test_period_form_enforces_monday_to_sunday(self):
        self.open_calendar()
        self.page.locator('#new-period').click()
        self.page.get_by_label('Inicio', exact=True).fill('2026-11-17')
        self.page.get_by_label('Cierre', exact=True).fill('2026-11-22')
        self.page.get_by_role('button', name='Guardar', exact=True).click()
        self.assertFalse(self.page.locator('#period-start').evaluate('el => el.validity.valid'))
        self.page.get_by_label('Inicio', exact=True).fill('2026-11-16')
        self.page.get_by_role('button', name='Guardar', exact=True).click()
        self.expect(self.page.locator('#page-message')).to_have_text('Periodo guardado.')
