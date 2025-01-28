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
Render docker config.json for the registry-publishing secret and other docker configuration.
*/}}
{{- define "buildDockerConfig" -}}

{{- /* initialize a dict to represent a docker config with registry credentials */}}
{{- $auths := dict }}
{{- range .Values.registry }}
  {{- /* default auth url */ -}}
  {{- $url := (default "https://index.docker.io/v1" .url) }}

  {{- /* default username if unspecified
    (_json_key for gcr.io, <token> otherwise)
  */ -}}
  {{- if not .username }}
    {{- if eq $url "https://gcr.io" }}
      {{- $_ := set . "username" "_json_key" }}
    {{- else }}
      {{- $_ := set . "username" "<token>" }}
    {{- end }}
  {{- end }}
  {{- $username := .username -}}
  {{- $auths := merge $auths (dict $url (dict "auth" (printf "%s:%s" $username .password | b64enc))) }}
{{- end }}
{{- $dockerConfig := dict "auths" $auths }}

{{- /* augment our initialized docker config with buildDockerConfig */}}
{{- if .Values.config.BinderHub.buildDockerConfig }}
{{- $dockerConfig := merge $dockerConfig .Values.config.BinderHub.buildDockerConfig }}
{{- end }}

{{- $dockerConfig | toPrettyJson }}
{{- end }}
