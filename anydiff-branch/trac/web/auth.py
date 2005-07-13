# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003, 2004, 2005 Edgewall Software
# Copyright (C) 2003, 2004, 2005 Jonas Borgstr�m <jonas@edgewall.com>
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

from __future__ import generators

import time

from trac import util
from trac.core import *
from trac.web.chrome import INavigationContributor


class Authenticator:
    """Implements user authentication based on HTTP authentication provided by
    the web-server, combined with cookies for communicating the login
    information across the whole site.
    
    Expects that the web-server is setup so that a request to the path '/login'
    requires authentication (such as Basic or Digest). The login name is then
    stored in the database and associated with a unique key that gets passed
    back to the user agent using the 'trac_auth' cookie. This cookie is used
    to identify the user in subsequent requests to non-protected resources.
    """

    def __init__(self, db, req, check_ip=True, ignore_case=False):
        self.db = db
        self.authname = 'anonymous'
        self.ignore_case = ignore_case

        if req.incookie.has_key('trac_auth'):
            cookie = req.incookie['trac_auth'].value
            cursor = db.cursor()
            if check_ip:
                cursor.execute("SELECT name FROM auth_cookie "
                               "WHERE cookie=%s AND ipnr=%s",
                               (cookie, req.remote_addr))
            else:
                cursor.execute("SELECT name FROM auth_cookie WHERE cookie=%s",
                               (cookie,))
            row = cursor.fetchone()
            if row:
                self.authname = row[0]
            else:
                # Tell the user to drop any auth_cookie for which no
                # corresponding entry in our cookie table exists.
                self.expire_auth_cookie(req)

    def login(self, req):
        """Log the remote user in.
        
        This function expects to be called when the remote user name is
        available. The user name is inserted into the `auth_cookie` table and a
        cookie identifying the user on subsequent requests is sent back to the
        client.
        
        If the Authenticator was created with `ignore_case` set to true, then 
        the authentication name passed from the web server in req.remote_user
        will be converted to lower case before being used. This is to avoid
        problems on installations authenticating against Windows which is not
        case sensitive regarding user names and domain names
        """
        assert req.remote_user, 'Authentication information not available.'
        
        remote_user = req.remote_user
        if self.ignore_case:
            remote_user = remote_user.lower()

        if self.authname == remote_user:
            # Already logged in with the same user name
            return
        assert self.authname == 'anonymous', \
               'Already logged in as %s.' % self.authname

        cookie = util.hex_entropy()
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO auth_cookie (cookie,name,ipnr,time) "
                       "VALUES (%s, %s, %s, %s)",
                       (cookie, remote_user, req.remote_addr, int(time.time())))
        self.db.commit()
        self.authname = remote_user
        req.outcookie['trac_auth'] = cookie
        req.outcookie['trac_auth']['path'] = util.quote_cookie_value(req.cgi_location)

    def logout(self, req):
        """Log the user out.
        
        Simply deletes the corresponding record from the auth_cookie table.
        """
        if self.authname == 'anonymous':
            # Not logged in
            return

        cursor = self.db.cursor()
        # While deleting this cookie we also take the opportunity to delete
        # cookies older than 10 days
        cursor.execute("DELETE FROM auth_cookie WHERE name=%s OR time < %s",
                       (self.authname, int(time.time()) - 86400 * 10))
        self.db.commit()
        self.expire_auth_cookie(req)

    def expire_auth_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past.
        """
        req.outcookie['trac_auth'] = ''
        req.outcookie['trac_auth']['path'] = util.quote_cookie_value(req.cgi_location)
        req.outcookie['trac_auth']['expires'] = -10000


class LoginModule(Component):

    implements(INavigationContributor)

    # INavigationContributor methods

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', 'logged in as %s' \
                  % util.escape(req.authname)
            yield 'metanav', 'logout', '<a href="%s">Logout</a>' \
                  % util.escape(self.env.href.logout())
        else:
            yield 'metanav', 'login', '<a href="%s">Login</a>' \
                  % util.escape(self.env.href.login())
