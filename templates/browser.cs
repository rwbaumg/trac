<?cs include: "header.cs"?>
<div id="page-content">
 <div id="subheader-links">
 </div>
 <div id="main">
  <div id="main-content">
   <div id="browser-body">
    <h1 id="browser-rev">Revision <?cs var:browser.revision?></h1>

    <form id="browser-chgrev" action="<?cs var:browser_current_href ?>" method="get">
      <div>
        View rev:
        <input type="text" name="rev" value="<?cs var:browser.revision?>"
          size="4" />
        <input type="submit" value="View" />
      </div>
    </form> 

    <div id="browser-pathlinks">
      <?cs each:part=browser.path ?>
        <?cs if !#first ?><?cs set:first=1 ?><?cs else ?> / <?cs /if ?>
        <a href="<?cs var:part.url ?>"><?cs var:part?></a>
      <?cs /each ?>
    </div>

    <table id="browser-list" cellspacing="0" cellpadding="0">
      <tr class="browser-listhdr">
        <th>&nbsp;</th>
        <th>Name</th>
        <th>Size</th>
        <th>Rev</th>
        <th>Date</th>
      </tr>
      <?cs if $browser.path != "/" ?>
        <tr class="br-row-even">
          <td class="br-icon-col">
            <a href="<?cs var:browser.parent_href ?>">
              <img src="<?cs var:htdocs_location ?>/folder.png" 
                    width="16" height="16" alt="[parent]" />
            </a>
          </td>
          <td class="br-name-col">
            <a href="<?cs var:browser.parent_href ?>">..</a>
          </td>
          <td class="br-size-col">&nbsp;</td>
          <td class="br-rev-col">&nbsp;</td>
          <td class="br-date-col">&nbsp;</td>
        </tr>
      <?cs /if ?>
      <?cs set:idx = #0 ?>
      <?cs each:item = browser.items ?>
        <?cs if idx % #2 ?>
          <tr class="br-row-even">
        <?cs else ?>
          <tr class="br-row-odd">
        <?cs /if ?>
        <?cs if item.is_dir == #1 ?>
          <td class="br-icon-col">
            <a href="<?cs var:item.browser_href ?>">
              <img src="<?cs var:htdocs_location ?>/folder.png"
                    width="16" height="16" alt="[dir]" />
            </a>
          </td>
          <td class="br-name-col">
            <a href="<?cs var:item.browser_href ?>"><?cs var:item.name ?></a>
          </td>
        <?cs else ?>
          <td class="br-icon-col">
            <a href="<?cs var:item.log_href ?>">
              <img src="<?cs var:htdocs_location ?>/file.png"
                    width="16" height="16" alt="[file]" />
            </a>
          </td>
          <td class="br-name-col">
            <a href="<?cs var:item.log_href ?>"><?cs var:item.name ?></a>
          </td>
         <?cs /if ?>
         <td class="br-size-col">
           <?cs if item.size != #0 ?><?cs var:item.size ?><?cs /if ?>
         </td>
         <td class="br-rev-col">
           <?cs if item.is_dir == #1 ?>
             <?cs var:item.created_rev ?>
           <?cs else ?>
             <a href="<?cs var:item.rev_href ?>">
	       <?cs var:item.created_rev ?>
	     </a>
           <?cs /if ?>
         </td>
         <td class="br-date-col">
           <?cs var:item.date ?>
         </td>
       </tr>
       <?cs set:idx = idx + #1 ?>
     <?cs /each ?>
   </table>
  </div>
  <div id="main-sidebar">
  </div>

 </div>
</div>
</div>
<?cs include:"footer.cs"?>
