<?cs set:html.stylesheet = 'css/ticket.css' ?>
<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Ticket Navigation</h2>
 <ul><?cs
  call:backlinks("ticket", ticket.id) ?><?cs
  if:len(links.prev) ?>
   <li class="first<?cs if:!len(links.up) && !len(links.next) ?> last<?cs /if ?>">
    &larr; <a href="<?cs var:links.prev.0.href ?>" title="<?cs
      var:links.prev.0.title ?>">Previous Ticket</a>
   </li><?cs
  /if ?><?cs
  if:len(links.up) ?>
   <li class="<?cs if:!len(links.prev) ?>first<?cs /if ?><?cs
                   if:!len(links.next) ?> last<?cs /if ?>">
    <a href="<?cs var:links.up.0.href ?>" title="<?cs
      var:links.up.0.title ?>">Back to Query</a>
   </li><?cs
  /if ?><?cs
  if:len(links.next) ?>
   <li class="<?cs if:!len(links.prev) && !len(links.up) ?>first <?cs /if ?>last">
    <a href="<?cs var:links.next.0.href ?>" title="<?cs
      var:links.next.0.title ?>">Next Ticket</a> &rarr;
   </li><?cs
  /if ?>
 </ul>
</div>

<div id="content" class="ticket">

 <h1>Ticket #<?cs var:ticket.id ?> <?cs
 if:ticket.status == 'closed' ?>(Closed: <?cs var:ticket.resolution ?>)<?cs
 elif:ticket.status != 'new' ?>(<?cs var:ticket.status ?>)<?cs
 /if ?></h1>

 <div id="searchable">
 <?cs def:ticketprop(label, name, value, fullrow) ?>
  <th id="h_<?cs var:name ?>"><?cs var:$label ?>:</th>
  <td headers="h_<?cs var:name ?>"<?cs if:fullrow ?> colspan="3"<?cs /if ?>><?cs
   if:$value ?><?cs var:$value ?><?cs else ?>&nbsp;<?cs
   /if ?></td><?cs if numprops % #2 && !$last_prop || fullrow ?>
 </tr><tr><?cs /if ?><?cs set numprops = $numprops + #1 - fullrow ?><?cs
 /def ?>

<div id="ticket">
 <div class="date">
  <p title="<?cs var:ticket.opened ?>">Opened <?cs var:ticket.opened_delta ?> ago</p><?cs
  if:ticket.lastmod ?>
   <p title="<?cs var:ticket.lastmod ?>">Last modified <?cs var:ticket.lastmod_delta ?> ago</p>
  <?cs /if ?>
 </div>
 <h2><?cs var:ticket.summary ?></h2>
 <table><tr><?cs
  call:ticketprop("Priority", "priority", ticket.priority, 0) ?><?cs
  call:ticketprop("Reporter", "reporter", ticket.reporter, 0) ?><?cs
  call:ticketprop("Severity", "severity", ticket.severity, 0) ?><?cs
  if ticket.status == "assigned"?><?cs
   call:ticketprop("Assigned to", "assignee", ticket.owner + " (accepted)", 0) ?><?cs
  else ?><?cs
   call:ticketprop("Assigned to", "assignee", ticket.owner, 0) ?><?cs
  /if ?><?cs
  call:ticketprop("Component", "component", ticket.component, 0) ?><?cs
  call:ticketprop("Status", "status", ticket.status, 0) ?><?cs
  call:ticketprop("Version", "version", ticket.version, 0) ?><?cs
  call:ticketprop("Resolution", "resolution", ticket.resolution, 0) ?><?cs
  call:ticketprop("Milestone", "milestone", ticket.milestone, 0) ?><?cs
  set:last_prop = #1 ?><?cs
  call:ticketprop("Keywords", "keywords", ticket.keywords, 0) ?><?cs
  set:last_prop = #0 ?>
 </tr></table><?cs if ticket.custom.0.name ?>
 <table><tr><?cs each:prop = ticket.custom ?><?cs
   if:name(prop) == len(ticket.custom) - 1 ?><?cs set:last_prop = #1 ?><?cs
   /if ?><?cs
   if:prop.type == "textarea" ?><?cs
    call:ticketprop(prop.label, prop.name, prop.value, 1) ?><?cs
   else ?><?cs
    call:ticketprop(prop.label, prop.name, prop.value, 0) ?><?cs
   /if?><?cs
  /each ?>
  </tr></table><?cs /if ?>
 <?cs if:ticket.description ?><div class="description">
  <?cs var:ticket.description.formatted ?>
 </div><?cs /if ?>

</div>

