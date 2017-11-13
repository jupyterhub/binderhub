/*
 * Basic functionalities for the settings page. Just a function that will post
 * to /settings/ the new binder to set as default.
 *
 */

"use strict";

function postOnClick(el)
{
    var data = new FormData();
    var new_default_binder = el.getAttribute('attr-binder')
    data.append('default', new_default_binder);

    var xhr = new XMLHttpRequest();
    xhr.addEventListener('load', function(event) {
      document.getElementsByClassName('active')[0].classList.remove('active')
      el.classList.add('active')
    });
    xhr.addEventListener('error', function(event) {
      console.log('Oups! Something went wrong.');
      console.log('event');
    });
    xhr.open('POST', 'settings/', true);
    xhr.send(data);
    return false;
}
