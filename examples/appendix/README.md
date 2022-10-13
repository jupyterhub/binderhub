This example shows how to use
[`appendix`](https://binderhub.readthedocs.io/en/latest/reference/app.html?highlight=c.BinderHub.appendix%20#binderhub.app.BinderHub)
feature of BinderHub.

Appendix consists of Docker commands which are passed to repo2docker and
executed at the end of each build process.

## What does this example do?

In this example `appendix` is used to customize the Notebook UI:

1. Instead of standard notebook login page with form,
   display an informative page, e.g. how to launch a new binder.
   This is very useful when people share
   pod urls instead of binder launch urls.

2. Remove logout button

3. Add binder buttons next to `Quit button`:

- `Go to repo`: opens the source repo url in new tab
- `Copy binder link`: copies the binder launch link into clipboard
- `Copy session link`: copies the binder session link into clipboard.
  When this link is shared with another user, that user will reach to
  the same binder session.
  It will not start a new launch.

## How does the example work?

To run the example you have to add the appendix into your BinderHub configuration as shown in
[binderhub_config.py](/examples/appendix/binderhub_config.py). These commands are executed every time when
there is a new build and it does:

- set environment variables for binder and repo urls
- download this appendix folder
- run [run-appendix](/examples/appendix/run-appendix) script

`run-appendix` mainly does 2 things:

1. Copy `templates` into `/etc/jupyter/binder_templates`
   and update notebook app configuration to append this path into `extra_template_paths`.
   So when notebook app starts, it uses customized templates.

2. Inject Javascript code into `~/.jupyter/custom/custom.js`. This is
   executed when the notebook app starts and it adds the buttons.
