# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003, 2004, 2005 Edgewall Software
# Copyright (C) 2003, 2004, 2005 Jonas Borgstr�m <jonas@edgewall.com>
# Copyright (C) 2004, 2005 Christopher Lenz <cmlenz@gmx.de>
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
#         Christopher Lenz <cmlenz@gmx.de>

from __future__ import generators
import re
import os
import imp
import string
import StringIO
import urllib

from trac import util
from trac.core import *
from trac.mimeview import *
from trac.wiki.api import WikiSystem, IWikiChangeListener

__all__ = ['wiki_to_html', 'wiki_to_oneliner', 'wiki_to_outline']


def system_message(msg, text):
    return """<div class="system-message">
 <strong>%s</strong>
 <pre>%s</pre>
</div>
""" % (msg, util.escape(text))


class WikiProcessor(object):

    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.error = None

        builtin_processors = {'html': self._html_processor,
                              'default': self._default_processor,
                              'comment': self._comment_processor}
        self.processor = builtin_processors.get(name)
        if not self.processor:
            # Find a matching wiki macro
            from trac.wiki import WikiSystem
            wiki = WikiSystem(env)
            for macro_provider in wiki.macro_providers:
                if self.name in list(macro_provider.get_macros()):
                    self.processor = self._macro_processor
                    break
        if not self.processor:
            # Find a matching mimeview renderer
            from trac.mimeview.api import MIME_MAP
            if self.name in MIME_MAP.keys():
                self.name = MIME_MAP[self.name]
                self.processor = self._mimeview_processor
            elif self.name in MIME_MAP.values():
                self.processor = self._mimeview_processor
            else:
                self.processor = self._default_processor
                self.error = 'No macro named [[%s]] found' % name

    def _comment_processor(self, req, text, env):
        return ''

    def _default_processor(self, req, text, env):
        return '<pre class="wiki">' + util.escape(text) + '</pre>\n'

    def _html_processor(self, req, text, env):
        if Formatter._htmlproc_disallow_rule.search(text):
            err = system_message('Error: HTML block contains disallowed tags.',
                                 text)
            env.log.error(err)
            return err
        if Formatter._htmlproc_disallow_attribute.search(text):
            err = system_message('Error: HTML block contains disallowed attributes.',
                                 text)
            env.log.error(err)
            return err
        return text

    def _macro_processor(self, req, text, env):
        from trac.wiki import WikiSystem
        wiki = WikiSystem(env)
        for macro_provider in wiki.macro_providers:
            if self.name in list(macro_provider.get_macros()):
                env.log.debug('Executing Wiki macro %s by provider %s'
                              % (self.name, macro_provider))
                return macro_provider.render_macro(req, self.name, text)

    def _mimeview_processor(self, req, text, env):
        return Mimeview(env).render(req, self.name, text)

    def process(self, req, text, inline=False):
        if self.error:
            return system_message('Error: Failed to load processor <code>%s</code>'
                                  % self.name, self.error)
        text = self.processor(req, text, self.env)
        if inline:
            code_block_start = re.compile('^<div class="code-block">')
            code_block_end = re.compile('</div>$')
            text, nr = code_block_start.subn('<span class="code-block">', text, 1 )
            if nr:
                text, nr = code_block_end.subn('</span>', text, 1 )
            return text
        else:
            return text


