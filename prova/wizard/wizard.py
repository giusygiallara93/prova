from odoo import api, fields, models


class MotivazioniWizard(models.Model):
    _name = 'motivazioni.sale.wizard'

    note = fields.Text('Note')
    motivazione_id = fields.Many2one('motivazioni.sale')

    def confirm_motivazioni_revision(self):
        records = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        for rec in records:
            rec.write({'state': 'revision',
                       'motivazioni': self.motivazione_id.id,
                       })

    def confirm_motivazioni(self):
        records = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        for rec in records:
            rec.write({

                       'motivazioni': self.motivazione_id.id,
                       })
