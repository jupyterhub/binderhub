import { getPathType } from './path';


export function getBuildFormValues() {
  const providerPrefix = $('#provider_prefix').val().trim();
  let repo = $('#repository').val().trim();
  if (providerPrefix !== 'git') {
    repo = repo.replace(/^(https?:\/\/)?gist.github.com\//, '');
    repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
    repo = repo.replace(/^(https?:\/\/)?gitlab.com\//, '');
  }
  // trim trailing or leading '/' on repo
  repo = repo.replace(/(^\/)|(\/?$)/g, '');
  // git providers encode the URL of the git repository as the repo
  // argument.
  if (repo.includes("://") || providerPrefix === 'gl') {
    repo = encodeURIComponent(repo);
  }

  let ref = $('#ref').val().trim() || $("#ref").attr("placeholder");
  if (providerPrefix === 'zenodo' || providerPrefix === 'figshare' || providerPrefix === 'dataverse' ||
    providerPrefix === 'hydroshare') {
    ref = "";
  }
  const path = $('#filepath').val().trim();
  return {
    'providerPrefix': providerPrefix, 'repo': repo,
    'ref': ref, 'path': path, 'pathType': getPathType()
  };
}
