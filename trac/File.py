# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003, 2004 Edgewall Software
# Copyright (C) 2003, 2004 Jonas Borgstr�m <jonas@edgewall.com>
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
#
# FIXME:
# * We need to figure out the encoding used somehow.

import os
import sys
import time
import StringIO
import mimetypes

import svn

import perm
import util
from Module import Module

class FileCommon(Module):
    CHUNK_SIZE = 4096
    MAX_FILE_SIZE = 128 * 1024
    
    def render (self):
        self.perm.assert_permission (perm.FILE_VIEW)

    def display(self):
        if self.mime_type and self.mime_type[:6] == 'image/':
            self.req.hdf.setValue('file.highlighted_html',
                                  '<hr /><img src="?format=raw">')
        elif self.mime_type and self.mime_type != 'application/octet-stream':
            data = self.read_func(self.MAX_FILE_SIZE)
            if len(data) == self.MAX_FILE_SIZE:
                self.req.hdf.setValue('file.max_file_size_reached', '1')
                self.req.hdf.setValue('file.max_file_size',
                                      str(self.MAX_FILE_SIZE))
            self.req.hdf.setValue('file.highlighted_html',
                                  self.env.mimeview.display(data, self.mime_type))
        self.req.display('file.cs')

    def display_raw(self):
        self.req.send_response(200)
        self.req.send_header('Content-Type', self.mime_type)
        self.req.send_header('Conten-Length', str(self.length))
        self.req.send_header('Last-Modified', self.last_modified)
        self.req.end_headers()
        while 1:
            data = self.read_func(self.CHUNK_SIZE)
            if not data:
                break
            self.req.write(data)
    
class Attachment(FileCommon):
    def render(self):
        FileCommon.render(self)
        
        self.attachment_type = self.args.get('type', None)
        self.attachment_id = self.args.get('id', None)
        self.filename = os.path.basename(self.args.get('filename', None))

        self.path = os.path.join(self.env.get_attachments_dir(),
                                 self.attachment_type,
                                 self.attachment_id,
                                 self.filename)
        try:
            f = open(self.path, 'rb')
        except IOError:
            raise util.TracError('Attachment not found')
        
        self.mime_type, enc = mimetypes.guess_type(self.filename)
        stat = os.fstat(f.fileno())
        self.length = stat[6]
        self.last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                      time.gmtime(stat[8]))
        self.read_func = lambda x: f.read(x)

    def display(self):
        self.req.hdf.setValue('file.filename', self.filename)
        if self.attachment_type == 'ticket':
            self.req.hdf.setValue('file.attachment_parent',
                                  '#' + self.attachment_id)
            self.req.hdf.setValue('file.attachment_parent_href',
                                  self.env.href.ticket(int(self.attachment_id)))
        FileCommon.display(self)


class File(FileCommon):
    def generate_path_links(self):
        # FIXME: Browser, Log and File should share implementation of this
        # function.
        list = self.path.split('/')
        path = '/'
        self.req.hdf.setValue('file.filename', list[-1])
        self.req.hdf.setValue('file.path.0', '[root]')
        self.req.hdf.setValue('file.path.0.url' , self.env.href.browser(path))
        i = 0
        for part in list[:-1]:
            i = i + 1
            if part == '':
                break
            path = path + part + '/'
            self.req.hdf.setValue('file.path.%d' % i, part)
            self.req.hdf.setValue('file.path.%d.url' % i,
                                  self.env.href.browser(path))

    def display(self):
        self.generate_path_links()
        FileCommon.display(self)

    def render(self):
        FileCommon.render(self)
        
        rev = self.args.get('rev', None)
        self.path = self.args.get('path', '/')
        if not rev:
            rev = svn.fs.youngest_rev(self.fs_ptr, self.pool)
        else:
            rev = int(rev)
        root = svn.fs.revision_root(self.fs_ptr, rev, self.pool)
        
        # Try to do an educated guess about the mime-type
        self.mime_type = svn.fs.node_prop (root, self.path,
                                           svn.util.SVN_PROP_MIME_TYPE,
                                           self.pool)
        if not self.mime_type:
            self.mime_type = mimetypes.guess_type(self.path)[0] or 'text/plain'
        elif self.mime_type == 'application/octet-stream':
            self.mime_type = mimetypes.guess_type(self.path)[0] or \
                             'application/octet-stream'
            
        self.length = svn.fs.file_length(root, self.path, self.pool)
        date = svn.fs.revision_prop(self.fs_ptr, rev,
                                svn.util.SVN_PROP_REVISION_DATE, self.pool)
        date_seconds = svn.util.svn_time_from_cstring(date, self.pool) / 1000000
        self.last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                      time.gmtime(date_seconds))
        f = svn.fs.file_contents(root, self.path, self.pool)
        self.read_func = lambda x: svn.util.svn_stream_read(f, x)
