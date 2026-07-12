# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError

class AssetFlowMaintenance(models.Model):
    _name = 'assetflow.maintenance'
    _description = 'Maintenance Request'
    _order = 'request_date desc'

    name = fields.Char(string='Maintenance Request Number', required=True, copy=False, index=True, default='/')
    asset_id = fields.Many2one('assetflow.asset', string='Asset', required=True, index=True)
    raised_by_id = fields.Many2one('res.users', string='Raised By', required=True, default=lambda self: self.env.user)
    technician_id = fields.Many2one('res.users', string='Assigned Technician', domain="[('share', '=', False)]")
    
    description = fields.Text(string='Description', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Priority', default='low', required=True, index=True)
    
    photo = fields.Binary(string='Photo Attachment')
    request_date = fields.Date(string='Request Date', required=True, default=fields.Date.context_today)
    approval_date = fields.Date(string='Approval Date')
    resolution_date = fields.Date(string='Resolution Date')
    resolution_notes = fields.Text(string='Resolution Notes')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('assigned', 'Technician Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True, index=True)

    @api.constrains('asset_id', 'status')
    def _check_active_request(self):
        for rec in self:
            if rec.status in ('pending', 'approved', 'assigned', 'in_progress'):
                duplicates = self.search([
                    ('id', '!=', rec.id),
                    ('asset_id', '=', rec.asset_id.id),
                    ('status', 'in', ('pending', 'approved', 'assigned', 'in_progress'))
                ])
                if duplicates:
                    raise ValidationError(_(
                        "An active maintenance request is already in progress for asset '%s'."
                    ) % rec.asset_id.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                seq = self.env['ir.sequence'].next_by_code('assetflow.maintenance')
                if not seq:
                    count = self.search_count([]) + 1
                    seq = 'MR-%s' % str(count).zfill(4)
                vals['name'] = seq
        return super(AssetFlowMaintenance, self).create(vals_list)

    def _check_manager_permission(self):
        if not self.env.user.has_group('assetflow.group_asset_manager'):
            raise AccessError(_("Only Asset Managers are authorized to perform this operation."))

    def action_approve(self):
        self._check_manager_permission()
        for rec in self:
            if rec.status != 'pending':
                raise ValidationError(_("Only pending requests can be approved."))
            rec.write({
                'status': 'approved',
                'approval_date': fields.Date.context_today(self)
            })
            rec.asset_id.write({'status': 'maintenance'})
        return True

    def action_reject(self):
        self._check_manager_permission()
        for rec in self:
            if rec.status != 'pending':
                raise ValidationError(_("Only pending requests can be rejected."))
            rec.write({'status': 'rejected'})
        return True

    def action_assign_technician(self):
        for rec in self:
            if rec.status != 'approved':
                raise ValidationError(_("Technicians can only be assigned to approved requests."))
            if not rec.technician_id:
                raise ValidationError(_("Please select a technician first."))
            rec.write({
                'status': 'assigned'
            })
        return True

    def action_start_work(self):
        for rec in self:
            if rec.status != 'assigned':
                raise ValidationError(_("Work can only start once a technician has been assigned."))
            rec.write({'status': 'in_progress'})
        return True

    def action_resolve(self, resolution_notes=False):
        for rec in self:
            if rec.status != 'in_progress':
                raise ValidationError(_("Only requests currently 'In Progress' can be marked as resolved."))
            rec.write({
                'status': 'resolved',
                'resolution_date': fields.Date.context_today(self),
                'resolution_notes': resolution_notes
            })
            rec.asset_id.write({'status': 'available'})
        return True
