#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
__author__ = 'Daniel Lundin <daniel@edgewall.com>, Jonas Borgstr�m <jonas@edgewall.com>'
__copyright__ = 'Copyright (c) 2005 Edgewall Software'
__license__ = """
 Copyright (C) 2003, 2004, 2005 Edgewall Software
 Copyright (C) 2003, 2004 Jonas Borgstr�m <jonas@edgewall.com>
 Copyright (C) 2003, 2004 Daniel Lundin <daniel@edgewall.com>

 Trac is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License as
 published by the Free Software Foundation; either version 2 of
 the License, or (at your option) any later version.

 Trac is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA."""

import os
import os.path
import sys
import time
import cmd
import shlex
import shutil
import StringIO
import urllib

from trac import perm, util
from trac.env import Environment
from trac.Milestone import Milestone
import trac.siteconfig

def my_sum(list):
    """Python2.2 doesn't have sum()"""
    tot = 0
    for item in list:
        tot += item
    return tot


class TracAdmin(cmd.Cmd):
    intro = ''
    license = trac.__license_long__
    credits = trac.__credits__
    doc_header = 'Trac Admin Console %(ver)s\n' \
                 'Available Commands:\n' \
                 % {'ver':trac.__version__ }
    ruler = ''
    prompt = "Trac> "
    __env = None
    
    def __init__(self,envdir=None):
        cmd.Cmd.__init__(self)
        self.interactive = 0
        if envdir:
            self.env_set(os.path.abspath(envdir))

    def docmd(self, cmd='help'):
        self.onecmd(cmd)

    def emptyline(self):
        pass

    def run(self):
        self.interactive = 1
        print 'Welcome to trac-admin %(ver)s\n'                \
              'Interactive Trac adminstration console.\n'       \
              '%(copy)s\n\n'                                    \
              "Type:  '?' or 'help' for help on commands.\n" %  \
              {'ver':trac.__version__,'copy':__copyright__}
        while 1:
            try:
                self.cmdloop()
                break
            except KeyboardInterrupt:
                print "\n** Interrupt. Use 'quit' to exit **"

    ##
    ## Environment methods
    ##

    def env_set(self, envname, env=None):
        self.envname = envname
        self.prompt = "Trac [%s]> " % self.envname
        if env is not None:
            self.__env = env

    def env_check(self):
        try:
            self.__env = Environment(self.envname)
        except:
            return 0
        return 1

    def env_create(self, db_str):
        try:
            self.__env = Environment(self.envname, create=True, db_str=db_str)
            return self.__env
        except Exception, e:
            print 'Failed to create environment.', e
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def db_open(self):
        try:
            if not self.__env:
                self.__env = Environment(self.envname)
            return self.__env.get_db_cnx()
        except Exception, e:
            print 'Failed to open environment.', e
            sys.exit(1)

    def db_execsql (self, sql, cursor=None):
        data = []
        if not cursor:
            cnx=self.db_open()
            cursor = cnx.cursor()
        else:
            cnx = None
        cursor.execute(sql)
        while 1:
            row = cursor.fetchone()
            if row == None:
                break
            data.append(row)
        if cnx:
            cnx.commit()
        return data

    ##
    ## Utility methods
    ##

    def arg_tokenize (self, argstr):
        if hasattr(shlex, 'split'):
            toks = shlex.split(argstr)
        else:
            def my_strip(s, c):
                """string::strip in python2.1 doesn't support arguments"""
                i = j = 0
                for i in range(len(s)):
                    if not s[i] in c:
                        break
                for j in range(len(s), 0, -1):
                    if not s[j-1] in c:
                        break
                return s[i:j]
        
            lexer = shlex.shlex(StringIO.StringIO(argstr))
            lexer.wordchars = lexer.wordchars + ".,_/"
            toks = []
            while 1:
                token = my_strip(lexer.get_token(), '"\'')
                if not token:
                    break
                toks.append(token)
        return toks or ['']

    def word_complete (self, text, words):
        return [a for a in words if a.startswith (text)]

    def print_listing(self, headers, data, sep=' ',decor=1):
        ldata = data
        if decor:
            ldata.insert (0, headers)
        print
        colw=[]
        ncols = len(ldata[0]) # assumes all rows are of equal length
        for cnum in xrange(0, ncols):
            mw = 0
            for cell in [str(d[cnum]) or '' for d in ldata]:
                if len(cell) > mw:
                    mw = len(cell)
            colw.append(mw)
        for rnum in xrange(0, len(ldata)):
            for cnum in xrange(0, ncols):
                if decor and rnum == 0:
                    sp = ('%%%ds' % len(sep)) % ' '  # No separator in header
                else:
                    sp = sep
                if cnum+1 == ncols: sp = '' # No separator after last column
                print ("%%-%ds%s" % (colw[cnum], sp)) % (ldata[rnum][cnum] or ''),
            print
            if rnum == 0 and decor:
                print ''.join(['-' for x in xrange(0,(1+len(sep))*cnum+my_sum(colw))])
        print

    def print_doc(self,doc,decor=0):
        if not doc: return
        self.print_listing (['Command','Description'], doc, '  --', decor) 

    def get_component_list (self):
        data = self.db_execsql ("SELECT name FROM component")
        return [r[0] for r in data]

    def get_user_list (self):
        data = self.db_execsql ("SELECT DISTINCT username FROM permission")
        return [r[0] for r in data]

    def get_wiki_list (self):
        data = self.db_execsql('SELECT DISTINCT name FROM wiki') 
        return [r[0] for r in data]

    def get_dir_list (self, pathstr,justdirs=0):
        dname = os.path.dirname(pathstr)
        d = os.path.join(os.getcwd(), dname)
        dlist = os.listdir(d)
        if justdirs:
            result = []
            for entry in dlist:
                try:
                    if os.path.isdir(entry):
                        result.append(entry)
                except:
                    pass
        else:
            result = dlist
        return result

    def get_enum_list (self, type):
        data = self.db_execsql("SELECT name FROM enum WHERE type='%s'" % type) 
        return [r[0] for r in data]

    def get_milestone_list (self):
        data = self.db_execsql("SELECT name FROM milestone") 
        return [r[0] for r in data]

    def get_version_list (self):
        data = self.db_execsql("SELECT name FROM version") 
        return [r[0] for r in data]

    def _parse_datetime(self, t):
        seconds = None
        t = t.strip()
        if t == 'now':
            seconds = int(time.time())
        else:
            for format in ['%x %X', '%x, %X', '%X %x', '%X, %x', '%x', '%c',
                           '%b %d, %Y']:
                try:
                    pt = time.strptime(t, format)
                    seconds = int(time.mktime(pt))
                except ValueError:
                    continue
                break
        if seconds == None:
            try:
                seconds = int(t)
            except ValueError:
                pass
        if seconds == None:
            print >> sys.stderr, 'Unknown time format'
        return seconds


    ##
    ## Available Commands
    ##

    ## Help
    _help_help = [('help', 'Show documentation')]

    def do_help(self, line=None):
        arg = self.arg_tokenize(line)
        if arg[0]:
            try:
                doc = getattr(self, "_help_" + arg[0])
                self.print_doc (doc)
            except AttributeError:
                print "No documentation found for '%s'" % arg[0]
        else:
            docs = (self._help_about + self._help_help +
                    self._help_initenv + self._help_hotcopy +
                    self._help_resync + self._help_upgrade +
                    self._help_wiki +
#                    self._help_config + self._help_wiki +
                    self._help_permission + self._help_component +
                    self._help_priority + self._help_severity + 
                    self._help_version + self._help_milestone)
            print 'trac-admin - The Trac Administration Console %s' % trac.__version__
            if not self.interactive:
                print
                print "Usage: trac-admin </path/to/projenv> [command [subcommand] [option ...]]\n"
                print "Invoking trac-admin without command starts "\
                       "interactive mode."
            self.print_doc (docs)
            print self.credits

    
    ## About / Version
    _help_about = [('about', 'Shows information about trac-admin')]

    def do_about(self, line):
        print
        print 'Trac Admin Console %s' % trac.__version__
        print '================================================================='
        print self.license
        print self.credits


    ## Quit / EOF
    _help_quit = [['quit', 'Exit the program']]
    _help_exit = _help_quit
    _help_EOF = _help_quit

    def do_quit(self,line):
        print
        sys.exit()

    do_exit = do_quit # Alias
    do_EOF = do_quit # Alias

