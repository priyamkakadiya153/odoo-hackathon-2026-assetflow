# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetFlowBooking(models.Model):
    _name = 'assetflow.booking'
    _description = 'Resource Booking'
    _order = 'date_start desc'

    resource_id = fields.Many2one('assetflow.asset', string='Resource', required=True, index=True, domain="[('is_bookable', '=', True)]")
    employee_id = fields.Many2one('res.users', string='Employee', required=True, index=True, domain="[('share', '=', False)]")
    department_id = fields.Many2one('assetflow.department', string='Department')
    
    date_start = fields.Datetime(string='Booking Start Date & Time', required=True, index=True)
    date_end = fields.Datetime(string='Booking End Date & Time', required=True, index=True)
    purpose = fields.Text(string='Purpose')
    
    status = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='upcoming', required=True, index=True)

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id

    @api.constrains('resource_id', 'date_start', 'date_end', 'status')
    def _check_booking_overlap(self):
        for rec in self:
            if rec.status == 'cancelled':
                continue
            if not rec.date_start or not rec.date_end:
                continue
            if rec.date_start >= rec.date_end:
                raise ValidationError(_("The booking start time must be earlier than the end time."))
            
            # Search for overlapping bookings on the same resource
            overlapping = self.search([
                ('id', '!=', rec.id),
                ('resource_id', '=', rec.resource_id.id),
                ('status', '!=', 'cancelled'),
                ('date_start', '<', rec.date_end),
                ('date_end', '>', rec.date_start)
            ])
            if overlapping:
                conflict = overlapping[0]
                raise ValidationError(_(
                    "The resource '%s' is already booked for this period. "
                    "Conflicting booking: %s to %s."
                ) % (rec.resource_id.name, conflict.date_start, conflict.date_end))

    def action_start(self):
        for rec in self:
            if rec.status != 'upcoming':
                raise ValidationError(_("Only upcoming bookings can be started."))
            rec.write({'status': 'ongoing'})
        return True

    def action_complete(self):
        for rec in self:
            if rec.status != 'ongoing':
                raise ValidationError(_("Only ongoing bookings can be completed."))
            rec.write({'status': 'completed'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.status in ('completed', 'cancelled'):
                raise ValidationError(_("Completed or already cancelled bookings cannot be cancelled."))
            rec.write({'status': 'cancelled'})
        return True
