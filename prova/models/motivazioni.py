from odoo import api, fields, models

class Motivazioni(models.Model):
    _name= 'motivazioni.sale'
    _description = "Motivazioni"

    name = fields.Char('Nome',required=True)
    state = fields.Selection([
        ('draft', 'Da Validare'),
        ('revision', 'Da Revisionare'),
        ('sent', 'Da Confermare'),
        ('cancel', 'Annullato'),
        ('sale', 'Confermato'),
        ('sospeso', 'Sospeso'),
    ], tracking=True,
    )

