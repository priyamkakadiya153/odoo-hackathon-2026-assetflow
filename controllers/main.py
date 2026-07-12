# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.http import request

class AssetFlowAuthSignupHome(AuthSignupHome):
    
    def do_signup(self, qcontext):
        # Prevent self-elevation of roles and force employee constraints
        qcontext['role'] = 'employee'
        qcontext['status'] = 'active'
        
        # If department was sent in context, ignore it for security 
        # (Admins or Dept Heads will assign departments later)
        if 'department_id' in qcontext:
            del qcontext['department_id']
            
        super(AssetFlowAuthSignupHome, self).do_signup(qcontext)

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        # Standard forgot password preparation hooks
        return super(AssetFlowAuthSignupHome, self).web_auth_reset_password(*args, **kw)
