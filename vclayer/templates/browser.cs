<?cs set:html.stylesheet = 'css/browser.css' ?>
<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="<?cs var:browser.log_href ?>">Revision Log</a></li>
 </ul>
</div>

<div id="content" class="browser">
 <?cs call:browser_path_links(browser.path, browser) ?>

 <div id="jumprev">
  <form action="" method="get">
   <div>
    <label for="rev">View revision:</label>
    <input type="text" id="rev" name="rev" value="<?cs
      var:browser.revision?>" size="4" />
   </div>
  </form>
 </div>

 <?cs if:browser.is_dir ?>
  <table class="listing" id="dirlist">
   <thead>
    <tr>
     <th class="name<?cs if:browser.order == 'name' ?> <?cs if:browser.desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
      <a title="Sort by name<?cs if:browser.order == 'name' && !browser.desc ?> (descending)<?cs /if ?>"
         href="?order=name<?cs if:browser.order == 'name' && !browser.desc ?>&desc=1<?cs /if ?>">Name</a>
     </th>
     <th class="rev">Rev</th>
     <th class="age<?cs if:browser.order == 'date' ?> <?cs if:browser.desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
      <a title="Sort by age<?cs if:browser.order == 'date' && !browser.desc ?> (descending)<?cs /if ?>"
         href="?order=date<?cs if:browser.order == 'date' && !browser.desc ?>&desc=1<?cs /if ?>">Age</a>
     </th>
     <th class="change">Last Change</th>
    </tr>
   </thead>
   <tbody>
    <?cs if:len(links.up) != "/" ?>
     <tr class="even">
      <td class="name" colspan="4">
       <a class="parent" title="Parent Directory" href="<?cs
         var:links.up.0.href ?>">../</a>
      </td>
     </tr>
    <?cs /if ?>
    <?cs each:item = browser.items ?>
     <?cs set:change = browser.changes[item.rev] ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="name"><?cs
       if:item.is_dir ?><?cs
        if:item.permission ?>
         <a class="dir" title="Browse Directory" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="dir" title="Access Denied" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       else ?><?cs
        if:item.permission != '' ?>    
         <a class="file" title="View File" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="file" title="Access Denied" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       /if ?>
      </td>
      <td class="rev"><?cs if:item.permission != '' ?><a title="View Revision Log" href="<?cs
        var:item.log_href ?>"><?cs var:item.rev ?></a><?cs else ?><?cs var:item.rev ?><?cs /if ?></td>
      <td class="age"><span title="<?cs var:item.date ?>"><?cs
        var:browser.changes[item.rev].age ?></span></td>
      <td class="change">
       <span class="author"><?cs var:browser.changes[item.rev].author ?>:</span>
       <span class="change"><?cs var:browser.changes[item.rev].message ?></span>
      </td>
     </tr>
    <?cs /each ?>
   </tbody>
  </table>
 <?cs else ?>
  <table id="info" summary="Revision info">
   <tr>
    <th scope="row">
     Revision <a href="<?cs var:file.changeset_href ?>"><?cs var:file.rev ?></a>
     (checked in by <?cs var:file.author ?>, <?cs var:file.age ?> ago)
    </th>
    <td class="message"><?cs var:file.message ?></td>
   </tr>
  </table>
  <div id="preview">
   <?cs if:file.preview ?>
    <?cs var:file.preview ?>
   <?cs elif:file.max_file_size_reached ?>
    <strong>HTML preview not available</strong>, since file-size exceeds
    <?cs var:file.max_file_size  ?> bytes.
    Try <a href="<?cs var:file.raw_href ?>">downloading</a> the file instead.
   <?cs else ?>
    <strong>HTML preview not available</strong>. To view, <a href="<?cs
    var:file.raw_href ?>">download</a> the file.
   <?cs /if ?>
  </div>
 <?cs /if ?>

 <div id="help">
  <strong>Note:</strong> See <a href="<?cs var:trac.href.wiki
  ?>/TracBrowser">TracBrowser</a> for help on using the browser.
 </div>

</div>
<?cs include:"footer.cs"?>
