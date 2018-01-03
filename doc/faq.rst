.. _faq:

Frequently Asked Questions
==========================

The following are some common questions and issues that arise when deploying
your own BinderHub.

How can I increase my GitHub API limit?
---------------------------------------

By default GitHub only lets you make a handful of requests each hour. To
increase this limit significantly, create an API access token that's attached
to your GitHub username.

1. Create a new token with default (check no boxes)
   permissions `here <https://github.com/settings/tokens/new>`_.

2. Store your new token somewhere secure (e.g. keychain, netrc, etc.)

3. Before running your BinderHub server, run the following::

   export GITHUB_ACCESS_TOKEN=<insert_token_value_here>

BinderHub will automatically use the token stored in this variable when making
API requests to GitHub.
