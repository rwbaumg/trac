// Generated by CoffeeScript 1.12.6
(function() {
  var $, captionedButton, deleteComment, deleteTicket;

  $ = jQuery;

  captionedButton = function(symbol, text) {
    if (ui.use_symbols) {
      return symbol;
    } else {
      return symbol + " " + text;
    }
  };

  deleteTicket = function() {
    return $("<form action=\"#\" method=\"get\">\n <div class=\"inlinebuttons\">\n  <input type=\"hidden\" name=\"action\" value=\"delete\">\n  <input type=\"submit\"\n         value=\"" + (captionedButton('–', _('Delete'))) + "\"\n         title=\"" + (_('Delete ticket')) + "\"\n         class=\"trac-delete\">\n </div>\n</form>");
  };

  deleteComment = function(c) {
    var cdate, cnum, ref;
    ref = c.id.substr(12).split('-'), cnum = ref[0], cdate = ref[1];
    return $("<form action=\"#\" method=\"get\">\n <div class=\"inlinebuttons\">\n  <input type=\"hidden\" name=\"action\" value=\"delete-comment\">\n  <input type=\"hidden\" name=\"cnum\" value=\"" + cnum + "\">\n  <input type=\"hidden\" name=\"cdate\" value=\"" + cdate + "\">\n  <input type=\"submit\"\n         value=\"" + (captionedButton('–', _('Delete'))) + "\"\n         title=\"" + (_('Delete comment %(num)s', {
      num: cnum
    })) + "\"\n         class=\"trac-delete\">\n </div>\n</form>");
  };

  $(document).ready(function() {
    $('#ticket .description h3').after(deleteTicket());
    return $('#changelog div.change').each(function() {
      return $('.trac-ticket-buttons', this).prepend(deleteComment(this));
    });
  });

}).call(this);
