function copy_link_into_clipboard(b) {
  var $temp = $("<input>");
  $(b).parent().append($temp);
  $temp.val($(b).data("url")).select();
  document.execCommand("copy");
  $temp.remove();
}

function add_binder_buttons() {
  var copy_button =
    '<button id="copy-{name}-link" ' +
    '                 title="Copy {name} link to clipboard" ' +
    '                 class="btn btn-default btn-sm navbar-btn" ' +
    '                 style="margin-right: 4px; margin-left: 2px;" ' +
    '                 data-url="{url}" ' +
    '                 onclick="copy_link_into_clipboard(this);">' +
    "         Copy {name} link</button>";

  var link_button =
    '<a id="copy-{name}-link" ' +
    '                 href="{url}" ' +
    '                 class="btn btn-default btn-sm navbar-btn" ' +
    '                 style="margin-right: 4px; margin-left: 2px;" ' +
    '                 target="_blank">' +
    "              Go to {name}</a>";

  var s = $("<span id='binder-buttons'></span>");
  s.append(
    link_button.replace(/{name}/g, "repo").replace("{url}", "{repo_url}"),
  );
  s.append(
    copy_button.replace(/{name}/g, "binder").replace("{url}", "{binder_url}"),
  );
  if ($("#ipython_notebook").length && $("#ipython_notebook>a").length) {
    s.append(
      copy_button
        .replace(/{name}/g, "session")
        .replace(
          "{url}",
          window.location.origin.concat($("#ipython_notebook>a").attr("href")),
        ),
    );
  }
  // add buttons at the end of header-container
  $("#header-container").append(s);
}

add_binder_buttons();
