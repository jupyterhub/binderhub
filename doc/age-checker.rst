============================
Check the age of a BinderHub
============================

There are several core pieces of technology behind a BinderHub. This page
provides a quick interface to check how up-to-date each of them is.

**Check the age of a BinderHub with the form below**

.. raw:: html

   <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.0/build/pure-min.css" integrity="sha384-nn4HPE8lTHyVtfCBi5yW9d20FjT8BJwUXyWZT9InLYax14RDjBj46LmSztkmNP9w" crossorigin="anonymous">
   <style>
   input#checkAgeButton {
    font-size: 1rem;
    line-height: 1.5;
    background-color: #477dca;
    border-radius: 3px;
    border: none;
    color: white;
    display: inline-block;
    font-weight: 700;
    padding: 6px 18px;
    margin-top: 1em;
    text-decoration: none
   }

   div.version_text {
     font-weight: bolder;
   }

   div.version_text span.empty {
     color: grey;
   }
   div.version_text span.fail {
     color: red;
   }
   div.version_text span.success {
     color: green;
   }
   </style>

   <form id="badgeform" class="pure-form">
      <input type="text" class="pure-input-1-4" id="binderhuburl" placeholder="BinderHub URL">
      <input type="button" id="checkAgeButton" onclick="checkAge()" value="Check Age" />
   </form>

   <hr />

   <div class="version_text" id="binderhubversiontext">BinderHub version: <span class="empty">Fill in the box then click "check age"</span></div>
   <div class="version_text" id="repo2dockerversiontext">repo2docker version: <span class="empty">Fill in the box then click "check age"</span></div>

   <script>
   function checkAge() {
       // Variables
       var repo2docker_div = document.querySelectorAll('div#repo2dockerversiontext span')[0];
       var binderhub_div = document.querySelectorAll('div#binderhubversiontext span')[0];

       // Build the new badge link
       var url = document.getElementById("binderhuburl").value;
       if (!url.startsWith('http')) {
          url = "https://" + url;
       }

       // Get the versions for this BinderHub
       var url=`${url}/versions`;
       var resp = $.get(url);
       resp.done((versions, status) => {
            console.log(status);

            // Versions will be a JSON response
            bhub_version = versions['binderhub'];
            r2d_version = versions['builder'];
            console.log(versions)

            // Update the rST
            repo2docker_div.setAttribute('class', 'success')
            binderhub_div.setAttribute('class', 'success')
            binderhub_div.textContent = `${bhub_version}`
            repo2docker_div.textContent = `${r2d_version}`
       });

       resp.fail(() => {
         binderhub_div.setAttribute('class', 'fail')
         repo2docker_div.setAttribute('class', 'fail')
         binderhub_div.textContent = "BinderHub URL not correct! Please check your URL."
         repo2docker_div.textContent = "BinderHub URL not correct! Please check your URL."
       });
   }
   </script>
