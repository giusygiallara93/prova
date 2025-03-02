from odoo import api, fields, models

class PianoRinnovo(models.Model):
    _name= 'piano.rinnovo'

    _description = "Piano Rinnovo"

    name = fields.Char()
    numero = fields.Integer('Numero')
    periodi = fields.Selection([
        ('giorno', 'Giorni'),
        ('mese', 'Mese'),
        ('anno', 'Anno'),
    ]
    )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('piano.rinnovo.sequence')
        return super().create(vals)
