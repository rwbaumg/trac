<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <h2>Navigation</h2><?cs
 with:links = chrome.links ?>
  <ul><?cs
   if:diff.chgset ?><?cs
    if:len(links.prev) ?>
     <li class="first<?cs if:!len(links.next) ?> last<?cs /if ?>">
     &larr; <a class="prev" href="<?cs var:links.prev.0.href ?>" title="<?cs
        var:links.prev.0.title ?>">Previous <?cs 
         if:diff.restricted ?>Change<?cs else ?>Changeset<?cs /if ?></a>
     </li><?cs
    /if ?><?cs
    if:len(links.next) ?>
     <li class="<?cs if:len(links.prev) ?>first <?cs /if ?>last">
      <a class="next" href="<?cs var:links.next.0.href ?>" title="<?cs
        var:links.next.0.title ?>">Next <?cs 
         if:diff.restricted ?>Change<?cs else ?>Changeset<?cs /if ?></a> &rarr;
     </li><?cs
    /if ?><?cs
   else ?>
    <li class="first"><a href="<?cs var:diff.reverse_href ?>">Reverse Diff</a></li><?cs
   /if ?>
  </ul><?cs
 /with ?>
</div>

<div id="content" class="changeset">
 <div id="title"><?cs
  if:diff.chgset ?><?cs
   if:diff.restricted ?>
    <h1>Changeset <a title="Show full changeset" href="<?cs var:diff.href.new_rev ?>">
      <?cs var:diff.new_rev ?></a> 
     for <a title="Show entry in browser" href="<?cs var:diff.href.new_path ?>">
      <?cs var:diff.new_path ?></a> 
    </h1><?cs
   else ?>
    <h1>Changeset <?cs var:diff.new_rev ?></h1><?cs
   /if ?><?cs
  else ?><?cs
    if:diff.restricted ?>
    <h1>Changes in <a title="Show entry in browser" href="<?cs var:diff.href.new_path ?>">
      <?cs var:diff.new_path ?></a>
     from revision <a title="Show full changeset" href="<?cs var:diff.href.old_rev ?>">
      <?cs var:diff.old_rev ?></a>
     to <a title="Show full changeset" href="<?cs var:diff.href.new_rev ?>">
      <?cs var:diff.new_rev ?></a>
    </h1><?cs
   else ?>
    <h1>Changes from <a title="Show entry in browser" href="<?cs var:diff.href.old_path ?>">
      <?cs var:diff.old_path ?></a> 
     at revision <a title="Show full changeset" href="<?cs var:diff.href.old_rev ?>">
      <?cs var:diff.old_rev ?></a>
     to <a title="Show entry in browser" href="<?cs var:diff.href.new_path ?>">
     <?cs var:diff.new_path ?></a> 
     at revision <a title="Show full changeset" href="<?cs var:diff.href.new_rev ?>">
     <?cs var:diff.new_rev ?></a>
    </h1><?cs
   /if ?><?cs
  /if ?>
 </div>

<?cs each:change = diff.changes ?><?cs
 if:len(change.diff) ?><?cs
  set:has_diffs = 1 ?><?cs
 /if ?><?cs
/each ?><?cs if:has_diffs || diff.options.ignoreblanklines 
  || diff.options.ignorecase || diff.options.ignorewhitespace ?>