class Formatter(object):
    flavor = 'default'

    # Rules provided by IWikiSyntaxProviders are inserted between pre_rules and post_rules
    _pre_rules = [r"(?P<bolditalic>''''')",
                  r"(?P<bold>''')",
                  r"(?P<italic>'')",
                  r"(?P<underline>__)",
                  r"(?P<strike>~~)",
                  r"(?P<subscript>,,)",
                  r"(?P<superscript>\^)",
                  r"(?P<inlinecode>!?\{\{\{(?P<inline>.*?)\}\}\})",
                  r"(?P<htmlescapeentity>!?&#\d+;)"]
    _post_rules = [r"(?P<shref>!?((?P<sns>\w+):(?P<stgt>(&#34;(.*?)&#34;|'(.*?)')|(([^ ][^ |]+)*[^|'~_\., \)]))))",
                   r"(?P<lhref>!?\[(?P<lns>\w+):(?P<ltgt>[^ ]+) (?P<label>.*?)\])",
                   r"(?P<macro>!?\[\[(?P<macroname>[\w/+-]+)(\]\]|\((?P<macroargs>.*?)\)\]\]))",
                   r"(?P<heading>^\s*(?P<hdepth>=+)\s.*\s(?P=hdepth)\s*$)",
                   r"(?P<list>^(?P<ldepth>\s+)(?:\*|\d+\.) )",
                   r"(?P<definition>^\s+(.+)::)\s*",
                   r"(?P<indent>^(?P<idepth>\s+)(?=\S))",
                   r"(?P<last_table_cell>\|\|$)",
                   r"(?P<table_cell>\|\|)"]

    _processor_re = re.compile('#\!([\w+-][\w+-/]*)')
    _anchor_re = re.compile('[^\w\d\.-:]+', re.UNICODE)
    
    img_re = re.compile(r"\.(gif|jpg|jpeg|png)(\?.*)?$", re.IGNORECASE)
    _htmlproc_disallow_rule = re.compile('(?i)<(script|noscript|embed|object|'
                                         'iframe|frame|frameset|link|style|'
                                         'meta|param|doctype)')
    _htmlproc_disallow_attribute = re.compile('(?i)<[^>]*\s+(on\w+)=')


    def __init__(self, env, req=None, absurls=0, db=None):
        self.env = env
        self.req = req
        self._db = db
        self._absurls = absurls
        self._anchors = []
        self._open_tags = []
        self.href = absurls and env.abs_href or env.href
        self._local = env.config.get('project', 'url', '') or env.abs_href.base

    def _get_db(self):
        if not self._db:
            self._db = self.env.get_db_cnx()
        return self._db
    db = property(fget=_get_db)

    def _get_rules(self):
        return WikiSystem(self.env).rules
    rules = property(_get_rules)

    def _get_link_resolvers(self):
        return WikiSystem(self.env).link_resolvers
    link_resolvers = property(_get_link_resolvers)

    def replace(self, fullmatch):
        wiki = WikiSystem(self.env)        
        for itype, match in fullmatch.groupdict().items():
            if match and not itype in wiki.helper_patterns:
                # Check for preceding escape character '!'
                if match[0] == '!':
                    return match[1:]
                if itype in wiki.external_handlers:
                    return wiki.external_handlers[itype](self, match, fullmatch)
                else:
                    return getattr(self, '_' + itype + '_formatter')(match, fullmatch)

    def tag_open_p(self, tag):
        """Do we currently have any open tag with @tag as end-tag"""
        return tag in self._open_tags

    def close_tag(self, tag):
        tmp =  ''
        for i in xrange(len(self._open_tags)-1, -1, -1):
            tmp += self._open_tags[i][1]
            if self._open_tags[i][1] == tag:
                del self._open_tags[i]
                for j in xrange(i, len(self._open_tags)):
                    tmp += self._open_tags[j][0]
                break
        return tmp
        
    def open_tag(self, open, close):
        self._open_tags.append((open, close))

    def simple_tag_handler(self, open_tag, close_tag):
        """Generic handler for simple binary style tags"""
        if self.tag_open_p((open_tag, close_tag)):
            return self.close_tag(close_tag)
        else:
            self.open_tag(open_tag, close_tag)
        return open_tag

    def _bolditalic_formatter(self, match, fullmatch):
        italic = ('<i>', '</i>')
        italic_open = self.tag_open_p(italic)
        tmp = ''
        if italic_open:
            tmp += italic[1]
            self.close_tag(italic[1])
        tmp += self._bold_formatter(match, fullmatch)
        if not italic_open:
            tmp += italic[0]
            self.open_tag(*italic)
        return tmp

    def _shref_formatter(self, match, fullmatch):
        ns = fullmatch.group('sns')
        target = fullmatch.group('stgt')
        return self._make_link(ns, target, match, match)

    def _lhref_formatter(self, match, fullmatch):
        ns = fullmatch.group('lns')
        target = fullmatch.group('ltgt') 
        label = fullmatch.group('label')
        return self._make_link(ns, target, match, label)

    def _make_link(self, ns, target, match, label):
        # check first for an alias defined in trac.ini
        ns = self.env.config.get('intertrac', ns.upper(), ns)
        if ns in self.link_resolvers:
            return self.link_resolvers[ns](self, ns, target, label)
        elif target[:2] == '//' or ns == "mailto":
            return self._make_ext_link(ns+':'+target, label)
        elif self.env.siblings.has_key(ns):
            ref = wiki_to_oneliner(target, self.env.siblings[ns])
            return ref.replace('>%s' % target, '>%s' % label)
        else:
            intertrac = self._make_intertrac_link(ns, target, label)
            if intertrac:
                return intertrac
            else:
                interwiki = self._make_interwiki_link(ns, target, label)
                if interwiki:
                    return interwiki
                else:
                    return match

    def _make_intertrac_link(self, ns, target, label):
        url = self.env.config.get('intertrac', ns.upper()+'.url')
        if url:
            name = self.env.config.get('intertrac', ns.upper()+'.title',
                                       'Trac project %s' % ns)
            sep = target.find(':')
            if sep != -1:
                url = '%s/%s/%s' % (url, target[:sep], target[sep+1:])
            else: 
                url = '%s/search?q=%s' % (url, urllib.quote_plus(target))
            return self._make_ext_link(url, label, '%s in %s' % (target, name))
        else:
            return None

    def intertrac_helper(self, ns, target, label, fullmatch):
        if fullmatch: # short form
            alias = fullmatch.group('it_%s' % ns)
            if alias:
                intertrac = self.env.config.get('intertrac', alias.upper(), alias)
                target = '%s:%s' % (ns, target[len(alias):])
                it = self._make_intertrac_link(intertrac, target, label)
                return it or label
        return None

    def _make_interwiki_link(self, ns, target, label):
        interwiki = InterWikiMap(self.env)
        if interwiki.has_key(ns):
            return self._make_ext_link(interwiki.url(ns, target), label,
                                       '%s in %s' % (target, ns))
        else:
            return None

    def _make_ext_link(self, url, text, title=''):
        title_attr = title and ' title="%s"' % title or ''
        if Formatter.img_re.search(url) and self.flavor != 'oneliner':
            return '<img src="%s" alt="%s"%s />' % (url, title or text)
        if not url.startswith(self._local):
            return '<a class="ext-link" href="%s"%s>%s</a>' \
                   % (url, title_attr, text)
        else:
            return '<a href="%s"%s>%s</a>' % (url, title_attr, text)

    def _bold_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<strong>', '</strong>')

    def _italic_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<i>', '</i>')

    def _underline_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<span class="underline">', '</span>')

    def _strike_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<del>', '</del>')

    def _subscript_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<sub>', '</sub>')

    def _superscript_formatter(self, match, fullmatch):
        return self.simple_tag_handler('<sup>', '</sup>')

    def _inlinecode_formatter(self, match, fullmatch):
        return '<tt>%s</tt>' % fullmatch.group('inline')

    def _htmlescapeentity_formatter(self, match, fullmatch):
        #dummy function that match html escape entities in the format:
        # &#[0-9]+;
        # This function is used to avoid these being matched by
        # the tickethref regexp
        return match

    def _macro_formatter(self, match, fullmatch):
        name = fullmatch.group('macroname')
        if name in ['br', 'BR']:
            return '<br />'
        args = fullmatch.group('macroargs')
        args = util.unescape(args)
        try:
            macro = WikiProcessor(self.env, name)
            return macro.process(self.req, args, 1)
        except Exception, e:
            return system_message('Error: Macro %s(%s) failed' % (name, args), e)

    def _heading_formatter(self, match, fullmatch):
        match = match.strip()
        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        self.close_list()
        self.close_def_list()

        depth = min(len(fullmatch.group('hdepth')), 5)
        heading = match[depth + 1:len(match) - depth - 1]
        anchor = anchor_base = self._anchor_re.sub('', heading.decode('utf-8'))
        if not anchor or not anchor[0].isalpha():
            # an ID must start with a letter in HTML
            anchor = 'a' + anchor
        i = 1
        while anchor in self._anchors:
            anchor = anchor_base + str(i)
            i += 1
        self._anchors.append(anchor)
        self.out.write('<h%d id="%s">%s</h%d>' % (depth, anchor.encode('utf-8'),
                                                  wiki_to_oneliner(heading,
                                                      self.env, self._db,
                                                      self._absurls),
                                                  depth))

    def _indent_formatter(self, match, fullmatch):
        depth = int((len(fullmatch.group('idepth')) + 1) / 2)
        list_depth = len(self._list_stack)
        if list_depth > 0 and depth == list_depth + 1:
            self.in_list_item = 1
        else:
            self.open_indentation(depth)
        return ''

    def _last_table_cell_formatter(self, match, fullmatch):
        return ''

    def _table_cell_formatter(self, match, fullmatch):
        self.open_table()
        self.open_table_row()
        if self.in_table_cell:
            return '</td><td>'
        else:
            self.in_table_cell = 1
            return '<td>'

    def close_indentation(self):
        self.out.write(('</blockquote>' + os.linesep) * self.indent_level)
        self.indent_level = 0

    def open_indentation(self, depth):
        if self.in_def_list:
            return
        diff = depth - self.indent_level
        if diff != 0:
            self.close_paragraph()
            self.close_indentation()
            self.close_list()
            self.indent_level = depth
            self.out.write(('<blockquote>' + os.linesep) * depth)

    def _list_formatter(self, match, fullmatch):
        ldepth = len(fullmatch.group('ldepth'))
        depth = int((len(fullmatch.group('ldepth')) + 1) / 2)
        self.in_list_item = depth > 0
        type_ = ['ol', 'ul'][match[ldepth] == '*']
        self._set_list_depth(depth, type_)
        return ''

    def _definition_formatter(self, match, fullmatch):
        tmp = self.in_def_list and '</dd>' or '<dl>'
        tmp += '<dt>%s</dt><dd>' % wiki_to_oneliner(match[:-2], self.env,
                                                    self.db)
        self.in_def_list = True
        return tmp

    def close_def_list(self):
        if self.in_def_list:
            self.out.write('</dd></dl>\n')
        self.in_def_list = False

    def _set_list_depth(self, depth, type_):
        current_depth = len(self._list_stack)
        diff = depth - current_depth
        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        if diff > 0:
            for i in range(diff):
                self._list_stack.append(type_)
                self.out.write('<%s><li>' % type_)
        elif diff < 0:
            for i in range(-diff):
                tmp = self._list_stack.pop()
                self.out.write('</li></%s>' % tmp)
            if self._list_stack != [] and type_ != self._list_stack[-1]:
                tmp = self._list_stack.pop()
                self._list_stack.append(type_)
                self.out.write('</li></%s><%s><li>' % (tmp, type_))
            if depth > 0:
                self.out.write('</li><li>')
        # diff == 0
        elif self._list_stack != [] and type_ != self._list_stack[-1]:
            tmp = self._list_stack.pop()
            self._list_stack.append(type_)
            self.out.write('</li></%s><%s><li>' % (tmp, type_))
        elif depth > 0:
            self.out.write('</li><li>')

    def close_list(self):
        if self._list_stack != []:
            self._set_list_depth(0, None)

    def open_paragraph(self):
        if not self.paragraph_open:
            self.out.write('<p>' + os.linesep)
            self.paragraph_open = 1

    def close_paragraph(self):
        if self.paragraph_open:
            while self._open_tags != []:
                self.out.write(self._open_tags.pop()[1])
            self.out.write('</p>' + os.linesep)
            self.paragraph_open = 0

    def open_table(self):
        if not self.in_table:
            self.close_paragraph()
            self.close_indentation()
            self.close_list()
            self.close_def_list()
            self.in_table = 1
            self.out.write('<table class="wiki">' + os.linesep)

    def open_table_row(self):
        if not self.in_table_row:
            self.open_table()
            self.in_table_row = 1
            self.out.write('<tr>')

    def close_table_row(self):
        if self.in_table_row:
            self.in_table_row = 0
            if self.in_table_cell:
                self.in_table_cell = 0
                self.out.write('</td>')

            self.out.write('</tr>')

    def close_table(self):
        if self.in_table:
            self.close_table_row()
            self.out.write('</table>' + os.linesep)
            self.in_table = 0

    def handle_code_block(self, line):
        if line.strip() == '{{{':
            self.in_code_block += 1
            if self.in_code_block == 1:
                self.code_processor = None
                self.code_text = ''
            else:
                self.code_text += line + os.linesep
                if not self.code_processor:
                    self.code_processor = WikiProcessor(self.env, 'default')
        elif line.strip() == '}}}':
            self.in_code_block -= 1
            if self.in_code_block == 0 and self.code_processor:
                self.close_paragraph()
                self.close_table()
                self.out.write(self.code_processor.process(self.req, self.code_text))
            else:
                self.code_text += line + os.linesep
        elif not self.code_processor:
            match = Formatter._processor_re.search(line)
            if match:
                name = match.group(1)
                self.code_processor = WikiProcessor(self.env, name)
            else:
                self.code_text += line + os.linesep 
                self.code_processor = WikiProcessor(self.env, 'default')
        else:
            self.code_text += line + os.linesep

    def format(self, text, out, escape_newlines=False):
        self.out = out
        self._open_tags = []
        self._list_stack = []

        self.in_code_block = 0
        self.in_table = 0
        self.in_def_list = 0
        self.in_table_row = 0
        self.in_table_cell = 0
        self.indent_level = 0
        self.paragraph_open = 0

        for line in text.splitlines():
            # Handle code block
            if self.in_code_block or line.strip() == '{{{':
                self.handle_code_block(line)
                continue
            # Handle Horizontal ruler
            elif line[0:4] == '----':
                self.close_paragraph()
                self.close_indentation()
                self.close_list()
                self.close_def_list()
                self.close_table()
                self.out.write('<hr />' + os.linesep)
                continue
            # Handle new paragraph
            elif line == '':
                self.close_paragraph()
                self.close_indentation()
                self.close_list()
                self.close_def_list()
                continue

            line = util.escape(line)
            if escape_newlines:
                line += ' [[BR]]'
            self.in_list_item = False
            # Throw a bunch of regexps on the problem
            result = re.sub(self.rules, self.replace, line)

            if not self.in_list_item:
                self.close_list()

            if self.in_def_list and not line.startswith(' '):
                self.close_def_list()

            if self.in_table and line[0:2] != '||':
                self.close_table()

            if len(result) and not self.in_list_item and not self.in_def_list \
                    and not self.in_table:
                self.open_paragraph()
            out.write(result + os.linesep)
            self.close_table_row()

        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        self.close_list()
        self.close_def_list()