<?cs if:ticket.depends_on.me + ticket.depends_on.others > #0 ?>
<h2>Ticket Dependencies:</h2>
<p class="dependencies"><?cs
 if ticket.depends_on.others > #0 ?>
  This ticket 
  <a href="<?cs var:trac.href.xref ?>/ticket/<?cs var:ticket.id ?>#outgoing-relations"
     title="See outgoing &laquo;depends-on&raquo; relations">
   <?cs call:relation("depends-on") ?></a> <?cs var:ticket.depends_on.others ?> 
   <?cs call:plural(ticket.depends_on.others, "ticket", "tickets") ?>.<?cs
 /if ?><?cs
 if ticket.depends_on.me > #0 ?><?cs
  call:plural($ticket.depends_on.me,
   "There is one ticket",
   "There are " + $ticket.depends_on.me + " tickets ") ?>
   which <a href="<?cs var:trac.href.xref ?>/ticket/<?cs var:ticket.id ?>#incoming-relations"
            title="See incoming &laquo;depends-on&raquo; relations">
    <?cs call:relation("depends-on") ?></a> this ticket.<?cs
 /if ?>
</p>
<?cs /if ?>

<?cs if:ticket.attach_href || len(ticket.attachments) ?>
<h2>Attachments</h2><?cs
 if ticket.attachments.0.name ?><div id="attachments">
  <ul class="attachments"><?cs each:a = ticket.attachments ?>
   <li><a href="<?cs var:a.href ?>" title="View attachment"><?cs
   var:a.name ?></a> (<?cs var:a.size ?>) - <?cs
   if:a.descr ?><q><?cs var:a.descr ?></q>,<?cs
   /if ?> added by <em><?cs
   var:a.author ?></em> on <em><?cs
   var:a.time ?></em>.</li><?cs
  /each ?></ul><?cs
 /if ?><?cs
 if:ticket.attach_href ?>
  <form method="get" action="<?cs var:ticket.attach_href ?>"><div>
   <input type="hidden" name="action" value="new" />
   <input type="submit" value="Attach File" />
  </div></form><?cs
 /if ?><?cs if ticket.attachments.0.name ?></div><?cs /if ?>
<?cs /if ?>

<?cs if:len(ticket.changes) ?><h2>Changelog</h2>
<div id="changelog"><?cs
 each:change = ticket.changes ?>
  <h3 id="change_<?cs var:name(change) ?>" class="change"><?cs
   var:change.date ?>: Modified by <?cs var:change.author ?></h3><?cs
  if:len(change.fields) ?>
   <ul class="changes"><?cs
   each:field = change.fields ?>
    <li><strong><?cs var:name(field) ?></strong> <?cs
    if:name(field) == 'attachment' ?><em><?cs var:field.new ?></em> added<?cs
    elif:field.old && field.new ?>changed from <em><?cs
     var:field.old ?></em> to <em><?cs var:field.new ?></em><?cs
    elif:!field.old && field.new ?>set to <em><?cs var:field.new ?></em><?cs
    elif:field.old && !field.new ?>deleted<?cs
    else ?>changed<?cs
    /if ?>.</li>
    <?cs
   /each ?>
   </ul><?cs
  /if ?>
  <div class="comment"><?cs var:change.comment ?></div><?cs
 /each ?></div><?cs
/if ?>

