Set up the container registry
=============================

BinderHub will build Docker images out of GitHub repositories, and then
registers those images with an online registry so that JupyterHub can
serve user instances from that registry. You can use any registry that
you like, though this guide covers how to properly configure the **Google
Container Registry** (``gcr.io``).

Doing this involves using the Container Registry user interface. The following
steps will create an account with google cloud that has the authorization
to push to google container registry:

1. Go to `console.cloud.google.com`_
2. Make sure your project is selected
3. Click ``<hamburger menu> -> IAM / Admin -> Service Accounts`` menu option
4. Click **Create service account**
5. Give your account a descriptive name such as "BinderHub-registry"
6. Click ``Role -> Storage -> Storage Admin`` menu option
7. Check **Furnish new private key**
8. Click **Create**

These steps will download a **JSON file** to your computer. The JSON file
contains the password that can be used to push Docker images to the ``gcr.io``
registry.

.. important::

   Make sure to remember this password as you cannot generate a second one
   without re-doing the steps above.

Now that our registry is set up, it's time to :doc:`setup-binderhub`.

.. _console.cloud.google.com: http://console.cloud.google.com