class OneLinerFormatter(Formatter):
    """
    A special version of the wiki formatter that only implement a
    subset of the wiki formatting functions. This version is useful
    for rendering short wiki-formatted messages on a single line
    """
    flavor = 'oneliner'

    # Override a few formatters to disable some wiki syntax in "oneliner"-mode
    def _list_formatter(self, match, fullmatch): return match
    def _macro_formatter(self, match, fullmatch): return match
    def _indent_formatter(self, match, fullmatch): return match
    def _heading_formatter(self, match, fullmatch): return match
    def _definition_formatter(self, match, fullmatch): return match
    def _table_cell_formatter(self, match, fullmatch): return match
    def _last_table_cell_formatter(self, match, fullmatch): return match

    def format(self, text, out):
        if not text:
            return
        self.out = out
        self._open_tags = []

        result = re.sub(self.rules, self.replace, util.escape(text.strip()))
        # Close all open 'one line'-tags
        result += self.close_tag(None)
        out.write(result)


class OutlineFormatter(Formatter):
    """
    A simple Wiki formatter
    """
    flavor = 'outline'
    
    def __init__(self, env, absurls=0, db=None):
        Formatter.__init__(self, env, None, absurls, db)

    def format(self, text, out, max_depth=None):
        self.outline = []
        class NullOut(object):
            def write(self, data): pass
        Formatter.format(self, text, NullOut())

        curr_depth = 0
        for depth,link in self.outline:
            if max_depth is not None and depth > max_depth:
                continue
            if depth < curr_depth:
                out.write('</li></ol><li>' * (curr_depth - depth))
            elif depth > curr_depth:
                out.write('<ol><li>' * (depth - curr_depth))
            else:
                out.write("</li><li>\n")
            curr_depth = depth
            out.write(link)
        out.write('</li></ol>' * curr_depth)

    def _heading_formatter(self, match, fullmatch):
        Formatter._heading_formatter(self, match, fullmatch)
        depth = min(len(fullmatch.group('hdepth')), 5)
        heading = match[depth + 1:len(match) - depth - 1]
        anchor = self._anchors[-1]
        self.outline.append((depth, '<a href="#%s">%s</a>' % (anchor, heading)))

    def handle_code_block(self, line):
        if line.strip() == '{{{':
            self.in_code_block += 1
        elif line.strip() == '}}}':
            self.in_code_block -= 1


