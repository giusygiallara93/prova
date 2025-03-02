from odoo import api, fields, models
from odoo.tools import date_utils
from odoo.fields import Command


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # genera tante ft quante richieste nel intervallo
    def create_invoice_from_order(self):
        start_date = self.date_order
        self.ensure_one()
        for i in range(0, self.piano_rate_id.intervallo):
            if self.piano_rate_id.periodi == 'giorno':
                next_schedule = date_utils.add(start_date,
                                               days=int(i))
                data_due = next_schedule
            elif self.piano_rate_id.periodi == 'mese':
                next_schedule = date_utils.add(start_date,
                                               months=int(i))
                data_due = next_schedule
            else:
                next_schedule = date_utils.add(start_date,
                                               years=int(i))
                data_due = next_schedule

            self.env['account.move'].create(
                {'move_type': 'out_invoice',
                 'partner_id': self.partner_id.id,
                 'invoice_date': fields.date.today(),
                 'invoice_date_due': data_due,
                 'ref': self.name,

                 'invoice_line_ids': [(0, 0, {
                     'product_id': line.product_id.id,
                     'name': line.product_id.name,
                     'quantity': line.product_uom_qty,
                     'price_unit': round(line.price_unit / self.piano_rate_id.intervallo, 2),
                     'discount': line.discount,
                     'tax_ids': [Command.set(line.tax_id.ids)],
                     'sale_line_ids': [Command.link(self.id)],
                 }) for line in self.order_line]

                 })
            self.invoice_count = self.env['account.move'].search_count([
                ('line_ids.sale_line_ids.order_id', '=', self.id)])