<form method="post" id="prefs" action="">
 <div><?cs 
  if:!diff.chgset ?>
   <input type="hidden" name="old_path" value="<?cs var:diff.old_path ?>" />
   <input type="hidden" name="path" value="<?cs var:diff.new_path ?>" />
   <input type="hidden" name="old" value="<?cs var:diff.old_rev ?>" />
   <input type="hidden" name="new" value="<?cs var:diff.new_rev ?>" /><?cs
  /if ?>
  <label for="style">View differences</label>
  <select id="style" name="style">
   <option value="inline"<?cs
     if:diff.style == 'inline' ?> selected="selected"<?cs
     /if ?>>inline</option>
   <option value="sidebyside"<?cs
     if:diff.style == 'sidebyside' ?> selected="selected"<?cs
     /if ?>>side by side</option>
  </select>
  <div class="field">
   Show <input type="text" name="contextlines" id="contextlines" size="2"
     maxlength="3" value="<?cs var:diff.options.contextlines ?>" />
   <label for="contextlines">lines around each change</label>
  </div>
  <fieldset id="ignore">
   <legend>Ignore:</legend>
   <div class="field">
    <input type="checkbox" id="blanklines" name="ignoreblanklines"<?cs
      if:diff.options.ignoreblanklines ?> checked="checked"<?cs /if ?> />
    <label for="blanklines">Blank lines</label>
   </div>
   <div class="field">
    <input type="checkbox" id="case" name="ignorecase"<?cs
      if:diff.options.ignorecase ?> checked="checked"<?cs /if ?> />
    <label for="case">Case changes</label>
   </div>
   <div class="field">
    <input type="checkbox" id="whitespace" name="ignorewhitespace"<?cs
      if:diff.options.ignorewhitespace ?> checked="checked"<?cs /if ?> />
    <label for="whitespace">White space changes</label>
   </div>
  </fieldset>
  <div class="buttons">
   <input type="submit" name="update" value="Update" />
  </div>
 </div>
</form><?cs /if ?>

