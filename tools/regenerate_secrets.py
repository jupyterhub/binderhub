"""
This script is used to regenerate secrets for travis-ci
"""

import os
import tarfile
import webbrowser

from subprocess import run

TARGET_REPOS = ('jupyterhub/helm-chart', 'MeeseeksBox/mybinder.org-deploy')
SOURCE_REPO = 'Carreau/binderhub' # change me
TARFILE = 'secret.tar'

def main():

    to_tar = []


    for repo in TARGET_REPOS :
        name = repo.replace('/','-')
        pubfile = f"{name}-key.pub"
        to_tar.append(f'{name}-key')
        settings_url = f"https://github.com/{repo}/settings/keys"

        command = ("ssh-keygen", "-q", "-t", "rsa", "-b", "2048", "-N", "", "-C", f"travis-{name}-key", "-f", f"{name}-key")

        print('generating Deployment key for {repo}...')
        run(command)
        print("Add the content of pubfile to {settings_url}")
        with open(pubfile, 'r') as f:
            print(f.read())
        open_settings = input('enter "y" open the setting page:\n').lower()
        if open_settings == 'y':
            webbrowser.open(settings_url)
        print(f'Erasing public key {pubfile}...')
        os.remove(pubfile)


    with tarfile.open(TARFILE,'w') as tar:
        for f in to_tar:
            tar.add(f)

    for f in to_tar:
        os.remove(f)
    if os.path.exists(TARFILE+'.enc'):
        os.remove(TARFILE+'.enc')
    run(['travis', 'encrypt-file', '--no-interactive', '--repo', SOURCE_REPO, TARFILE, '--add'])
    os.remove(TARFILE)



if __name__ == '__main__':
    main()
