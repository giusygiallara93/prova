from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prodotti_da_approvvigionare_ids = fields.One2many('prodotti.approvvigionare', 'product_id',string='Prodotti')

