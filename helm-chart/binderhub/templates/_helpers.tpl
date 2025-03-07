{{- /*
  binderhub-service.chart-version-to-git-ref:
    Renders a valid git reference from a chartpress generated version string.
    In practice, either a git tag or a git commit hash will be returned.

    - The version string will follow a chartpress pattern,
      like "0.1.0-0.dev.git.17.h8368bc0", see
      https://github.com/jupyterhub/chartpress#examples-chart-versions-and-image-tags.

    - The regexReplaceAll function is a sprig library function, see
      https://masterminds.github.io/sprig/strings.html.

    - The regular expression is in golang syntax, but \d had to become \\d for
      example.
*/}}
{{- define "binderhub-service.chart-version-to-git-ref" -}}
{{- regexReplaceAll ".*\\.git\\.\\d+\\.h(.*)" . "${1}" }}
{{- end }}
