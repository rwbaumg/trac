# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgstr�m <jonas@edgewall.com>
# Copyright (C) 2004-2005 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Jonas Borgstr�m <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

from __future__ import generators
import time
import re

from trac import mimeview, util
from trac.core import *
from trac.Search import ISearchSource, query_to_sql, shorten_result
from trac.Timeline import ITimelineEventProvider
from trac.versioncontrol import Changeset, Node
from trac.versioncontrol.svn_authz import SubversionAuthorizer
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.wiki import wiki_to_html, wiki_to_oneliner, IWikiSyntaxProvider
from trac.versioncontrol.web_ui.diff import AbstractDiffModule

class ChangesetModule(AbstractDiffModule):

    implements(INavigationContributor, 
               ITimelineEventProvider, IWikiSyntaxProvider, ISearchSource)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'browser'

    def get_navigation_items(self, req):
        return []

    # (reimplemented) IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/changeset/([0-9]+)(/.*)?$', req.path_info)
        if match:
            req.args['rev'] = match.group(1)
            path = match.group(2)
            if path:
                req.args['path'] = path
            return 1

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('changeset', 'Repository checkins')

    def get_timeline_events(self, req, start, stop, filters):
        if 'changeset' in filters:
            format = req.args.get('format')
            show_files = int(self.config.get('timeline',
                                             'changeset_show_files'))
            db = self.env.get_db_cnx()
            repos = self.env.get_repository()
            authzperm = SubversionAuthorizer(self.env, req.authname)
            rev = repos.youngest_rev
            while rev:
                if not authzperm.has_permission_for_changeset(rev):
                    rev = repos.previous_rev(rev)
                    continue

                chgset = repos.get_changeset(rev)
                if chgset.date < start:
                    return
                if chgset.date < stop:
                    message = chgset.message or '--'
                    if format == 'rss':
                        title = 'Changeset <em>[%s]</em>: %s' \
                                % (util.escape(chgset.rev),
                                   util.escape(util.shorten_line(message)))
                        href = self.env.abs_href.changeset(chgset.rev)
                        message = wiki_to_html(message, self.env, db,
                                               absurls=True)
                    else:
                        title = 'Changeset <em>[%s]</em> by %s' \
                                % (util.escape(chgset.rev),
                                   util.escape(chgset.author))
                        href = self.env.href.changeset(chgset.rev)
                        message = wiki_to_oneliner(message, self.env, db,
                                                   shorten=True)
                    if show_files:
                        files = []
                        for chg in chgset.get_changes():
                            if show_files > 0 and len(files) >= show_files:
                                files.append('...')
                                break
                            files.append('<span class="%s">%s</span>'
                                         % (chg[2], util.escape(chg[0])))
                        message = '<span class="changes">' + ', '.join(files) +\
                                  '</span>: ' + message
                    yield 'changeset', href, title, chgset.date, chgset.author,\
                          message
                rev = repos.previous_rev(rev)


    # IWikiSyntaxProvider methods
    
    def get_wiki_syntax(self):
        yield (r"!?\[\d+(?:/[^\]]*)?\]|(?:\b|!)r\d+\b(?!:\d)",
               lambda x, y, z: self._format_link(x, 'changeset',
                                                 y[0] == 'r' and y[1:]
                                                 or y[1:-1], y, z))

    def get_link_resolvers(self):
        yield ('changeset', self._format_link)

    def _format_link(self, formatter, ns, chgset, label, fullmatch=None):
        sep = chgset.find('/')
        if sep > 0:
            rev, path = chgset[:sep], chgset[sep:]
        else:
            rev, path = chgset, None
        cursor = formatter.db.cursor()
        cursor.execute('SELECT message FROM revision WHERE rev=%s', (rev,))
        row = cursor.fetchone()
        if row:
            return '<a class="changeset" title="%s" href="%s">%s</a>' \
                   % (util.escape(util.shorten_line(row[0])),
                      formatter.href.changeset(rev, path), label)
        else:
            return '<a class="missing changeset" href="%s"' \
                   ' rel="nofollow">%s</a>' \
                   % (formatter.href.changeset(rev, path), label)

    # ISearchProvider methods

    def get_search_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('changeset', 'Changesets')

    def get_search_results(self, req, query, filters):
        if not 'changeset' in filters:
            return
        authzperm = SubversionAuthorizer(self.env, req.authname)
        db = self.env.get_db_cnx()
        sql = "SELECT rev,time,author,message " \
              "FROM revision WHERE %s" % \
              (query_to_sql(db, query, 'message||author'),)
        cursor = db.cursor()
        cursor.execute(sql)
        for rev, date, author, log in cursor:
            if not authzperm.has_permission_for_changeset(rev):
                continue
            yield (self.env.href.changeset(rev),
                   '[%s]: %s' % (rev, util.escape(util.shorten_line(log))),
                   date, author,
                   util.escape(shorten_result(log, query.split())))
