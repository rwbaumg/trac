<?xml version="1.0"?>
<!-- RSS generated by Trac v<?cs var:trac.version ?> on <?cs var:trac.time ?> -->
<rss version="2.0">
    <channel>
      <?cs if:project.name.encoded ?>
        <title><?cs var:project.name.encoded ?>: Revisions of <?cs var:log.path ?></title>
      <?cs else ?>
        <title>Revisions of <?cs var:log.path ?></title>
      <?cs /if ?>
      <link><?cs var:base_host ?><?cs var:log.log_href ?></link>
      <description>Trac Log - Revisions of <?cs var:log.path ?></description>
      <language>en-us</language>
      <generator>Trac v<?cs var:trac.version ?></generator>
          <!--  XXX: author element requires email address in rss 2.0.
                maybe we should use the DC rdf stuff for metadata instead? -->
      <?cs each:item = log.items ?>
       <item>
         <author><?cs var: var:log.changes[item.rev].author ?></author> 
         <pubDate><?cs var:$item.date ?></pubDate>
         <title>Revision <?cs var:item.rev ?>: <?cs var:log.changes[item.rev].shortlog ?></title>
         <link><?cs var:base_host ?><?cs var:item.changeset_href ?></link>
         <description><?cs var:log.changes[item.rev].message ?></description>
         <category>Report</category>
       </item>
      <?cs /each ?>
    </channel>
</rss>
