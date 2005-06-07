<?cs 
def:anydiff(new_path,new_rev,module_href) ?>
 <div id="anydiff"><?cs
  if:session.diff_base_path == new_path && session.diff_base_rev == new_rev ?>
   <em>This Path/Revision is the Base for Diff</em><?cs
  else ?><?cs
   if:session.diff_base_path ?>
    <form action="<?cs var:diff.href ?>" method="get">
     <input type="hidden" name="old_path" value="<?cs var:session.diff_base_path ?>" />
     <input type="hidden" name="old" value="<?cs var:session.diff_base_rev ?>" />
     <input type="hidden" name="new" value="<?cs var:new_rev ?>" />
     <div class="buttons">
      <input type="submit" name="diff" value="Diff" 
              title="Diff the current Path/Revision against the selected Base" />
     </div>
     <label for="diff">
      from <em><?cs var:session.diff_base_path ?></em> 
       in revision <em><?cs var:session.diff_base_rev ?></em>
     </label>
    </form>
    <form action="<?cs var:module_href ?>" method="get">
     <input type="hidden" name="diff" value="clear" />
     <div class="buttons">
      <input type="submit" value="Clear" 
       title="Clear the Base for Diff" />
     </div>
    </form><?cs
   /if ?>
   <form action="<?cs var:module_href ?>" method="get">
    <input type="hidden" name="rev" value="<?cs var:new_rev ?>" />
    <input type="hidden" name="diff" value="set" />
    <div class="buttons">
     <input type="submit" 
       value="Set<?cs if:!session.diff_base_path ?>  Base for Diff<?cs /if ?>"
      title="Select the current Path/Revision as the new Base for Diff" />
    </div>
   </form><?cs
  /if ?>
 </div><?cs
/def ?>
