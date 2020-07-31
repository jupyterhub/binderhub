// Cycle through helpful messages on the loading page
const help_messages = [
    'New to Binder? Check out the <a target="_blank" href="https://mybinder.readthedocs.io/en/latest/">Binder Documentation</a> for more information.',
    'You can learn more about building your own Binder repositories in <a target="_blank" href="https://docs.mybinder.org">the Binder community documentation</a>.',
    'We use the <a target="_blank" href="https://repo2docker.readthedocs.io/">repo2docker</a> tool to automatically build the environment in which to run your code.',
    'Take a look at the <a target="_blank" href="https://repo2docker.readthedocs.io/en/latest/config_files.html">full list of configuration files supported by repo2docker.</a>',
    'Need more than just a Jupyter notebook? You can <a target="_blank" href="https://mybinder.readthedocs.io/en/latest/howto/user_interface.html">customize the user interface</a>.',
    'Take a look at our <a target="_blank" href="https://github.com/binder-examples/">gallery of example repositories</a>.',
    'If a repository takes a long time to launch, it is usually because Binder needs to create the environment for the first time.',
    'The tool that powers this page is called <a target="_blank" href="https://binderhub.readthedocs.io">BinderHub</a>. It is an open source tool that you can deploy yourself.',
    'The Binder team has <a target="_blank" href="https://mybinder-sre.readthedocs.io/en/latest/">a site reliability guide</a> that talks about what it is like to run a BinderHub.',
    'You can connect with the Binder community in the <a target="_blank" href="https://discourse.jupyter.org/c/binder">Jupyter community forum</a>.',
    'Empty log? Notebook not loading? Maybe your ad blocker is interfering. Consider adding this site to the list of trusted sources.',
    'Your launch may take longer the first few times a repository is used. This is because our machine needs to create your environment.',
    'Read our <a target="_blank" href="https://discourse.jupyter.org/t/how-to-reduce-mybinder-org-repository-startup-time/4956">advice for speeding up your Binder launch</a>.',
]

// Set a launch timeout beyond-which we'll stop cycling messages
export function nextHelpText () {
    var text = $('div#loader-links p.text-center');
    if (text !== null) {
        if (!text.hasClass('longLaunch')) {
            // Pick a random help message and update
            var msg = help_messages[Math.floor(Math.random() * help_messages.length)];
        } else {
            var msg = 'Your session is taking longer than usual to start!<br />Check the log messages below to see what is happening.';
        }
        text.html(msg);
    }
}
