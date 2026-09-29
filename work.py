# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

import datetime

from trytond.model import ModelSQL, ModelView, fields
from trytond.modules.company.model import employee_field
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.wizard import Button, StateAction, StateView, Wizard


class WorkShiftRecord(ModelSQL, ModelView):
    'Work Shift Record'
    __name__ = 'production.work.shift.record'

    company = fields.Many2One('company.company', 'Company', required=True)
    work = fields.Many2One(
        'production.work', 'Work', ondelete='CASCADE',
        states={'editable': False})
    production = fields.Many2One(
        'production', 'Production', states={'editable': False})
    workplace = fields.Integer('Workplace', required=True, readonly=True)
    date = fields.Date('Date', required=True, readonly=True)
    shift = fields.Many2One(
        'working.shift.definition', 'Shift', required=True, readonly=True)
    user = employee_field('User')
    line = fields.Many2One(
        'production.work.center', 'Line', required=False, readonly=True)
    operation = fields.Many2One(
        'production.routing.operation', 'Operation',
        states={'editable': False})
    cycles = fields.One2Many(
        'production.work.cycle', 'shift_record', 'Cycles',
        readonly=True)
    state = fields.Selection([
            ('active', 'Active'),
            ('finished', 'Finished'),
            ], 'State', required=True, readonly=True, sort=False)

    @classmethod
    def default_company(cls):
        return Transaction().context.get('company')

    @classmethod
    def default_state(cls):
        return 'active'

    @classmethod
    def default_date(cls):
        return datetime.date.today()

    def get_rec_name(self, name):
        if self.user:
            return '%s@%s' % (self.shift.name, self.user.rec_name)
        return str(self.id)


class CreateWorkShiftRecordStart(ModelView):
    'Create Work Shift Record'
    __name__ = 'production.work.shift.record.create.start'

    company = fields.Many2One('company.company', 'Company', required=True)
    work = fields.Many2One(
        'production.work', 'Work',
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    production = fields.Many2One(
        'production', 'Production',
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    workplace = fields.Integer('Workplace', required=True)
    date = fields.Date('Date', required=True)
    shift = fields.Many2One(
        'working.shift.definition', 'Shift', required=True)
    user = fields.Many2One('company.employee', 'User')
    line = fields.Many2One(
        'production.work.center', 'Line',
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    operation = fields.Many2One(
        'production.routing.operation', 'Operation')

    @classmethod
    def default_company(cls):
        return Transaction().context.get('company')

    @classmethod
    def default_date(cls):
        Date = Pool().get('ir.date')
        return Date.today()

    @classmethod
    def default_user(cls):
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if user.employee:
            return user.employee.id

    @fields.depends('work', 'company', 'production', 'operation', 'line')
    def on_change_work(self):
        if not self.work:
            return
        self.company = self.work.company
        self.production = self.work.production
        self.operation = self.work.operation
        self.line = self.work.work_center


class CreateWorkShiftRecord(Wizard):
    'Create Work Shift Record'
    __name__ = 'production.work.shift.record.create'
    start = StateView(
        'production.work.shift.record.create.start',
        'production_work_shift.work_shift_record_create_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('production_work_shift.act_shift_record')

    @classmethod
    def create_shift_record(cls, values):
        ShiftRecord = Pool().get('production.work.shift.record')
        shift_values = {
            key: value for key, value in values.items()
            if value is not None
        }
        shift_record, = ShiftRecord.create([shift_values])
        return shift_record

    def do_create_(self, action):
        values = {
            'company': self.start.company.id,
            'work': self.start.work.id if self.start.work else None,
            'production': (
                self.start.production.id if self.start.production else None),
            'workplace': self.start.workplace,
            'date': self.start.date,
            'shift': self.start.shift.id,
            'user': self.start.user.id if self.start.user else None,
            'line': self.start.line.id if self.start.line else None,
            'operation': (
                self.start.operation.id if self.start.operation else None),
            'state': 'active',
            }
        shift_record = self.create_shift_record(values)
        return action, {
            'res_id': [shift_record.id],
            'views': list(reversed(action['views'])),
            }


class WorkCycle(metaclass=PoolMeta):
    __name__ = 'production.work.cycle'

    shift_record = fields.Many2One(
        'production.work.shift.record', 'Shift Record',
        states={
            'readonly': Eval('state').in_(['running', 'done', 'cancelled']),
            },
        depends=['state'])
