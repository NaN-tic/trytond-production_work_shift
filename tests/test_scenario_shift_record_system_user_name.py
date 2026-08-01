import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from trytond.modules.valero.production_app.configuration import (
    WorkplaceLineSubmit, WorkplaceNameConfiguration, WorkplaceNameSubmit,
    WorkplaceOperationSubmit, WorkplacePicker,
)
from trytond.tests.test_tryton import drop_db


class TestShiftRecordSystemUserName(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        self.assertEqual(WorkplaceNameSubmit._method, ['GET', 'POST'])
        self.assertEqual(WorkplaceLineSubmit._method, ['GET', 'POST'])
        self.assertEqual(WorkplaceOperationSubmit._method, ['GET', 'POST'])

        terminal = SimpleNamespace(
            id=5,
            system_user=SimpleNamespace(id=9),
            default_operation=SimpleNamespace(id=11),
        )
        session = SimpleNamespace(
            active_terminal=terminal,
            active_workplace=None,
            system_user=None,
            set_active_terminal_admin_mode=lambda value: None,
            set_active_workplace=lambda value: None,
            set_active_shift=lambda value: None,
            set_active_work_center=lambda value: None,
            set_active_operation=lambda value: None,
            set_active_production=lambda value: None,
            set_active_work=lambda value: None,
            set_terminal_shift_record=lambda *args, **kwargs: None,
            set_system_user=lambda value: None,
        )

        class WorkplaceNamePage:

            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def url(self):
                return f"/workplace/name/{self.kwargs['workplace']}"

        shift = SimpleNamespace(id=7, name='Manana')

        class ShiftDefinition:

            @staticmethod
            def search(domain, limit=None, order=None):
                return [shift]

        picker = SimpleNamespace(
            workplace=4,
            session=session,
            _get_workplace_shift_record=lambda workplace: None,
            _next_url=lambda skip_shift_record_quality=False: '/next',
        )
        with patch(
                'trytond.modules.valero.production_app.configuration.Pool') as PoolMock:
            PoolMock.return_value.get.side_effect = lambda name: (
                WorkplaceNamePage if name == 'www.production.workplace.name'
                else ShiftDefinition if name == 'working.shift.definition'
                else None)
            response = WorkplacePicker.select_workplace(picker)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/workplace/name/4')

        name_page = SimpleNamespace(
            workplace=4,
            shift_record_name='BETETA HERRANZ, M DOLORES',
            turn='7',
            session=session,
            _get_turn_id=lambda: 7,
            _get_workplace_shift_record=lambda workplace: None,
            _set_terminal_shift_record=lambda shift_record: (
                session.set_terminal_shift_record(
                    shift_record.id if shift_record else None,
                    terminal=terminal.id,
                    workplace=4)
                if shift_record else session.set_terminal_shift_record(None)),
            _next_url=lambda skip_shift_record_quality=False: '/next',
        )

        open_record = SimpleNamespace(
            id=88,
            state='active',
            shift=shift,
            line=SimpleNamespace(id=33),
            operation=SimpleNamespace(id=44),
            production=SimpleNamespace(id=55),
            work=SimpleNamespace(id=66),
        )
        session.get_terminal_shift_record = (
            lambda terminal=None, workplace=None: open_record)
        shift_record_model = MagicMock()
        with patch(
                'trytond.modules.valero.production_app.configuration.Pool') as PoolMock, patch(
                'trytond.modules.valero.production_app.configuration.ensure_active_shift_record') as ensure_mock:
            PoolMock.return_value.get.side_effect = lambda name: (
                ShiftDefinition if name == 'working.shift.definition'
                else shift_record_model if name == 'production.work.shift.record'
                else None)
            response = WorkplaceNameConfiguration.submit(name_page)

        ensure_mock.assert_not_called()
        shift_record_model.write.assert_called_once_with([open_record], {
            'system_user_name': 'BETETA HERRANZ, M DOLORES',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/next')

        session.get_terminal_shift_record = lambda terminal=None, workplace=None: None

        shift_record_model = MagicMock()
        with patch(
                'trytond.modules.valero.production_app.configuration.Pool') as PoolMock, patch(
                'trytond.modules.valero.production_app.configuration.ensure_active_shift_record') as ensure_mock:
            PoolMock.return_value.get.side_effect = lambda name: (
                ShiftDefinition if name == 'working.shift.definition'
                else shift_record_model if name == 'production.work.shift.record'
                else None)
            ensure_mock.return_value = SimpleNamespace(
                id=42, state='active', line=None, operation=None,
                production=None, work=None)
            response = WorkplaceNameConfiguration.submit(name_page)

        ensure_mock.assert_called_once_with(
            session, shift=shift, system_user_name='BETETA HERRANZ, M DOLORES')
        shift_record_model.write.assert_called_once_with(
            [ensure_mock.return_value], {'operation': 11})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/next')
