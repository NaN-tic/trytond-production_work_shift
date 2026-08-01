import unittest
from types import SimpleNamespace
from unittest.mock import patch

from trytond.modules.valero.production_app.state import ensure_active_shift_record
from trytond.tests.test_tryton import drop_db


class TestShiftRecordWithoutEmployee(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        user = SimpleNamespace(
            id=17,
            login='rbotto',
            rec_name='Ruben Botto',
            active=True,
            party=SimpleNamespace(name='RUBEN BOTTO'),
            employee=None,
            employees=[],
            company=SimpleNamespace(id=3),
        )

        class FakeShiftRecord:

            created = []

            def __init__(self, **values):
                self.__dict__.update(values)
                self.id = 101
                self.saved = False
                FakeShiftRecord.created.append(dict(values))

            def save(self):
                self.saved = True

        class FakeCreateShiftRecord:

            @classmethod
            def create_shift_record(cls, values):
                record = FakeShiftRecord(**values)
                record.save()
                return record

        session = SimpleNamespace(
            id=8,
            active_terminal=SimpleNamespace(id=5),
            active_workplace=2,
            system_user=user,
            get_terminal_shift_record=lambda terminal=None, workplace=None: None,
            set_terminal_shift_record=lambda *args, **kwargs: None,
        )
        shift = SimpleNamespace(id=19)

        with patch(
                'trytond.modules.valero.production_app.state.Pool') as PoolMock, \
                patch(
                    'trytond.modules.valero.production_app.state.get_active_shift',
                    return_value=shift), patch(
                    'trytond.modules.valero.production_app.state.get_user_employee',
                    return_value=None), patch(
                    'trytond.modules.valero.production_app.state.get_session_work',
                    return_value=None), patch(
                    'trytond.modules.valero.production_app.state.get_session_work_center',
                    return_value=None), patch(
                    'trytond.modules.valero.production_app.state.get_session_operation',
                    return_value=None), patch(
                    'trytond.modules.valero.production_app.state.get_session_production',
                    return_value=None), patch(
                    'trytond.modules.valero.production_app.state.get_session_shift_record',
                    return_value=None):
            PoolMock.return_value.get.side_effect = lambda name, type=None: (
                FakeCreateShiftRecord
                if name == 'production.work.shift.record.create'
                else FakeShiftRecord)

            created = ensure_active_shift_record(session)

        self.assertIsNotNone(created)
        self.assertTrue(created.saved)
        self.assertEqual(FakeShiftRecord.created[0]['company'], 3)
        self.assertNotIn('user', FakeShiftRecord.created[0])
