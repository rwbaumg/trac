<?xml version="1.0"?>
<rss version="2.0">
 <?cs set:base_url = HTTP.Protocol + '://' + HTTP.Host ?>
 <channel><?cs
  if:project.name.encoded ?>
   <title><?cs var:project.name.encoded ?>: Ticket Query</title><?cs
  else ?>
   <title>Ticket Query</title><?cs
  /if ?>
  <link><?cs var:base_url ?><?cs var:trac.href.query ?></link><?cs
  if:project.descr ?>
   <description><?cs var:project.descr ?></description><?cs
  /if ?>
  <language>en-us</language>
  <image>
   <title><?cs var:project.name.encoded ?></title>
   <url><?cs
    if:!header_logo.src_abs ?><?cs var:base_url ?><?cs
    /if ?><?cs
    var:header_logo.src ?></url>
   <link><?cs var:base_url ?><?cs var:$trac.href.timeline ?></link><?cs
   if:header_logo.width ?>
    <width><?cs var:header_logo.width ?></width><?cs
   /if ?><?cs
   if:header_logo.height ?>
    <height><?cs var:header_logo.height ?></height><?cs
   /if ?>
  </image>
  <generator>Trac v<?cs var:trac.version ?></generator><?cs
  each:result = query.results ?>
   <item>
    <link><?cs var:base_url + result.href ?></link>
    <guid isPermaLink="true"><?cs var:base_url + result.href ?></guid>
    <title><?cs var:'#' + result.id + ': ' + result.summary ?></title><?cs
    if:result.created_gmt ?>
     <pubDate><?cs var:result.created_gmt ?></pubDate><?cs
    /if ?><?cs
    if:result.reporter ?>
     <author><?cs var:result.reporter ?></author><?cs
    /if ?>
    <description><?cs var:result.description ?></description>
    <category>Tickets</category>
    <comments><?cs var:base_url + result.href ?>#changelog</comments>
   </item><?cs
  /each ?>
 </channel>
</rss>