<?cs if $trac.acl.TICKET_MODIFY ?>
<form action="<?cs var:cgi_location ?>#preview" method="post">
 <hr />
 <h3><a name="edit" onfocus="document.getElementById('comment').focus()">Add/Change #<?cs
   var:ticket.id ?> (<?cs var:ticket.summary ?>)</a></h3>
 <div class="field">
  <input type="hidden" name="mode" value="ticket" />
  <input type="hidden" name="id"   value="<?cs var:ticket.id ?>" />
  <label for="author">Your email or username:</label><br />
  <input type="text" id="author" name="author" size="40"
    value="<?cs var:ticket.reporter_id ?>" /><br />
 </div>
 <div class="field">
  <fieldset class="iefix">
   <label for="comment">Comment (you may use <a tabindex="42" href="<?cs
     var:$trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label><br />
   <p><textarea id="comment" name="comment" class="wikitext" rows="10" cols="78"><?cs
     var:ticket.comment ?></textarea></p>
  </fieldset><?cs
  if ticket.comment_preview ?>
   <fieldset id="preview">
    <legend>Comment Preview</legend>
    <?cs var:ticket.comment_preview ?>
   </fieldset><?cs
  /if ?>
 </div>

 <fieldset id="properties">
  <legend>Change Properties</legend>
  <div class="main">
   <label for="summary">Summary:</label>
   <input id="summary" type="text" name="summary" size="70" value="<?cs
     var:ticket.summary ?>" /><?cs
   if $trac.acl.TICKET_ADMIN ?>
    <br />
    <label for="description">Description:</label>
    <div style="float: left">
     <textarea id="description" name="description" class="wikitext" rows="10" cols="68"><?cs
       var:ticket.description ?></textarea>
    </div>
    <br style="clear: left" />
    <label for="reporter">Reporter:</label>
    <input id="reporter" type="text" name="reporter" size="70"
           value="<?cs var:ticket.reporter ?>" /><?cs
   /if ?>
  </div>
  <div class="col1">
   <label for="component">Component:</label><?cs
   call:hdf_select(ticket.components, "component", ticket.component, 0) ?>
   <br />
   <label for="version">Version:</label><?cs
   call:hdf_select(ticket.versions, "version", ticket.version, 0) ?>
   <br />
   <label for="severity">Severity:</label><?cs
   call:hdf_select(enums.severity, "severity", ticket.severity, 0) ?>
   <br />
   <label for="keywords">Keywords:</label>
   <input type="text" id="keywords" name="keywords" size="20"
       value="<?cs var:ticket.keywords ?>" />
  </div>
  <div class="col2">
   <label for="priority">Priority:</label><?cs
   call:hdf_select(enums.priority, "priority", ticket.priority, 0) ?><br />
   <label for="milestone">Milestone:</label><?cs
   call:hdf_select(ticket.milestones, "milestone", ticket.milestone, 1) ?><br />
   <label for="owner">Assigned to:</label>
   <input type="text" id="owner" name="owner" size="20" value="<?cs
     var:ticket.owner ?>" disabled="disabled" /><br />
   <label for="cc">Cc:</label>
   <input type="text" id="cc" name="cc" size="30" value="<?cs var:ticket.cc ?>" /><br />
   <label for="depends_on"><?cs call:relation("depends-on") ?>:</label>
   <textarea id="depends_on" name="depends_on" cols="30" rows="2"><?cs 
     var:ticket.depends_on ?></textarea>
  </div>
  <?cs if:len(ticket.custom) ?><div class="custom">
   <?cs call:ticket_custom_props(ticket) ?>
  </div><?cs /if ?>
 </fieldset>

 <fieldset id="action">
  <legend>Action</legend><?cs
  if:!ticket.action ?><?cs set:ticket.action = 'leave' ?><?cs
  /if ?><?cs
  def:action_radio(id) ?>
   <input type="radio" id="<?cs var:id ?>" name="action" value="<?cs
     var:id ?>"<?cs if:$ticket.action == $id ?> checked="checked"<?cs
     /if ?> /><?cs
  /def ?>
  <?cs call:action_radio('leave') ?>
  <label for="leave">leave as <?cs var:ticket.status ?></label><br /><?cs
  if $ticket.status == "new" ?>
   <?cs call:action_radio('accept') ?>
   <label for="accept">accept ticket</label><br /><?cs
  /if ?><?cs
  if $ticket.status == "closed" ?>
   <?cs call:action_radio('reopen') ?>
   <label for="reopen">reopen ticket</label><br /><?cs
  /if ?><?cs
  if $ticket.status == "new" || $ticket.status == "assigned" || $ticket.status == "reopened" ?><?cs
   if $ticket.can_be_closed ?>
    <?cs call:action_radio('resolve') ?>
    <label for="resolve">resolve</label>
    <label for="resolve_resolution">as:</label>
    <?cs call:hdf_select(enums.resolution, "resolve_resolution", args.resolve_resolution, 0) ?><br /><?cs
   else ?>
	<em>(you must resolve the dependent tickets before you can resolve this one)</em><br /><?cs 
   /if ?>
   <?cs call:action_radio('reassign') ?>
   <label for="reassign">reassign</label>
   <label>to:<?cs
   if:len(ticket.users) ?><?cs
    call:hdf_select(ticket.users, "reassign_owner", ticket.reassign_owner, 0) ?><?cs
   else ?>
    <input type="text" id="reassign_owner" name="reassign_owner" size="40" value="<?cs
      var:ticket.reassign_owner ?>" /><?cs
   /if ?></label><?cs
  /if ?><?cs
  if $ticket.status == "new" || $ticket.status == "assigned" || $ticket.status == "reopened" ?>
   <script type="text/javascript">
     var resolve = document.getElementById("resolve");
     var reassign = document.getElementById("reassign");
     var updateActionFields = function() {
       enableControl('resolve_resolution', resolve.checked);
       enableControl('reassign_owner', reassign.checked);
     };
     addEvent(window, 'load', updateActionFields);
     addEvent(document.getElementById("leave"), 'click', updateActionFields);<?cs
    if $ticket.status == "new" ?>
     addEvent(document.getElementById("accept"), 'click', updateActionFields);<?cs
    /if ?>
    addEvent(resolve, 'click', updateActionFields);
    addEvent(reassign, 'click', updateActionFields);
   </script><?cs
  /if ?>
 </fieldset>

 <script type="text/javascript" src="<?cs
   var:htdocs_location ?>js/wikitoolbar.js"></script>

 <div class="buttons">
  <input type="reset" value="Reset" />&nbsp;
  <input type="submit" name="preview" value="Preview" />&nbsp;
  <input type="submit" value="Submit changes" /> 
 </div>
</form>
<?cs /if ?>

 </div>
</div>
<?cs include "footer.cs"?>
