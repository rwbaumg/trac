<?cs set:html.stylesheet = 'css/report.css' ?>
<?cs include:"header.cs" ?>
<?cs include:"macros.cs" ?>

<div id="ctxtnav" class="nav">
 <ul><?cs if:trac.acl.REPORT_VIEW ?>
  <li class="last"><a href="<?cs
    var:trac.href.report ?>">Available Reports</a></li>
 <?cs /if ?></ul>
</div>

<div id="content" class="query">
 <h1><?cs var:title ?></h1>

<script type="text/javascript" src="<?cs
  var:htdocs_location ?>query.js" defer="defer"></script>
<form id="query" method="post" action="<?cs var:cgi_location ?>">
 <fieldset id="filters">
  <legend>Filters</legend>
  <?cs def:checkbox_checked(constraint, option) ?><?cs
   each:value = constraint ?><?cs
    if:value == option ?> checked="checked"<?cs
    /if ?><?cs
   /each ?><?cs
  /def ?><?cs
  def:option_selected(constraint, option) ?><?cs
   each:value = constraint ?><?cs
    if:value == option ?> selected="selected"<?cs
    /if ?><?cs
   /each ?><?cs
  /def ?>
  <table><?cs each:property = ticket.properties ?><?cs
   each:constraint = query.constraints ?><?cs
    if:property.name == name(constraint) ?>
     <tr class="<?cs var:property.name ?>">
      <th scope="row"><label><?cs var:property.label ?></label></th><?cs
      if:property.type != "radio" ?>
       <td class="mode">
        <select name="<?cs var:property.name ?>_mode"><?cs
         each:mode = query.modes[property.type] ?>
          <option value="<?cs var:mode.value ?>"<?cs
           if:mode.value == constraint.mode ?> selected="selected"<?cs
           /if ?>><?cs var:mode.name ?></option><?cs
         /each ?>
       </td><?cs
      /if ?>
      <td class="filter"<?cs if:property.type == "radio" ?> colspan="2"<?cs /if ?>><?cs
       if:property.type == "select" ?>
        <select name="<?cs var:name(constraint) ?>"><option></option><?cs
        each:option = property.options ?>
         <option<?cs call:option_selected(constraint, option) ?>><?cs
           var:option ?></option><?cs
        /each ?></select><?cs
       elif:property.type == "radio" ?><?cs
        each:option = property.options ?>
         <input type="checkbox" id="<?cs var:property.name ?>_<?cs
           var:option ?>" name="<?cs var:property.name ?>" value="<?cs
           var:option ?>"<?cs call:checkbox_checked(constraint, option) ?> />
         <label for="<?cs var:property.name ?>_<?cs var:option ?>"><?cs
           var:option ?></label><?cs
        /each ?><?cs
       elif:property.type == "text" ?>
        <input type="text" name="<?cs var:property.name ?>" value="<?cs
          var:constraint.0 ?>" size="42" /><?cs
       /if ?>
      </td>
      <td class="actions">
       <input type="button" name="rm_filter_<?cs
         var:property.name ?>" value="-" onclick="removeFilter(this, '<?cs
         var:property.name ?>'); return false" />
      </td>
     </tr><?cs /if ?><?cs
    /each ?><?cs
   /each ?>
   <tr>
    <td class="actions" colspan="4" style="text-align: right">
     <label for="add_filter">Add filter</label>
     <select name="add_filter" id="add_filter" onchange="addFilter(this)">
      <option></option><?cs
      each:property = ticket.properties ?>
       <option value="<?cs var:property.name ?>"<?cs
         if:len(query.constraints[property.name]) != 0 ?> disabled="disabled"<?cs
         /if ?>><?cs var:property.label ?></option><?cs
      /each ?>	
     </select>
     <noscript><input type="submit" name="add" value="+" /></noscript>
    </td>
   </tr>
  </table>
 </fieldset>
 <div class="buttons">
  <input type="hidden" name="mode" value="query" />
  <input type="hidden" name="order" value="<?cs var:query.order ?>" />
  <?cs if:query.desc ?><input type="hidden" name="desc" value="1" /><?cs /if ?>
  <input type="submit" name="update" value="Update" />
 </div>
</form>

<p id="nummatches"><?cs alt:len(query.results) ?>No<?cs /alt ?> ticket<?cs if:len(query.results) != 1 ?>s<?cs
/if ?> matched this query.</p>

<?cs if:len(query.results) ?>
 <table id="tktlist" class="listing">
  <thead><tr><?cs each:header = query.headers ?><?cs
   if:name(header) == 0 ?><th class="ticket<?cs
    if:header.order ?> <?cs var:header.order ?><?cs /if ?>">
    <a href="<?cs var:header.href ?>" title="Sort by ID (<?cs
      if:header.order == 'asc' ?>descending<?cs
      else ?>ascending<?cs /if ?>)">Ticket</a>
    </th><?cs
   else ?>
    <th<?cs if:header.order ?> class="<?cs var:header.order ?>"<?cs /if ?>>
     <a href="<?cs var:header.href ?>" title="Sort by <?cs
       var:header.name ?> (<?cs if:header.order == 'asc' ?>descending<?cs
       else ?>ascending<?cs /if ?>)"><?cs var:header.name ?></a>
    </th><?cs
   /if ?>
  <?cs /each ?></tr></thead>
  <tbody>
   <?cs each:result = query.results ?><tr class="<?cs
     if:name(result) % 2 ?>odd<?cs else ?>even<?cs /if ?> <?cs
     var:result.priority ?>">
    <?cs each:header = query.headers ?><?cs
     if:name(header) == 0 ?>
      <td class="ticket"><a href="<?cs var:result.href ?>" title="View ticket"><?cs
        var:result.id ?></a></td><?cs
     else ?>
      <td><?cs if:header.name == 'summary' ?>
       <a href="<?cs var:result.href ?>" title="View ticket"><?cs
         var:result[header.name] ?></a><?cs
      else ?>
       <?cs var:result[header.name] ?><?cs
      /if ?>
      </td><?cs
     /if ?>
    <?cs /each ?>
   </tr><?cs /each ?>
  </tbody>
 </table>
<?cs /if ?>

<div id="help">
 <strong>Note:</strong> See <a href="<?cs var:$trac.href.wiki ?>/TracQuery">TracQuery</a> 
 for help on using queries.
</div>

<script type="text/javascript" defer="defer"><?cs set:idx = 0 ?>
 var properties={<?cs each:property = ticket.properties ?><?cs
  var:property.name ?>:{type:"<?cs var:property.type ?>",label:"<?cs
  var:property.label ?>",options:[<?cs
   each:option = property.options ?>"<?cs var:option ?>"<?cs
    if:name(option) < len(property.options) -1 ?>,<?cs /if ?><?cs
   /each ?>]}<?cs
  set:idx = idx + 1 ?><?cs if:idx < len(ticket.properties) ?>,<?cs /if ?><?cs
 /each ?>};<?cs set:idx = 0 ?>
 var modes = {<?cs each:type = query.modes ?><?cs var:name(type) ?>:[<?cs
  each:mode = type ?>{text:"<?cs var:mode.name ?>",value:"<?cs var:mode.value ?>"}<?cs
   if:name(mode) < len(type) -1 ?>,<?cs /if ?><?cs
  /each ?>]<?cs
  set:idx = idx + 1 ?><?cs if:idx < len(query.modes) ?>,<?cs /if ?><?cs
 /each ?>};
</script>

</div>
<?cs include:"footer.cs" ?>
