from datetime import timedelta
from odoo import _, api, fields, models
from odoo.odoo.exceptions import ValidationError, UserError
from odoo.fields import Command

from odoo.odoo.tools import date_utils


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one('res.partner', domain="[('state_approval','=', 'approvato')]")
    piano_rate_id = fields.Many2one('piano.rate', 'Piano Rate')

    invoice_count = fields.Integer(store=True,
                                   compute='_compute_invoice_count',
                                   string='Invoice count',
                                   help='Number of invoices generated')
    date_schedule = fields.Date()
    state = fields.Selection([
        ('draft', 'Da Validare'),
        ('revision', 'Da Revisionare'),
        ('sent', 'Da Confermare'),
        ('cancel', 'Annullato'),
        ('sale', 'Confermato'),
        ('sospeso', 'Sospeso'),
    ], tracking=True,
    )
    rinnovo_automatico = fields.Boolean('Rinnovo Automatico')
    piano_di_rinnovo = fields.Many2one('piano.rinnovo', 'Piano Rinnovo')
    motivazioni = fields.Many2one('motivazioni.sale', string='Motivazioni')

    appunti_welcome_call = fields.Text("Appunti Welcome Call")
    esito_welcome_call = fields.Selection([
        ('ok', 'OK'),
        ('irreperibile', 'Irreperibile'),
        ('ko', ' KO'),
    ],
    )
    deadline_recesso = fields.Date('Deadline recesso', compute="compute_deadline_recesso")

    @api.depends('line_ids.sale_line_ids')
    def _compute_origin_so_count(self):
        for move in self:
            move.sale_order_count = len(move.line_ids.sale_line_ids.order_id)

    @api.depends('date_order', 'state')
    def compute_deadline_recesso(self):
        self.deadline_recesso = self.date_order + timedelta(days=14)

    def action_revisiona(self):
        self.write({'state': 'revision'})
        return {
            'name': _('AGGIUNTA MOTIVAZIONE'),
            'view_mode': 'form',
            'res_model': 'motivazioni.sale.wizard',
            'view_id': self.env.ref('esercizio.motivazioni_sale_wizard_form_view_revisiona').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_annulla(self):
        self.write({'state': 'cancel'})
        return {
            'name': _('AGGIUNTA MOTIVAZIONE'),
            'view_mode': 'form',
            'res_model': 'motivazioni.sale.wizard',
            'view_id': self.env.ref('esercizio.motivazioni_sale_wizard_form_view_cancel').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_sospendi(self):
        self.write({'state': 'sospeso'})
        return {
            'name': _('AGGIUNTA MOTIVAZIONE'),
            'view_mode': 'form',
            'res_model': 'motivazioni.sale.wizard',
            'view_id': self.env.ref('esercizio.motivazioni_sale_wizard_form_view_sospendi').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.depends('state')
    def action_riattiva_ordine(self):
        if self.state != self._origin.state:
            self.state = self._origin.state

    # invio mail e passa allo stato confermato
    def action_invia(self):
        self.ensure_one()
        if self.esito_welcome_call == 'ko':
            raise UserError(_("LA WELCOME CALL DELL'ORDINE E' KO"))
        else:
            self.order_line._validate_analytic_distribution()

            lang = self.env.context.get('lang')
            mail_template = self._find_mail_template()
            if mail_template and mail_template.lang:
                lang = mail_template._render_lang(self.ids)[self.id]
            self.state = 'sale'
            ctx = {
                'default_model': 'sale.order',
                'default_res_ids': self.ids,
                'default_template_id': mail_template.id if mail_template else None,
                'default_composition_mode': 'comment',
                'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
                'proforma': self.env.context.get('proforma', False),
                'force_email': True,
                'model_description': self.with_context(lang=lang).type_name,
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

    def action_send_mail(self):
        super().action_send_mail()
        self.write({'state': 'sale'})

    def action_validate_sale(self):
        self.write({'state': 'sent'})
        return {
            'name': _('AGGIUNTA MOTIVAZIONE'),
            'view_mode': 'form',
            'res_model': 'motivazioni.sale.wizard',
            'view_id': self.env.ref('esercizio.motivazioni_sale_wizard_form_view_sent').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

        # validazione massiva

    def action_multi_validate_sale(self):
        count = set(self.mapped(('state')))
        count_total = len(count)
        if count_total > 1:
            raise ValidationError(_('I preventivi hanno stati diversi'))
        else:
            self.write({'state': 'sent'})

    # genera tanti po quanti fornitori diversi con i loro prodotti da approvvigionare
    def action_confirm(self):
        super().action_confirm()
        po = self.env['purchase.order']
        purchase = None
        account = None

        if not account:
            for line in self.order_line:
                for l in line.product_id.prodotti_da_approvvigionare_ids.filtered(lambda x: set(x.fornitore_id)):
                    for forn in l.fornitore_id:
                        po_vals = {
                            'partner_id': forn.id,
                            'origin': self.name
                        }
                    purchase = po.create(po_vals)
                    order_line = []
                    if purchase:
                        for line in self.order_line:
                            if line.product_id:
                                for l in line.product_id.prodotti_da_approvvigionare_ids:
                                    if l.fornitore_id:
                                        for forn in l.fornitore_id:
                                            if forn.id == purchase.partner_id.id:
                                                vals = {
                                                    'product_id': l.product_id.id,
                                                    'product_uom_qty': 1,
                                                    'price_unit': l.costo,
                                                }
                                                order_line.append((0, 0, vals))

                    if order_line:
                        purchase.sudo().update({'order_line': order_line})

    # smartbutton
    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    def action_view_invoice(self, invoices=False):
        if not invoices:
            invoices = self.mapped('invoice_ids')
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or
                                                   self.env['account.move'].default_get(
                                                       ['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.name,
            })
        action['context'] = context
        return action
