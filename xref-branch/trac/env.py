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

from trac import db, db_default, Logging, Mimeview, util
from trac.Xref import object_factory


import ConfigParser
import os
import shutil
import sys
import time
import urllib
import unicodedata

db_version = db_default.db_version

class Environment:
    """
    Trac stores project information in a Trac environment.

    A Trac environment consists of a directory structure containing
    among other things:
     * a configuration file.
     * a sqlite database (stores tickets, wiki pages...)
     * Project specific templates and wiki macros.
     * wiki and ticket attachments.
    """
    def __init__(self, path, create=0):
        self.path = path
        if create:
            self.create()
        self.verify()
        self.load_config()
        try: # Use binary I/O on Windows
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except ImportError:
            pass
        self.setup_log()
        self.setup_mimeviewer()

    def verify(self):
        """Verifies that self.path is a compatible trac environment"""
        fd = open(os.path.join(self.path, 'VERSION'), 'r')
        assert fd.read(26) == 'Trac Environment Version 1'
        fd.close()

    def get_db_cnx(self):
        return db.get_cnx(self)

    def get_repository(self, authname=None):
        from trac.versioncontrol.cache import CachedRepository
        from trac.versioncontrol.svn_authz import SubversionAuthorizer
        from trac.versioncontrol.svn_fs import SubversionRepository
        repos_dir = self.get_config('trac', 'repository_dir')
        if not repos_dir:
            raise EnvironmentError, 'Path to repository not configured'
        authz = None
        if authname:
            authz = SubversionAuthorizer(self, authname)
        repos = SubversionRepository(repos_dir, authz, self.log)
        return CachedRepository(self.get_db_cnx(), repos, authz, self.log)

    def create(self):
        def _create_file(fname, data=None):
            fd = open(fname, 'w')
            if data: fd.write(data)
            fd.close()
        # Create the directory structure
        os.mkdir(self.path)
        os.mkdir(os.path.join(self.path, 'conf'))
        os.mkdir(self.get_log_dir())
        os.mkdir(self.get_attachments_dir())
        os.mkdir(self.get_templates_dir())
        os.mkdir(os.path.join(self.path, 'wiki-macros'))
        # Create a few static files
        _create_file(os.path.join(self.path, 'VERSION'),
                     'Trac Environment Version 1\n')
        _create_file(os.path.join(self.path, 'README'),
                    'This directory contains a Trac project.\n'
                    'Visit http://trac.edgewall.com/ for more information.\n')
        _create_file(os.path.join(self.path, 'conf', 'trac.ini'))
        _create_file(os.path.join(self.get_templates_dir(), 'README'),
                     'This directory contains project-specific custom templates and style sheet.\n')
        _create_file(os.path.join(self.get_templates_dir(), 'site_header.cs'),
                     """<?cs
####################################################################
# Site header - Contents are automatically inserted above Trac HTML
?>
""")
        _create_file(os.path.join(self.get_templates_dir(), 'site_footer.cs'),
                     """<?cs
#########################################################################
# Site footer - Contents are automatically inserted after main Trac HTML
?>
""")
        _create_file(os.path.join(self.get_templates_dir(), 'site_css.cs'),
                     """<?cs
##################################################################
# Site CSS - Place custom CSS, including overriding styles here.
?>
""")
        # Create default database
        import sqlite
        os.mkdir(os.path.join(self.path, 'db'))
        cnx = sqlite.connect(os.path.join(self.path, 'db', 'trac.db'))
        cursor = cnx.cursor()
        cursor.execute(db_default.schema)
        cnx.commit()

    def insert_default_data(self):
        def prep_value(v):
            if v == None:
                return 'NULL'
            else:
                return '"%s"' % v
        cnx = self.get_db_cnx()
        cursor = cnx.cursor()
        
        for t in xrange(0, len(db_default.data)):
            table = db_default.data[t][0]
            cols = ','.join(db_default.data[t][1])
            for row in db_default.data[t][2]:
                values = ','.join(map(prep_value, row))
                sql = "INSERT INTO %s (%s) VALUES(%s);" % (table, cols, values)
                cursor.execute(sql)
        for s,n,v in db_default.default_config:
            if not self.cfg.has_section(s):
                self.cfg.add_section(s)
            self.cfg.set(s, n, v)
        self.save_config()
        cnx.commit()

    def get_version(self):
        cnx = self.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT value FROM system WHERE name='database_version'")
        row = cursor.fetchone()
        return row and int(row[0])

    def load_config(self):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(os.path.join(self.path, 'conf', 'trac.ini'))

    def get_config(self, section, name, default=''):
        if not self.cfg.has_option(section, name):
            return default
        return self.cfg.get(section, name)

    def set_config(self, section, name, value):
        """Changes a config value, these changes are _not_ persistent
        unless saved with save_config()"""
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        return self.cfg.set(section, name, value)

    def get_config_items(self, section):
        if not self.cfg.has_section(section):
            return None
        try:
            return self.cfg.items(section)
        except AttributeError:
            items=[]
            for option in self.cfg.options(section):
                items.append((option,self.cfg.get(section,option)))
            return items    


    def save_config(self):
        self.cfg.write(open(os.path.join(self.path, 'conf', 'trac.ini'), 'w'))

    def get_templates_dir(self):
        return os.path.join(self.path, 'templates')

    def get_log_dir(self):
        return os.path.join(self.path, 'log')

    def setup_log(self):
        logtype = self.get_config('logging','log_type','file')
        loglevel = self.get_config('logging','log_level','warn')
        logfile = self.get_config('logging','log_file','trac.log')
        logfile = os.path.join(self.get_log_dir(), logfile)
        logid = self.path # Env-path provides process-unique ID
        self.log = Logging.logger_factory(logtype, logfile, loglevel, logid)

    def setup_mimeviewer(self):
        self.mimeview = Mimeview.Mimeview(self)
    
    def get_attachments_dir(self):
        return os.path.join(self.path, 'attachments')

    def get_attachments(self, cnx, type, id):
        cursor = cnx.cursor()
        cursor.execute('SELECT filename,description,type,size,time,author,ipnr '
                       'FROM attachment '
                       'WHERE type=%s AND id=%s ORDER BY time', (type, id))
        return cursor.fetchall()
    
    def get_attachments_hdf(self, cnx, type, id, hdf, prefix):
        from Wiki import wiki_to_oneliner
        files = self.get_attachments(cnx, type, id)
        idx = 0
        for file in files:
            hdf['%s.%d' % (prefix, idx)] = {
                'name': file['filename'],
                'descr': wiki_to_oneliner(file['description'], self, cnx),
                'author': util.escape(file['author']),
                'ipnr': file['ipnr'],
                'size': util.pretty_size(file['size']),
                'time': time.strftime('%c', time.localtime(file['time'])),
                'href': self.href.attachment(type, id, file['filename'])
            }
            idx += 1

    def create_attachment(self, cnx, type, id, attachment,
                          description, author, ipnr):
        # Maximum attachment size (in bytes)
        max_size = int(self.get_config('attachment', 'max_size', '262144'))
        if hasattr(attachment.file, 'fileno'):
            stat = os.fstat(attachment.file.fileno())
            length = stat[6]
        else:
            length = attachment.file.len
        if max_size >= 0 and length > max_size:
            raise util.TracError('Maximum attachment size: %d bytes' % max_size,
                                 'Upload failed')
        dir = os.path.join(self.get_attachments_dir(), type,
                           urllib.quote(id))
        if not os.access(dir, os.F_OK):
            os.makedirs(dir)
        filename = attachment.filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        assert filename, 'No file uploaded'

        # We try to normalize the filename to utf-8 NFC if we can.
        # Files uploaded from OS X might be in NFD.
        if sys.version_info[0] > 2 or \
           (sys.version_info[0] == 2 and sys.version_info[1] >= 3):
            filename = unicodedata.normalize('NFC', unicode(filename, 'utf-8')).encode('utf-8')

        filename = urllib.quote(filename)
        path, fd = util.create_unique_file(os.path.join(dir, filename))
        filename = os.path.basename(path)
        filename = urllib.unquote(filename)
        cursor = cnx.cursor()
        cursor.execute('INSERT INTO attachment VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                       (type, id, filename, length, int(time.time()),
                       description, author, ipnr))
        object_factory(self, type, id).replace_xrefs_from_wiki(cnx, 'attachment:%s' % filename,
                                                               description)
        shutil.copyfileobj(attachment.file, fd)
        self.log.info('New attachment: %s/%s/%s by %s', type, id, filename, author)
        cnx.commit()
        return filename

    def delete_attachment(self, cnx, type, id, filename):
        cursor = cnx.cursor()
        cursor.execute('DELETE FROM attachment WHERE type=%s AND id=%s AND '
                       'filename=%s', (type, id, filename))

        qfilename = urllib.quote(filename)
        
        object_factory(env, type, id).delete_xrefs(cnx, 'attachment:%s' % qfilename)

        path = os.path.join(self.get_attachments_dir(), type,
                            urllib.quote(id), qfilename)
        try:
            os.unlink(path)
        except OSError:
            # Older versions of Trac saved attachments with unquoted filenames,
            # so try that. See #1112.
            path = os.path.join(self.get_attachments_dir(), type,
                                urllib.quote(id), filename)
            try:
                os.unlink(path)
            except OSError:
                raise util.TracError, 'Attachment not found'

        self.log.info('Attachment removed: %s/%s/%s', type, id, filename)
        cnx.commit()

    def get_known_users(self, cnx=None):
        """
        Generator that yields information about all known users, i.e. users that
        have logged in to this Trac environment and possibly set their name and
        email.

        This function generates one tuple for every user, of the form
        (username, name, email) ordered alpha-numerically by username.
        """
        if not cnx:
            cnx = self.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT DISTINCT s.username, n.var_value, e.var_value "
                       "FROM session AS s "
                       " LEFT JOIN session AS n ON (n.sid IS NULL "
                       "  AND n.username=s.username AND n.var_name = 'name') "
                       " LEFT JOIN session AS e ON (e.sid IS NULL "
                       "  AND e.username=s.username AND e.var_name = 'email') "
                       "WHERE s.sid IS NULL ORDER BY s.username")
        for username,name,email in cursor:
            yield username, name, email

    def backup(self, dest=None):
        """Simple SQLite-specific backup. Copy the database file."""
        db_str = self.get_config('trac', 'database', 'sqlite:db/trac.db')
        if db_str[:7] != 'sqlite:':
            raise EnvironmentError, 'Can only backup sqlite databases'
        db_name = os.path.join(self.path, db_str[7:])
        if not dest:
            dest = '%s.%i.bak' % (db_name, self.get_version())
        shutil.copy (db_name, dest)

    def upgrade(self, backup=None,backup_dest=None):
        """Upgrade database. Each db version should have its own upgrade
        module, names upgrades/dbN.py, where 'N' is the version number (int)."""
        dbver = self.get_version()
        if dbver == db_default.db_version:
            return 0
        elif dbver > db_default.db_version:
            raise EnvironmentError, 'Database newer than Trac version'
        else:
            if backup:
                self.backup(backup_dest)
            cnx = self.get_db_cnx()
            cursor = cnx.cursor()
            import upgrades
            for i in xrange(dbver + 1, db_default.db_version + 1):
                try:
                    upg  = 'db%i' % i
                    __import__('upgrades', globals(), locals(),[upg])
                    d = getattr(upgrades, upg)
                except AttributeError:
                    err = 'No upgrade module for version %i (%s.py)' % (i, upg)
                    raise EnvironmentError, err
                d.do_upgrade(self, i, cursor)
                if hasattr(d, 'do_db_upgrade'): # for more complex upgrades, as in 'db9.py'
                    d.do_db_upgrade(self, i, cnx)
            cursor.execute("UPDATE system SET value=%s WHERE "
                           "name='database_version'", (db_default.db_version))
            self.log.info('Upgraded db version from %d to %d',
                          dbver, db_default.db_version)
            cnx.commit()
            return 1


def open_environment(env_path=None):
    if not env_path:
        env_path = os.getenv('TRAC_ENV')
    if not env_path:
        raise EnvironmentError, \
              'Missing environment variable "TRAC_ENV". Trac requires this ' \
              'variable to point to a valid Trac Environment.'

    env = Environment(env_path)
    version = env.get_version()
    if version < db_version:
        raise EnvironmentError, \
              'The Trac Environment needs to be upgraded. Run "trac-admin %s ' \
              'upgrade"' % env_path
    elif version > db_version:
        raise EnvironmentError, \
              'Unknown Trac Environment version (%d).' % version
    return env
