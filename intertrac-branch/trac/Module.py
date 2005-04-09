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

import cgi
import re
import urllib


class Module:

    db = None
    env = None
    log = None
    perm = None

    _name = None

    def render(self, req):
        raise NotImplementedError


modules = {
#    name           (module_name,   class_name,         <module>: wiki syntax)
    'about'       : ('About',       'About',            0),
    'about_trac'  : ('About',       'About',            0),
    'attachment'  : ('attachment',  'AttachmentModule', 0),
    'browser'     : ('Browser',     'BrowserModule',    1),
    'source'      : ('Browser',     'BrowserModule',    1),
    'repos'       : ('Browser',     'BrowserModule',    1),
    'changeset'   : ('Changeset',   'ChangesetModule',  1),
    'file'        : ('Browser',     'FileModule',       0),
    'log'         : ('Browser',     'LogModule',        0),
    'milestone'   : ('Milestone',   'Milestone',        1),
    'newticket'   : ('Ticket',      'NewticketModule',  0),
    'query'       : ('Query',       'QueryModule',      1),
    'report'      : ('Report',      'Report',           1),
    'roadmap'     : ('Roadmap',     'Roadmap',          0),
    'search'      : ('Search',      'Search',           1),
    'settings'    : ('Settings',    'Settings',         0),
    'ticket'      : ('Ticket',      'TicketModule',     1),
    'timeline'    : ('Timeline',    'Timeline',         0),
    'wiki'        : ('Wiki',        'WikiModule',       1),
}

def module_factory(mode):
    module_name, constructor_name, has_wiki_syntax = modules[mode]
    module = __import__(module_name, globals(),  locals())
    constructor = getattr(module, constructor_name)
    module = constructor()
    module._name = mode
    return module

def parse_path_info(args, path_info):
    def set_if_missing(fs, name, value):
        if value and not fs.has_key(name):
            fs.list.append(cgi.MiniFieldStorage(name, value))

    match = re.search(r'^/(about(?:_trac)?|wiki)(?:/(.*))?', path_info)
    if match:
        set_if_missing(args, 'mode', match.group(1))
        if match.group(2):
            set_if_missing(args, 'page', match.group(2))
        return
    match = re.search(r'^/(newticket|timeline|search|roadmap|settings|query)/?', path_info)
    if match:
        set_if_missing(args, 'mode', match.group(1))
        return
    match = re.search(r'^/(ticket|report)(?:/([0-9]+)/*)?', path_info)
    if match:
        set_if_missing(args, 'mode', match.group(1))
        if match.group(2):
            set_if_missing(args, 'id', match.group(2))
        return
    match = re.search(r'^/(browser|source|repos|log|file)(?:(/.*))?', path_info)
    if match:
        set_if_missing(args, 'mode', match.group(1))
        if match.group(2):
            set_if_missing(args, 'path', match.group(2))
        return
    match = re.search(r'^/changeset/([0-9]+)/?', path_info)
    if match:
        set_if_missing(args, 'mode', 'changeset')
        set_if_missing(args, 'rev', match.group(1))
        return
    match = re.search(r'^/attachment/(ticket|wiki)(?:/(.*))?', path_info)
    if match:
        set_if_missing(args, 'mode', 'attachment')
        set_if_missing(args, 'type', match.group(1))
        set_if_missing(args, 'path', match.group(2))
        return
    match = re.search(r'^/milestone(?:/([^\?]+))?(?:/(.*)/?)?', path_info)
    if match:
        set_if_missing(args, 'mode', 'milestone')
        if match.group(1):
            set_if_missing(args, 'id', urllib.unquote(match.group(1)))
        return