#    ## Component
    _help_component = [('component list', 'Show available components'),
                       ('component add <name> <owner>', 'Add a new component'),
                       ('component rename <name> <newname>', 'Rename a component'),
                       ('component remove <name>', 'Remove/uninstall component'),
                       ('component chown <name> <owner>', 'Change component ownership')]

    def complete_component (self, text, line, begidx, endidx):
        if begidx in [16,17]:
            comp = self.get_component_list()
        elif begidx > 15 and line.startswith('component chown '):
            comp = self.get_user_list()
        else:
            comp = ['list','add','rename','remove','chown']
        return self.word_complete(text, comp)

    def do_component(self, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                self._do_component_list()
            elif arg[0] == 'add' and len(arg)==3:
                name = arg[1]
                owner = arg[2]
                self._do_component_add(name, owner)
            elif arg[0] == 'rename' and len(arg)==3:
                name = arg[1]
                newname = arg[2]
                self._do_component_rename(name, newname)
            elif arg[0] == 'remove'  and len(arg)==2:
                name = arg[1]
                self._do_component_remove(name)
            elif arg[0] == 'chown' and len(arg)==3:
                name = arg[1]
                owner = arg[2]
                self._do_component_set_owner(name, owner)
            else:    
                self.do_help ('component')
        except Exception, e:
            print 'Component %s failed:' % arg[0], e

    def _do_component_list(self):
        data = self.db_execsql('SELECT name, owner FROM component') 
        self.print_listing(['Name', 'Owner'], data)

    def _do_component_add(self, name, owner):
        self.db_execsql("INSERT INTO component (name,owner) VALUES('%s','%s')"
                        % (name, owner))

    def _do_component_rename(self, name, newname):
        cnx = self.db_open()
        cursor = cnx.cursor ()
        cursor.execute('SELECT name FROM component WHERE name=%s', name)
        data = cursor.fetchone()
        if not data:
            raise Exception("No such component '%s'" % name)
        self.db_execsql("UPDATE component SET name='%s' WHERE name='%s'"
                        % (newname,name), cursor)
        self.db_execsql("UPDATE ticket SET component='%s' WHERE component='%s'"
                        % (newname,name), cursor)
        cnx.commit()

    def _do_component_remove(self, name):
        cnx = self.db_open()
        cursor = cnx.cursor ()
        cursor.execute('SELECT name FROM component WHERE name=%s', name)
        data = cursor.fetchone()
        if not data:
            raise Exception("No such component '%s'" % name)
        data = self.db_execsql("DELETE FROM component WHERE name='%s'"
                               % (name))

    def _do_component_set_owner(self, name, owner):
        cnx = self.db_open()
        cursor = cnx.cursor ()
        cursor.execute('SELECT name FROM component WHERE name=%s', name)
        data = cursor.fetchone()
        if not data:
            raise Exception("No such component '%s'" % name)
        data = self.db_execsql("UPDATE component SET owner='%s' WHERE name='%s'"
                               % (owner,name))


    ## Permission
    _help_permission = [('permission list [user]', 'List permission rules'),
                       ('permission add <user> <action> [action] [...]', 'Add a new permission rule'),
                       ('permission remove <user> <action> [action] [...]', 'Remove permission rule')]

    def complete_permission(self, text, line, begidx, endidx):
        argv = self.arg_tokenize(line)
        argc = len(argv)
        if line[-1] == ' ': # Space starts new argument
            argc += 1
        if argc == 2:
            comp = ['list','add','remove']
        elif argc >= 4:
            comp = perm.permissions + perm.meta_permissions.keys()
            comp.sort()
        return self.word_complete(text, comp)

    def do_permission(self, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                user = None
                if len(arg) > 1:
                    user = arg[1]
                self._do_permission_list(user)
            elif arg[0] == 'add' and len(arg) >= 3:
                user = arg[1]
                for action in arg[2:]:
                    self._do_permission_add(user, action)
            elif arg[0] == 'remove'  and len(arg) >= 3:
                user = arg[1]
                for action in arg[2:]:
                    self._do_permission_remove(user, action)
            else:
                self.do_help('permission')
        except Exception, e:
            print 'Permission %s failed:' % arg[0], e

    def _do_permission_list(self, user=None):
        if user:
            data = self.db_execsql("SELECT username, action FROM permission "
                                   "WHERE username='%s' ORDER BY action" % user)
        else:
            data = self.db_execsql("SELECT username, action FROM permission "
                                   "ORDER BY username, action")
        self.print_listing(['User', 'Action'], data)
        print
        print 'Available actions:'
        actions = perm.permissions + perm.meta_permissions.keys()
        actions.sort()
        text = ', '.join(actions)
        print util.wrap(text, initial_indent=' ', subsequent_indent=' ',
                        linesep='\n')
        print

    def _do_permission_add(self, user, action):
        if not action.islower() and not action.isupper():
            print 'Group names must be in lower case and actions in upper case'
            return
        if action.isupper() and not \
           action in perm.permissions + perm.meta_permissions.keys():
            print '%s is not a valid action. Use the permission list command ' \
                  'to see the available actions.' % (action)
            return
        self.db_execsql("INSERT INTO permission VALUES('%s', '%s')" % (user, action))

    def _do_permission_remove(self, user, action):
        sql = "DELETE FROM permission"
        clauses = []
        if action != '*':
            clauses.append("action='%s'" % action)
        if user != '*':
            clauses.append("username='%s'" % user)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        self.db_execsql(sql)

    ## Initenv
    _help_initenv = [('initenv', 'Create and initialize a new environment interactively'),
                     ('initenv <projectname> <repospath> <templatepath>',
                      'Create and initialize a new environment from arguments')]

    def do_initdb(self, line):
        self.do_initenv(line)
        
    def get_initenv_args(self):
        returnvals = []
        print 'Creating a new Trac environment at %s' % self.envname
        print
        print 'Trac will first ask a few questions about your environment '
        print 'in order to initalize and prepare the project database.'
        print
        print " Please enter the name of your project."
        print " This name will be used in page titles and descriptions."
        print
        dp = 'My Project'
        returnvals.append(raw_input('Project Name [%s]> ' % dp) or dp)
        print
        print ' Please specify the connection string for the database to use.'
        print ' By default, a local SQLite database is created in the environment '
        print ' directory. It is also possible to use an already existing '
        print ' PostgreSQL database (check the Trac documentation for the exact '
        print ' connection string syntax).'
        print
        ddb = 'sqlite:db/trac.db'
        prompt = 'Database connection string [%s]> ' % ddb
        returnvals.append(raw_input(prompt) or ddb)
        print
        print ' Please specify the absolute path to the project Subversion repository.'
        print ' Repository must be local, and trac-admin requires read+write'
        print ' permission to initialize the Trac database.'
        print
        drp = '/var/svn/test'
        prompt = 'Path to repository [%s]> ' % drp
        returnvals.append(raw_input(prompt) or drp)
        print
        print ' Please enter location of Trac page templates.'
        print ' Default is the location of the site-wide templates installed with Trac.'
        print
        dt = trac.siteconfig.__default_templates_dir__
        prompt = 'Templates directory [%s]> ' % dt
        returnvals.append(raw_input(prompt) or dt)
        return returnvals

    def do_initenv(self, line):
        if self.env_check():
            print "Initenv for '%s' failed.\nDoes an environment already exist?" % self.envname
            return
        arg = self.arg_tokenize(line)
        project_name = None
        db_str = None
        repository_dir = None
        templates_dir = None
        if len(arg) == 1:
            returnvals = self.get_initenv_args()
            project_name, db_str, repository_dir, templates_dir = returnvals
        elif len(arg)!= 3:
            print 'Wrong number of arguments to initenv %d' % len(arg)
            return
        else:
            project_name, db_str, repository_dir, templates_dir = arg[0:3]

        if not os.access(os.path.join(templates_dir, 'header.cs'), os.F_OK):
            print templates_dir, "doesn't look like a Trac templates directory"
            return
        try:
            print 'Creating and Initializing Project'
            self.env_create(db_str)

            print ' Configuring Project'
            config = self.__env.config
            print '  trac.repository_dir'
            config.set('trac', 'repository_dir', repository_dir)
            print '  trac.database'
            config.set('trac', 'database', db_str)
            print '  trac.templates_dir'
            config.set('trac', 'templates_dir', templates_dir)
            print '  project.name'
            config.set('project', 'name', project_name)
            config.save()

            # Add the default wiki macros
            print ' Installing default wiki macros'
            for f in os.listdir(trac.siteconfig.__default_macros_dir__):
                if not f.endswith('.py'):
                    continue
                src = os.path.join(trac.siteconfig.__default_macros_dir__, f)
                dst = os.path.join(self.__env.path, 'wiki-macros', f)
                print " %s => %s" % (src, f)
                shutil.copy2(src, dst)

            # Add a few default wiki pages
            print ' Installing default wiki pages'
            cnx = self.__env.get_db_cnx()
            cursor = cnx.cursor()
            self._do_wiki_load(trac.siteconfig.__default_wiki_dir__, cursor)
            cnx.commit()

            print ' Indexing repository'
            repos = self.__env.get_repository()
            repos.sync()

        except Exception, e:
            print 'Failed to initialize environment.', e
            import traceback
            traceback.print_exc()
            sys.exit(2)


        print "---------------------------------------------------------------------"
        print
        print 'Project database for \'%s\' created.' % project_name
        print
        print ' Customize settings for your project using the command:'
        print
        print '   trac-admin %s' % self.envname
        print
        print ' Don\'t forget, you also need to copy (or symlink) "trac/cgi-bin/trac.cgi"'
        print ' to you web server\'s /cgi-bin/ directory, and then configure the server.'
        print
        print ' If you\'re using Apache, this config example snippet might be helpful:'
        print
        print '    Alias /trac "/wherever/you/installed/trac/htdocs/"'
        print '    <Location "/cgi-bin/trac.cgi">'
        print '        SetEnv TRAC_ENV "%s"' % self.envname
        print '    </Location>'
        print
        print '    # You need something like this to authenticate users'
        print '    <Location "/cgi-bin/trac.cgi/login">'
        print '        AuthType Basic'
        print '        AuthName "%s"' % project_name
        print '        AuthUserFile /somewhere/trac.htpasswd'
        print '        Require valid-user'
        print '    </Location>'
        print

        print ' The latest documentation can also always be found on the project website:'
        print ' http://projects.edgewall.com/trac/'
        print
        print 'Congratulations!'
        print
        
    _help_resync = [('resync', 'Re-synchronize trac with the repository')]

    ## Resync
    def do_resync(self, line):
        self.db_open() # We need to call this function to open the env, really stupid

        print 'resyncing...'
        cnx = self.__env.get_db_cnx()
        self.db_execsql("DELETE FROM revision")
        self.db_execsql("DELETE FROM node_change")

        repos = self.__env.get_repository()
        repos.sync()
            
        print 'done.'

    ## Wiki
    _help_wiki = [('wiki list', 'List wiki pages'),
                  ('wiki remove <name>', 'Remove wiki page'),
                  ('wiki export <page> [file]',
                   'Export wiki page to file or stdout'),
                  ('wiki import <page> [file]',
                   'Import wiki page from file or stdin'),
                  ('wiki dump <directory>',
                   'Export all wiki pages to files named by title'),
                  ('wiki load <directory>',
                   'Import all wiki pages from directory'),
                  ('wiki upgrade',
                   'Upgrade default wiki pages to current version')]

    def complete_wiki(self, text, line, begidx, endidx):
        argv = self.arg_tokenize(line)
        argc = len(argv)
        if line[-1] == ' ': # Space starts new argument
            argc += 1
        if argc == 2:
            comp = ['list','remove','import','export','dump','load', 'upgrade']
        else:
            if argv[1] in ['dump','load']:
                comp = self.get_dir_list(argv[-1], 1)
            elif argv[1] in ['export', 'import']:
                if argc==3:
                    comp = self.get_wiki_list()
                elif argc==4:
                    comp = self.get_dir_list(argv[-1])
        return self.word_complete(text, comp)

    def do_wiki(self, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                self._do_wiki_list()
            elif arg[0] == 'remove'  and len(arg)==2:
                name = arg[1]
                self._do_wiki_remove(name)
            elif arg[0] == 'import' and len(arg) == 3:
                title = arg[1]
                file = arg[2]
                self._do_wiki_import(file, title)
            elif arg[0] == 'export'  and len(arg) in [2,3]:
                page = arg[1]
                file = (len(arg) == 3 and arg[2]) or None
                self._do_wiki_export(page, file)
            elif arg[0] == 'dump' and len(arg) in [1,2]:
                dir = (len(arg) == 2 and arg[1]) or ''
                self._do_wiki_dump(dir)
            elif arg[0] == 'load' and len(arg) in [1,2]:
                dir = (len(arg) == 2 and arg[1]) or ''
                self._do_wiki_load(dir)
            elif arg[0] == 'upgrade' and len(arg) == 1:
                self._do_wiki_load(trac.siteconfig.__default_wiki_dir__,
                                   ignore=['WikiStart', 'checkwiki.py'])
            else:    
                self.do_help ('wiki')
        except Exception, e:
            print 'Wiki %s failed:' % arg[0], e

    def _do_wiki_list(self):
        data = self.db_execsql('SELECT name,max(version),time'
                               ' FROM wiki GROUP BY name ORDER BY name')
        ldata = [(d[0], d[1], time.ctime(d[2])) for d in data]
        self.print_listing(['Title', 'Edits', 'Modified'], ldata)

    def _do_wiki_remove(self, name):
        cnx = self.db_open()
        cursor = cnx.cursor ()
        cursor.execute('SELECT name FROM wiki WHERE name=%s', name)
        data = cursor.fetchone()
        if not data:
            raise Exception("No such wiki page '%s'" % name)
        data = self.db_execsql("DELETE FROM wiki WHERE name='%s'"
                               % (name))

    def _do_wiki_import(self, filename, title, cursor=None):
        if not os.path.isfile(filename):
            print "%s is not a file" % filename
            return
        f = open(filename,'r')
        data = util.to_utf8(f.read())

        # Make sure we don't insert the exact same page twice
        old = self.db_execsql("SELECT text FROM wiki "
                              "WHERE name='%s' "
                              "ORDER BY version DESC LIMIT 1" % title, cursor)
        if old and data == old[0][0]:
            print '  %s already up to date.' % title
            return
        
        data = data.replace("'", "''") # Escape ' for safe SQL
        f.close()
        
        sql = ("INSERT INTO wiki(version,name,time,author,ipnr,text) "
               " SELECT 1+COALESCE(max(version),0),'%(title)s','%(time)s',"
               " '%(author)s','%(ipnr)s','%(text)s' FROM wiki "
               " WHERE name='%(title)s'" 
               % {'title':title,
                  'time':int(time.time()),
                  'author':'trac',
                  'ipnr':'127.0.0.1',
                  'locked':'0',
                  'text':data})
        self.db_execsql(sql, cursor)

    def _do_wiki_export(self, page,filename=''):
        data=self.db_execsql("SELECT text FROM wiki "
                             " WHERE name='%s'"
                             " ORDER BY version DESC LIMIT 1" % page)
        text = data[0][0]
        if not filename:
            print text
        else:
            if os.path.isfile(filename):
                raise Exception("File '%s' exists" % filename)
            f = open(filename,'w')
            f.write(text)
            f.close()

    def _do_wiki_dump(self, dir):
        pages = self.get_wiki_list()
        for p in pages:
            dst = os.path.join(dir, urllib.quote(p, ''))
            print " %s => %s" % (p, dst)
            self._do_wiki_export(p, dst)

    def _do_wiki_load(self, dir,cursor=None, ignore=[]):
        for page in os.listdir(dir):
            if page in ignore:
                continue
            filename = os.path.join(dir, page)
            page = urllib.unquote(page)
            if os.path.isfile(filename):
                print " %s => %s" % (filename, page)
                self._do_wiki_import(filename, page, cursor)


    ## (Ticket) Priority
    _help_priority = [('priority list', 'Show possible ticket priorities'),
                       ('priority add <value>', 'Add a priority value option'),
                       ('priority change <value> <newvalue>',
                        'Change a priority value'),
                       ('priority remove <value>', 'Remove priority value')]

    def complete_priority (self, text, line, begidx, endidx):
        if begidx == 16:
            comp = self.get_enum_list ('priority')
        elif begidx < 15:
            comp = ['list','add','change','remove']
        return self.word_complete(text, comp)

    def do_priority(self, line):
        self._do_enum('priority', line)

    ## (Ticket) Severity
    _help_severity = [('severity list', 'Show possible ticket severities'),
                       ('severity add <value>', 'Add a severity value option'),
                       ('severity change <value> <newvalue>',
                        'Change a severity value'),
                       ('severity remove <value>', 'Remove severity value')]

    def complete_severity (self, text, line, begidx, endidx):
        if begidx == 16:
            comp = self.get_enum_list ('severity')
        elif begidx < 15:
            comp = ['list','add','change','remove']
        return self.word_complete(text, comp)

    def do_severity(self, line):
        self._do_enum('severity', line)

    # Priority and Severity share the same datastructure and methods:
    
    def _do_enum(self, type, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                self._do_enum_list(type)
            elif arg[0] == 'add' and len(arg)==2:
                name = arg[1]
                self._do_enum_add(type, name)
            elif arg[0] == 'change'  and len(arg)==3:
                name = arg[1]
                newname = arg[2]
                self._do_enum_change(type, name, newname)
            elif arg[0] == 'remove'  and len(arg)==2:
                name = arg[1]
                self._do_enum_remove(type, name)
            else:    
                self.do_help (type)
        except Exception, e:
            print 'Command %s failed:' % arg[0], e

    def _do_enum_list(self, type):
        data = self.db_execsql("SELECT name FROM enum WHERE type='%s' "
                               "ORDER BY value" % type)
        self.print_listing(['Possible Values'], data)

    def _do_enum_add(self, type, name):
        sql = ("INSERT INTO enum(value,type,name) "
               " SELECT 1+COALESCE(max(value),0),'%(type)s','%(name)s'"
               "   FROM enum WHERE type='%(type)s'" 
               % {'type':type, 'name':name})
        self.db_execsql(sql)

    def _do_enum_change(self, type, name, newname):
        d = {'name':name, 'newname':newname, 'type':type}
        data = self.db_execsql("SELECT name FROM enum" 
                               " WHERE type='%(type)s' AND name='%(name)s'" % d)
        if not data:
            raise Exception, "No such value '%s'" % name
        data = self.db_execsql("UPDATE enum SET name='%(newname)s'" 
                               " WHERE type='%(type)s' AND name='%(name)s'" % d)

    def _do_enum_remove(self, type, name):
        data = self.db_execsql("SELECT name FROM enum" 
                               " WHERE type='%s' AND name='%s'" % (type, name))
        if not data:
            raise Exception, "No such value '%s'" % name
        data = self.db_execsql("DELETE FROM enum WHERE type='%s' AND name='%s'"
                               % (type, name))


    ## Milestone
    _help_milestone = [('milestone list', 'Show milestones'),
                       ('milestone add <name> [due]', 'Add milestone'),
                       ('milestone rename <name> <newname>',
                        'Rename milestone'),
                       ('milestone due <name> <due>',
                        'Set milestone due date (Format: "%s" or "now")'
                        % util.get_date_format_hint()),
                       ('milestone completed <name> <completed>',
                        'Set milestone completed date (Format: "%s" or "now")'
                        % util.get_date_format_hint()),
                       ('milestone remove <name>', 'Remove milestone')]

    def complete_milestone (self, text, line, begidx, endidx):
        if begidx in [15,17]:
            comp = self.get_milestone_list ()
        elif begidx < 15:
            comp = ['list','add','rename','time','remove']
        return self.word_complete(text, comp)

    def do_milestone(self, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                self._do_milestone_list()
            elif arg[0] == 'add' and len(arg) in [2,3]:
                self._do_milestone_add(arg[1])
                if len(arg) == 3:
                    self._do_milestone_set_due(arg[1], arg[2])
            elif arg[0] == 'rename' and len(arg) == 3:
                self._do_milestone_rename(arg[1], arg[2])
            elif arg[0] == 'remove' and len(arg) == 2:
                self._do_milestone_remove(arg[1])
            elif arg[0] == 'due' and len(arg) == 3:
                self._do_milestone_set_due(arg[1], arg[2])
            elif arg[0] == 'completed' and len(arg) == 3:
                self._do_milestone_set_completed(arg[1], arg[2])
            else:
                self.do_help('milestone')
        except Exception, e:
            print 'Command %s failed:' % arg[0], e

    def _do_milestone_list(self):
        data = []
        self.db_open()
        for m in Milestone.select(self.__env, include_completed=True):
            data.append((m.name, m.due and time.strftime('%c', time.localtime(m.due)),
                         m.completed and time.strftime('%c', time.localtime(m.completed))))
        self.print_listing(['Name', 'Due', 'Completed'], data)

    def _do_milestone_rename(self, name, newname):
        self.db_open()
        milestone = Milestone(self.__env, None, name)
        milestone.name = newname
        milestone.update()

    def _do_milestone_add(self, name):
        self.db_open()
        milestone = Milestone(self.__env, None)
        milestone.name = name
        milestone.insert()

    def _do_milestone_remove(self, name):
        self.db_open()
        milestone = Milestone(self.__env, None, name)
        milestone.delete()

    def _do_milestone_set_due(self, name, t):
        self.db_open()
        milestone = Milestone(self.__env, None, name)
        milestone.due = self._parse_datetime(t)
        milestone.update()

    def _do_milestone_set_completed(self, name, t):
        self.db_open()
        milestone = Milestone(self.__env, None, name)
        milestone.completed = self._parse_datetime(t)
        milestone.update()

    ## Version
    _help_version = [('version list', 'Show versions'),
                       ('version add <name> [time]', 'Add version'),
                       ('version rename <name> <newname>',
                        'Rename version'),
                       ('version time <name> <time>',
                        'Set version date (Format: "%s" or "now")'
                        % util.get_date_format_hint()),
                       ('version remove <name>', 'Remove version')]

    def complete_version (self, text, line, begidx, endidx):
        if begidx in [13, 15]:
            comp = self.get_version_list ()
        elif begidx < 13:
            comp = ['list','add','rename','time','remove']
        return self.word_complete(text, comp)

    def do_version(self, line):
        arg = self.arg_tokenize(line)
        try:
            if arg[0]  == 'list':
                self._do_version_list()
            elif arg[0] == 'add' and len(arg) in [2,3]:
                self._do_version_add(arg[1])
                if len(arg) == 3:
                    self._do_version_time(arg[1], arg[2])
            elif arg[0] == 'rename' and len(arg) == 3:
                self._do_version_rename(arg[1], arg[2])
            elif arg[0] == 'time' and len(arg) == 3:
                self._do_version_time(arg[1], arg[2])
            elif arg[0] == 'remove' and len(arg) == 2:
                self._do_version_remove(arg[1])
            else:
                self.do_help('version')
        except Exception, e:
            print 'Command %s failed:' % arg[0], e

    def _do_version_list(self):
        data = self.db_execsql("SELECT name,time FROM version ORDER BY time,name")
        data = map(lambda x: (x[0], x[1] and time.strftime('%c', time.localtime(x[1]))), data)
        self.print_listing(['Name', 'Time'], data)

    def _do_version_rename(self, name, newname):
        d = {'name':name, 'newname':newname}
        data = self.db_execsql("SELECT name FROM version" 
                               " WHERE name='%(name)s'" % d)
        if not data:
            raise Exception, "No such version '%s'" % name
        data = self.db_execsql("UPDATE version SET name='%(newname)s'" 
                               " WHERE name='%(name)s'" % d)

    def _do_version_add(self, name):
        self.db_execsql("INSERT INTO version (name, time) "
                        "VALUES('%(name)s', 0)" % {'name':name})

    def _do_version_remove(self, name):
        d = {'name':name}
        data = self.db_execsql("SELECT name FROM version" 
                               " WHERE name='%(name)s'" % d)
        if not data:
            raise Exception, "No such version '%s'" % name
        data = self.db_execsql("DELETE FROM version" 
                               " WHERE name='%(name)s'" % d)

    def _do_version_time(self, name, t):
        d = {'name':name}
        data = self.db_execsql("SELECT name FROM version" 
                               " WHERE name='%(name)s'" % d)
        if not data:
            raise Exception, "No such version '%s'" % name
        seconds = self._parse_datetime(t)
        if seconds != None:
            data = self.db_execsql("UPDATE version SET time='%s'" 
                                   " WHERE name='%s'" % (seconds, name))

    _help_upgrade = [('upgrade', 'Upgrade database to current version')]
    def do_upgrade(self, line):
        arg = self.arg_tokenize(line)
        do_backup = 1
        if arg[0] in ['-b', '--no-backup']:
            do_backup = 0
        self.db_open()
        try:
            curr = self.__env.get_version()
            latest = trac.db_default.db_version
            if  curr < latest:
                print "Upgrade: Upgrading %s to db version %i" % (self.envname, latest)
                if do_backup:
                    print "Upgrade: Backup of old database saved in " \
                          "%s/db/trac.db.%i.bak" % (self.envname, curr)
                else:
                    print "Upgrade: Backup disabled. Non-existent warranty voided."
                self.__env.upgrade(do_backup)
            else:
                print "Upgrade: Database is up to date, no upgrade necessary."
        except Exception, e:
            print "Upgrade failed: ",e

    _help_hotcopy = [('hotcopy <backupdir>', 'Make a hot backup copy of an environment')]
    def do_hotcopy(self, line):
        arg = self.arg_tokenize(line)
        if arg[0]:
            dest = arg[0]
        else:
            self.do_help('hotcopy')
            return
        cnx=self.db_open()
        # Lock the database while copying files
        cnx.db.execute("BEGIN")
        import shutil
        print 'Hotcopying %s to %s ...' % (self.__env.path, dest),
        try:
            shutil.copytree(self.__env.path, dest, symlinks=1)
            print 'OK'
        except Exception, err:
            print err
        # Unlock database
        cnx.db.execute("ROLLBACK")

## ---------------------------------------------------------------------------

##
## Main
##

def run(*args):
    args = list(args)
    tracadm = TracAdmin()
    if len (args) > 0:
        if args[0] in ['-h','--help','help']:
            tracadm.docmd ("help")
        elif args[0] in ['-v','--version','about']:
            tracadm.docmd ("about")
        else:
            tracadm.env_set(os.path.abspath(args[0]))
            if len (args) > 1:
                s_args = ' '.join(["'%s'" % c for c in args[2:]])
                command = args[1] + ' ' +s_args
                tracadm.docmd(command)
            else:
                while 1:
                    tracadm.run()
    else:
        tracadm.docmd ("help")
