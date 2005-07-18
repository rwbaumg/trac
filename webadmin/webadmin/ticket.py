# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005 Edgewall Software
# Copyright (C) 2005 Jonas Borgstr�m <jonas@edgewall.com>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Jonas Borgstr�m <jonas@edgewall.com>

from trac import ticket, util
from trac.core import *
from trac.perm import IPermissionRequestor
from webadmin.web_ui import IAdminPageProvider


__all__ = []


class ComponentAdminPage(Component):

    implements(IAdminPageProvider)

    # IAdminPageProvider
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'components', 'Components')

    def process_admin_request(self, req, cat, page, component):
        req.perm.assert_permission('TICKET_ADMIN')
        
        # Detail view?
        if component:
            comp = ticket.Component(self.env, component)
            if req.method == 'POST':
                if req.args.get('save'):
                    comp.name = req.args.get('name')
                    comp.owner = req.args.get('owner')
                    comp.update()
                    req.redirect(self.env.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(self.env.href.admin(cat, page))

            req.hdf['admin.component'] = {
                'name': comp.name,
                'owner': comp.owner
            }
        else:
            if req.method == 'POST':
                # Add Component
                if req.args.get('add') and req.args.get('name'):
                    comp = ticket.Component(self.env)
                    comp.name = req.args.get('name')
                    if req.args.get('owner'):
                        comp.owner = req.args.get('owner')
                    comp.insert()
                    req.redirect(self.env.href.admin(cat, page))

                # Remove components
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No component selected'
                    db = self.env.get_db_cnx()
                    for name in sel:
                        comp = ticket.Component(self.env, name, db=db)
                        comp.delete(db=db)
                    db.commit()
                    req.redirect(self.env.href.admin(cat, page))

                # Set default component
                elif req.args.get('setdefault') and req.args.get('default'):
                    name = req.args.get('default')
                    self.log.info('Setting default component to %s', name)
                    self.config.set('ticket', 'default_component', name)
                    self.config.save()
                    req.redirect(self.env.href.admin(cat, page))

            default = self.config.get('ticket', 'default_component')
            req.hdf['admin.components'] = \
                [{'name': c.name, 'owner': c.owner,
                  'is_default': c.name == default,
                  'href': self.env.href.admin(cat, page, c.name)
                 } for c in ticket.Component.select(self.env)]
            

        restrict_owner = self.config.get('ticket', 'restrict_owner')
        if restrict_owner in util.TRUE:
            req.hdf['admin.owners'] = [username for username, name, email
                                       in self.env.get_known_users()]

        return 'admin_component.cs', None


class VersionsAdminPage(Component):

    implements(IAdminPageProvider)

    # IAdminPageProvider
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'versions', 'Versions')

    def process_admin_request(self, req, cat, page, version):
        req.perm.assert_permission('TICKET_ADMIN')
        
        # Detail view?
        if version:
            ver = ticket.Version(self.env, version)
            if req.method == 'POST':
                if req.args.get('save'):
                    ver.name = req.args.get('name')
                    # FIXME: parse the "time" field
                    ver.description = req.args.get('description')
                    ver.update()
                    req.redirect(self.env.href.admin(cat, page))
                elif req.args.get('remove'):
                    ver.delete()
                    req.redirect(self.env.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(self.env.href.admin(cat, page))

            req.hdf['admin.version'] = {
                'name': ver.name,
                'time': ver.time,
                'description': ver.description
            }
        else:
            if req.method == 'POST':
                # Add Version
                if req.args.get('add') and req.args.get('name'):
                    ver = ticket.Version(self.env)
                    ver.name = req.args.get('name')
                    ver.insert()
                    req.redirect(self.env.href.admin(cat, page))
                         
                # Remove versions
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No version selected'
                    db = self.env.get_db_cnx()
                    for name in sel:
                        ver = ticket.Version(self.env, name, db=db)
                        ver.delete(db=db)
                    db.commit()
                    req.redirect(self.env.href.admin(cat, page))

                # Set default version
                elif req.args.get('setdefault') and req.args.get('default'):
                    name = req.args.get('default')
                    self.log.info('Setting default version to %s', name)
                    self.config.set('ticket', 'default_version', name)
                    self.config.save()
                    req.redirect(self.env.href.admin(cat, page))

            default = self.config.get('ticket', 'default_version')
            req.hdf['admin.versions'] = \
                [{'name': c.name, 'time': c.time,
                  'is_default': c.name == default,
                  'href': self.env.href.admin(cat, page, c.name)
                 } for c in ticket.Version.select(self.env)]
            
        return 'admin_version.cs', None
