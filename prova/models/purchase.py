from datetime import timedelta

from odoo import _, api, fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_count = fields.Integer(string="Sale Count",compute='compute_sale_count',default=0)

    def action_view_so(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        res['domain'] = [('name', '=', self.origin)]
        res['display_name'] = _("Sale History for %s", self.display_name)
        return res

    def compute_sale_count(self):
        for record in self:
            record.sale_count = self.env['sale.order'].search_count([('name', '=',self.origin)])
