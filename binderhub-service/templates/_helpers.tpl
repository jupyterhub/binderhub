{{/*
Expand the name of the chart.
*/}}
{{- define "binderhub-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "binderhub-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "binderhub-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "binderhub-service.labels" -}}
helm.sh/chart: {{ include "binderhub-service.chart" . }}
{{ include "binderhub-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "binderhub-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "binderhub-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "binderhub-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "binderhub-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}



{{- /*
  binderhub-service.chart-version-to-git-ref:
    Renders a valid git reference from a chartpress generated version string.
    In practice, either a git tag or a git commit hash will be returned.

    - The version string will follow a chartpress pattern, see
      https://github.com/jupyterhub/chartpress#examples-chart-versions-and-image-tags.

    - The regexReplaceAll function is a sprig library function, see
      https://masterminds.github.io/sprig/strings.html.

    - The regular expression is in golang syntax, but \d had to become \\d for
      example.
*/}}
{{- define "binderhub-service.chart-version-to-git-ref" -}}
{{- regexReplaceAll ".*[.-]n\\d+[.]h(.*)" . "${1}" }}
{{- end }}