def wiki_to_html(wikitext, env, req, db=None, absurls=0, escape_newlines=False):
    out = StringIO.StringIO()
    Formatter(env, req, absurls, db).format(wikitext, out, escape_newlines)
    return out.getvalue()

def wiki_to_oneliner(wikitext, env, db=None, absurls=0):
    out = StringIO.StringIO()
    OneLinerFormatter(env, absurls, db).format(wikitext, out)
    return out.getvalue()

def wiki_to_outline(wikitext, env, db=None, absurls=0, max_depth=None):
    out = StringIO.StringIO()
    OutlineFormatter(env, absurls ,db).format(wikitext, out, max_depth)
    return out.getvalue()


# InterWiki support

class InterWikiMap(Component):

    implements(IWikiChangeListener)

    _page_name = 'InterWikiTxt'
    _interwiki_re = re.compile(r"(\w+)[ \t]+(.*)[ \t]*$",re.UNICODE)

    def __init__(self):
        self._interwiki_map = None

    def has_key(self, ns):
        if not self._interwiki_map:
            self._update()
        return self._interwiki_map.has_key(ns.upper())

    def url(self, ns, target):
        return self._interwiki_map[ns.upper()] + target
        # FIXME: take $n arguments into account, according to #1414

    # IWikiChangeListener methods

    def wiki_page_added(self, page):
        if page == InterWikiMap._page_name:
            self._update()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        if page == InterWikiMap._page_name:
            self._update()

    def wiki_page_deleted(self, page):
        if page == InterWikiMap._page_name:
            self._interwiki_map.clear()

    def _update(self):
        from trac.wiki.model import WikiPage
        self._interwiki_map = {}
        content = WikiPage(self.env, InterWikiMap._page_name).text
        in_map = False
        for line in content.split('\n'):
            if in_map:
                if line.startswith('----'):
                    in_map = False
                else:
                    m = re.match(InterWikiMap._interwiki_re, line)
                    if m:
                        interwiki = m.group(1).upper()
                        url = m.group(2)
                        self._interwiki_map[interwiki] = url
            elif line.startswith('----'):
                in_map = True

