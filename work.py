# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta


class WorkCycle(metaclass=PoolMeta):
    __name__ = 'production.work.cycle'

    shift = fields.Many2One('working.shift.definition', 'Shift')