<?cs def:node_change(item,cl,kind) ?><?cs 
  set:ndiffs = len(item.diff) ?><?cs
  set:nprops = len(item.props) ?>
  <div class="<?cs var:cl ?>"></div><?cs 
  if:cl == "rem" ?>
   <a title="Show what was removed (rev. <?cs var:item.rev.old ?>)" href="<?cs
     var:item.browser_href.old ?>"><?cs var:item.path.old ?></a><?cs
  else ?>
   <a title="Show entry in browser" href="<?cs
     var:item.browser_href.new ?>"><?cs var:item.path.new ?></a><?cs
  /if ?>
  <span class="comment">(<?cs var:kind ?>)</span><?cs
  if:item.path.old && item.change == 'copy' || item.change == 'move' ?>
   <small><em>(<?cs var:kind ?> from <a href="<?cs
    var:item.browser_href.old ?>" title="Show original file (rev. <?cs
    var:item.rev.old ?>)"><?cs var:item.path.old ?></a>)</em></small><?cs
  /if ?><?cs
  if:$ndiffs + $nprops > #0 ?>
    (<a href="#file<?cs var:name(item) ?>" title="Show differences"><?cs
      if:$ndiffs > #0 ?><?cs var:ndiffs ?>&nbsp;diff<?cs if:$ndiffs > #1 ?>s<?cs /if ?><?cs 
      /if ?><?cs
      if:$ndiffs && $nprops ?>, <?cs /if ?><?cs 
      if:$nprops > #0 ?><?cs var:nprops ?>&nbsp;prop<?cs if:$nprops > #1 ?>s<?cs /if ?><?cs
      /if ?></a>)<?cs
  elif:cl == "mod" ?>
    (<a href="<?cs var:item.browser_href.old ?>"
        title="Show previous version in browser">previous</a>)<?cs
  /if ?>
<?cs /def ?>

<dl id="overview"><?cs
 if:diff.chgset ?>
 <dt class="time">Timestamp:</dt>
 <dd class="time"><?cs var:changeset.time ?></dd>
 <dt class="author">Author:</dt>
 <dd class="author"><?cs var:changeset.author ?></dd>
 <dt class="message">Message:</dt>
 <dd class="message" id="searchable"><?cs
  alt:changeset.message ?>&nbsp;<?cs /alt ?></dd><?cs
 /if ?>
 <dt class="files"><?cs 
  if:len(diff.changes) > #0 ?>
   Files:<?cs
  else ?>
   (None)<?cs
  /if ?>
 </dt>
 <dd class="files">
  <ul><?cs each:item = diff.changes ?>
   <li><?cs
    if:item.change == 'add' ?><?cs
     call:node_change(item, 'add', 'added') ?><?cs
    elif:item.change == 'delete' ?><?cs
     call:node_change(item, 'rem', 'deleted') ?><?cs
    elif:item.change == 'copy' ?><?cs
     call:node_change(item, 'cp', 'copied') ?><?cs
    elif:item.change == 'move' ?><?cs
     call:node_change(item, 'mv', 'moved') ?><?cs
    elif:item.change == 'edit' ?><?cs
     call:node_change(item, 'mod', 'modified') ?><?cs
    /if ?>
   </li>
  <?cs /each ?></ul>
 </dd>
</dl>

<div class="diff">
 <div id="legend">
  <h3>Legend:</h3>
  <dl>
   <dt class="unmod"></dt><dd>Unmodified</dd>
   <dt class="add"></dt><dd>Added</dd>
   <dt class="rem"></dt><dd>Removed</dd>
   <dt class="mod"></dt><dd>Modified</dd>
   <dt class="cp"></dt><dd>Copied</dd>
   <dt class="mv"></dt><dd>Moved</dd>
  </dl>
 </div>
 <ul class="entries"><?cs
 each:item = diff.changes ?><?cs
  if:len(item.diff) || len(item.props) ?><li class="entry" id="file<?cs
   var:name(item) ?>"><h2><a href="<?cs
   var:item.browser_href.new ?>" title="Show new revision <?cs
   var:item.rev.new ?> of this file in browser"><?cs
   var:item.path.new ?></a></h2><?cs
   if:len(item.props) ?><ul class="props"><?cs
    each:prop = item.props ?><li>Property <strong><?cs
     var:name(prop) ?></strong> <?cs
     if:prop.old && prop.new ?>changed from <?cs
     elif:!prop.old ?>set<?cs
     else ?>deleted<?cs
     /if ?><?cs
     if:prop.old && prop.new ?><em><tt><?cs var:prop.old ?></tt></em><?cs /if ?><?cs
     if:prop.new ?> to <em><tt><?cs var:prop.new ?></tt></em><?cs /if ?></li><?cs
    /each ?></ul><?cs
   /if ?><?cs
   if:len(item.diff) ?><table class="<?cs
    var:diff.style ?>" summary="Differences" cellspacing="0"><?cs
    if:diff.style == 'sidebyside' ?>
     <colgroup class="l"><col class="lineno" /><col class="content" /></colgroup>
     <colgroup class="r"><col class="lineno" /><col class="content" /></colgroup>
     <thead><tr>
      <th colspan="2"><a href="<?cs
       var:item.browser_href.old ?>" title="Show old rev. <?cs
       var:item.rev.old ?> of <?cs var:item.path.old ?>">Revision <?cs
       var:item.rev.old ?></a></th>
      <th colspan="2"><a href="<?cs
       var:item.browser_href.new ?>" title="Show new rev. <?cs
       var:item.rev.new ?> of <?cs var:item.path.new ?>">Revision <?cs
       var:item.rev.new ?></a></th>
      </tr>
     </thead><?cs
     each:change = item.diff ?><tbody><?cs
      call:diff_display(change, diff.style) ?></tbody><?cs
      if:name(change) < len(item.diff) - 1 ?><tbody class="skipped"><tr>
       <th>&hellip;</th><td>&nbsp;</td><th>&hellip;</th><td>&nbsp;</td>
      </tr></tbody><?cs /if ?><?cs
     /each ?><?cs
    else ?>
     <colgroup><col class="lineno" /><col class="lineno" /><col class="content" /></colgroup>
     <thead><tr>
      <th title="Revision <?cs var:item.rev.old ?>"><a href="<?cs
       var:item.browser_href.old ?>" title="Show old version of <?cs
       var:item.path.old ?>">r<?cs var:item.rev.old ?></a></th>
      <th title="Revision <?cs var:item.rev.new ?>"><a href="<?cs
       var:item.browser_href.new ?>" title="Show new version of <?cs
       var:item.path.new ?>">r<?cs var:item.rev.new ?></a></th>
      <th>&nbsp;</th></tr>
     </thead><?cs
     each:change = item.diff ?><?cs
      call:diff_display(change, diff.style) ?><?cs
      if:name(change) < len(item.diff) - 1 ?><tbody class="skipped"><tr>
       <th>&hellip;</th><th>&hellip;</th><td>&nbsp;</td>
      </tr></tbody><?cs /if ?><?cs
     /each ?><?cs
    /if ?></table><?cs
   /if ?></li><?cs
  /if ?><?cs
 /each ?></ul>
</div>

</div>
<?cs include "footer.cs"?>
