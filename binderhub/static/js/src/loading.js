// Cycle through helpful messages on the loading page
const help_messages = [
    'New to Binder? Check out the <a target="_blank" href="https://mybinder.readthedocs.io/en/latest/">Binder Documentation</a> for more information',
    'If a Binder takes a long time to launch, it is usually because Binder needs to pull the environment onto a computer for the first time',
    'The tool that powers this page is called <a target="_blank" href="https://binderhub.readthedocs.io">BinderHub</a>. It is an open source tool that anybody can deploy',
    'The Binder team has <a target="_blank" href="https://mybinder-sre.readthedocs.io/en/latest/">a site reliability guide </a> that talks about what it is like to run a BinderHub',
    'You can connect with the Binder community in the <a target="_blank" href="https://discourse.jupyter.org/c/binder">Jupyter community forum</a>'
  ]

export function nextHelpText () {
    var text = $('div#loader-links p.text-center');
    if (text !== null) {
        // Pick a random help message and update
        var msg = help_messages[Math.floor(Math.random() * help_messages.length)];
        text.html(msg);
    }
}