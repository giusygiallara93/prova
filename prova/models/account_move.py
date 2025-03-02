from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_count = fields.Integer(compute="_compute_origin_so_count", string='Sale Order Count')

    @api.depends('line_ids.sale_line_ids')
    def _compute_origin_so_count(self):
        for move in self:
            move.sale_order_count = len(move.line_ids.sale_line_ids.order_id)


    def action_view_source_sale_orders(self):
        self.ensure_one()
        source_orders = self.line_ids.sale_line_ids.order_id
        result = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        if len(source_orders) > 1:
            result['domain'] = [('id', 'in', source_orders.ids)]
        elif len(source_orders) == 1:
            result['views'] = [(self.env.ref('sale.view_order_form', False).id, 'form')]
            result['res_id'] = source_orders.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

