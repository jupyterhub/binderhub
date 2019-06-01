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
   // commit data
   var response_data = {};
   var bhub_resp = $.get("https://api.github.com/repos/jupyterhub/binderhub/commits", (data) => {
     response_data['bhub_json'] = data;
     console.log("got binderhub commit data");
   });
   var r2d_resp = $.getJSON("https://api.github.com/repos/jupyter/repo2docker/commits", (data) => {
     response_data['r2d_json'] = data;
     console.log("got repo2docker commit data");
   });
   
   function findCommitFromSHA(commits, sha) {
    for (ii=0; ii < commits.length; ii++) {
      var this_commit = commits[ii]
      var this_sha = this_commit['sha'];
      search = this_sha.indexOf(sha.substr(1));  // A hack because there seems to be a bug w/ the SHA
      if (search != -1) {
          var chosen_commit = this_commit
          return chosen_commit
      } 
    }
   };

   function findCommitAge(commit) {
      return Date.parse(commit['commit']['author']['date']);
   };

   function milliToDays(milli) {
      return milli / 1000 / 60 / 60 / 24;
   }

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

            // Load the commit data
            var bhub_commits = response_data['bhub_json'];
            var r2d_commits = response_data['r2d_json'];
            var r2d_latest_date = findCommitAge(r2d_commits[0]);
            var bhub_latest_date = findCommitAge(bhub_commits[0]);

            // Versions will be a JSON response
            bhub_version = versions['binderhub'];
            r2d_version = versions['builder'];
            console.log(versions)
            
            // Find the commit for this version and parse its age
            bhub_commit_part = bhub_version.split('.')[3]
            r2d_commit_part = r2d_version.split(':')[1]
            var r2d_this_commit = findCommitFromSHA(r2d_commits, r2d_commit_part);
            var bhub_this_commit = findCommitFromSHA(bhub_commits, bhub_commit_part);
            var r2d_this_commit_age = findCommitAge(r2d_this_commit);
            var bhub_this_commit_age = findCommitAge(bhub_this_commit);

            // Convert age to days from milliseconds
            var bhub_age = parseInt(milliToDays(bhub_latest_date - bhub_this_commit_age));
            var r2d_age = parseInt(milliToDays(r2d_latest_date - r2d_this_commit_age));
            
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
