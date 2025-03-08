{{- /*
  binderhub.extraFiles.data:
    Renders content for a k8s Secret's data field, coming from extraFiles with
    binaryData entries.
*/}}
{{- define "binderhub.extraFiles.data.withNewLineSuffix" -}}
    {{- range $file_key, $file_details := . }}
        {{- include "binderhub.extraFiles.validate-file" (list $file_key $file_details) }}
        {{- if $file_details.binaryData }}
            {{- $file_key | quote }}: {{ $file_details.binaryData | nospace | quote }}{{ println }}
        {{- end }}
    {{- end }}
{{- end }}
{{- define "binderhub.extraFiles.data" -}}
    {{- include "binderhub.extraFiles.data.withNewLineSuffix" . | trimSuffix "\n" }}
{{- end }}

{{- /*
  binderhub.extraFiles.stringData:
    Renders content for a k8s Secret's stringData field, coming from extraFiles
    with either data or stringData entries.
*/}}
{{- define "binderhub.extraFiles.stringData.withNewLineSuffix" -}}
    {{- range $file_key, $file_details := . }}
        {{- include "binderhub.extraFiles.validate-file" (list $file_key $file_details) }}
        {{- $file_name := $file_details.mountPath | base }}
        {{- if $file_details.stringData }}
            {{- $file_key | quote }}: |
              {{- $file_details.stringData | trimSuffix "\n" | nindent 2 }}{{ println }}
        {{- end }}
        {{- if $file_details.data }}
            {{- $file_key | quote }}: |
              {{- if or (eq (ext $file_name) ".yaml") (eq (ext $file_name) ".yml") }}
              {{- $file_details.data | toYaml | nindent 2 }}{{ println }}
              {{- else if eq (ext $file_name) ".json" }}
              {{- $file_details.data | toJson | nindent 2 }}{{ println }}
              {{- else if eq (ext $file_name) ".toml" }}
              {{- $file_details.data | toToml | trimSuffix "\n" | nindent 2 }}{{ println }}
              {{- else }}
              {{- print "\n\nextraFiles entries with 'data' (" $file_key " > " $file_details.mountPath ") needs to have a filename extension of .yaml, .yml, .json, or .toml!" | fail }}
              {{- end }}
        {{- end }}
    {{- end }}
{{- end }}
{{- define "binderhub.extraFiles.stringData" -}}
    {{- include "binderhub.extraFiles.stringData.withNewLineSuffix" . | trimSuffix "\n" }}
{{- end }}

{{- define "binderhub.extraFiles.validate-file" -}}
    {{- $file_key := index . 0 }}
    {{- $file_details := index . 1 }}

    {{- /* Use of mountPath. */}}
    {{- if not ($file_details.mountPath) }}
        {{- print "\n\nextraFiles entries (" $file_key ") must contain the field 'mountPath'." | fail }}
    {{- end }}

    {{- /* Use one of stringData, binaryData, data. */}}
    {{- $field_count := 0 }}
    {{- if $file_details.data }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if $file_details.stringData }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if $file_details.binaryData }}
        {{- $field_count = add1 $field_count }}
    {{- end }}
    {{- if ne $field_count 1 }}
        {{- print "\n\nextraFiles entries (" $file_key ") must only contain one of the fields: 'data', 'stringData', and 'binaryData'." | fail }}
    {{- end }}
{{- end }}
