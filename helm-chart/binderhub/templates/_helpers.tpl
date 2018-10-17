{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Render docker config.json for the registry-publishing secret.
*/}}
{{- define "registryDockerConfig" -}}
{{- if .Values.registry.gcrKey }}
{
  "auths": {
    "https://gcr.io": {
      "auth": "{{ printf "_json_key:%s" .Values.registry.gcrKey | b64enc }}"
    }
  }
}
{{- else if .Values.registry.password }}
{{- $username := (default "<token>" .Values.registry.username )}}
{
  "auths": {
    "https://index.docker.io/v1": {
      "auth": "{{ printf "%s:%s" $username .Values.registry.password | b64enc }}"
    }
  }
}
{{- else }}
{{ .Values.registry.dockerConfigJson }}
{{- end }}
{{- end }}
