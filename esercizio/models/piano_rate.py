from odoo import api,fields, models

class PianoRate(models.Model):
    _name= 'piano.rate'

    _description = "Piano Rate"

    intervallo = fields.Integer('Intervallo')
    periodi = fields.Selection([
        ('giorno', 'Giorno'),
        ('mese', 'Mese'),
        ('anno', 'Anno'),
    ]
    )
    name = fields.Char()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('piano.rate.sequence')
        return super().create(vals)
