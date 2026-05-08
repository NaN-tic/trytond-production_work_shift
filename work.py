# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

import datetime

from trytond.model import ModelSQL, ModelView, fields
from trytond.modules.company.model import employee_field
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction


class WorkShiftRecord(ModelSQL, ModelView):
    'Work Shift Record'
    __name__ = 'production.work.shift.record'

    company = fields.Many2One('company.company', 'Company', required=True)
    work = fields.Many2One(
        'production.work', 'Work', ondelete='CASCADE',
        readonly=True)
    production = fields.Many2One(
        'production', 'Production', readonly=True)
    workplace = fields.Integer('Workplace', required=True, readonly=True)
    date = fields.Date('Date', required=True, readonly=True)
    shift = fields.Many2One(
        'working.shift.definition', 'Shift', required=True, readonly=True)
    user = employee_field('User')
    line = fields.Many2One(
        'production.work.center', 'Line', required=True, readonly=True)
    operation = fields.Many2One(
        'production.routing.operation', 'Operation',
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


class WorkCycle(metaclass=PoolMeta):
    __name__ = 'production.work.cycle'

    shift_record = fields.Many2One(
        'production.work.shift.record', 'Shift Record',
        states={
            'readonly': Eval('state').in_(['running', 'done', 'cancelled']),
            },
        depends=['state'])
