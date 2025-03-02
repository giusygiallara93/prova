from odoo import _, api, fields, models
from odoo.odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ("vat_unique", "UNIQUE(vat)", "VAT must be unique!")]
    _sql_constraints = [("l10n_it_codice_fiscale_unique", "UNIQUE(l10n_it_codice_fiscale)", "CF must be unique!")]

    referente_interno = fields.Boolean(default=False)
    rappresentante_legale = fields.Boolean(default=False)
    data_nascita = fields.Date(string="Data di nascita")
    luogo_di_nascita = fields.Text(string="Luogo di Nascita")
    tipo_di_documento = fields.Selection(
        [
            ("carta_identita", "Carta d'Identità"),
            ("patente", "Patente"),
            ("passaporto", "Passaporto"),
        ],
    )
    num_documento = fields.Text(string="Numero documento")
    scadenza_documento = fields.Date(string="Scadenza documento")
    data_emissione_documento = fields.Date(string="Data emissione documento")
    categoria_merceologica = fields.Selection([
        ('01.13.3', "Coltivazione di barbabietola da zucchero"),
        ('01.13.4', 'Coltivazione di patate'), ]
    )
    same_cf_partner_id = fields.Many2one('res.partner', string='Partner with same Fiscal Code',
                                         compute='_compute_same_cf_partner_id', store=False)

    progressivo_cliente = fields.Char(string='ID')
    state_approval = fields.Selection([('da_approvare', 'Da Approvare'),
                              ('approvato', 'Approvato'), ], default='da_approvare')

    referente_interno_id = fields.Many2one('res.partner',)
    rappresentante_legale_id = fields.Many2one('res.partner')

    @api.depends('referente_interno', 'rappresentante_legale')
    def action_approvato(self):
        if self.company_type == 'company':
            if not self.referente_interno_id or not self.rappresentante_legale_id:
                raise ValidationError(_('non è presente il rappresentante legale e il referente interno'))

            else:
                return self.write({'state_approval': 'approvato'})
        else:
            return self.write({'state_approval': 'approvato'})

    @api.depends('referente_interno', 'rappresentante_legale')
    def action_da_approvare(self):
        return self.write({'state_approval': 'da_approvare'})


    @api.depends('l10n_it_codice_fiscale', 'company_id', 'company_registry')
    def _compute_same_cf_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            Partner = self.with_context(active_test=False).sudo()
            domain = [
                ('l10n_it_codice_fiscale', '=', partner.l10n_it_codice_fiscale),
            ]
            if partner.company_id:
                domain += [('company_id', 'in', [False, partner.company_id.id])]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            should_check_cf = partner.l10n_it_codice_fiscale and len(partner.l10n_it_codice_fiscale) != 1
            partner.same_cf_partner_id = should_check_cf and not partner.parent_id and Partner.search(domain, limit=1)
            # check company_registry
            domain = [
                ('company_registry', '=', partner.company_registry),
                ('company_id', 'in', [False, partner.company_id.id]),
            ]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            partner.same_company_registry_partner_id = bool(
                partner.company_registry) and not partner.parent_id and Partner.search(domain, limit=1)

    @api.model
    def create(self, vals):
        vals['progressivo_cliente'] = self.env['ir.sequence'].next_by_code('res.partner.sequence')
        return super().create(vals)
