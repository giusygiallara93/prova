from odoo import api, fields, models


class ProdottiApprovvigionare(models.Model):
    _name = 'prodotti.approvvigionare'

    _description = "Prodotti da approvvigionare"

    product_id = fields.Many2one('product.product', 'Product')
    fornitore_id = fields.Many2one('res.partner', 'Fornitore')
    costo = fields.Float()
    sale_id = fields.Many2one('sale.order')
