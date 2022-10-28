{{/* vim: set filetype=mustache: */}}

{{/* Generate init containers */}}
{{- define "binderhub.builder.initContainers" }}
  {{- if eq .Values.containerBuilderPod "dind" -}}
      {{- with .Values.dind.initContainers }}
      initContainers:
        {{- . | toYaml | nindent 8 }}
      {{- end }}
  {{- end }}
  {{- if eq .Values.containerBuilderPod "pink" -}}
      {{- with .Values.pink.initContainers }}
      initContainers:
        {{- . | toYaml | nindent 8 }}
      {{- end }}
  {{- end }}
{{- end }}

{{/* Generate containers */}}
{{- define "binderhub.builder.containers" }}
  {{- if eq .Values.containerBuilderPod "dind" -}}
        image: {{ .Values.dind.daemonset.image.name }}:{{ .Values.dind.daemonset.image.tag }}
        imagePullPolicy: {{ .Values.dind.daemonset.image.pullPolicy }}
        resources:
          {{- .Values.dind.resources | toYaml | nindent 10 }}
        args:
          - dockerd
          - --storage-driver={{ .Values.dind.storageDriver }}
          - -H unix://{{ .Values.dind.hostSocketDir }}/docker.sock
          {{- with .Values.dind.daemonset.extraArgs }}
          {{- . | toYaml | nindent 10 }}
          {{- end }}
        securityContext:
          privileged: true
        volumeMounts:
        - name: dockerlib-dind
          mountPath: /var/lib/docker
        - name: rundind
          mountPath: {{ .Values.dind.hostSocketDir }}
        {{- with .Values.dind.daemonset.extraVolumeMounts }}
        {{- . | toYaml | nindent 8 }}
        {{- end }}
        {{- with .Values.dind.daemonset.lifecycle }}
        lifecycle:
          {{- . | toYaml | nindent 10 }}
        {{- end }}
  {{- end }}
  {{- if eq .Values.containerBuilderPod "pink" -}}
        image: {{ .Values.pink.daemonset.image.name }}:{{ .Values.pink.daemonset.image.tag }}
        imagePullPolicy: {{ .Values.pink.daemonset.image.pullPolicy }}
        resources:
          {{- .Values.pink.resources | toYaml | nindent 10 }}
        args:
          - podman
          - system
          - service
          - --time=0
          - unix:///var/run/pink/docker.sock
        securityContext:
          privileged: true
          runAsUser: 1000  # podman default user id
        volumeMounts:
        - mountPath: /home/podman/.local/share/containers/storage/
          name: podman-containers
        - mountPath: /var/run/pink/
          name: podman-socket
        {{- with .Values.pink.daemonset.extraVolumeMounts }}
        {{- . | toYaml | nindent 8 }}
        {{- end }}
        {{- with .Values.pink.daemonset.lifecycle }}
        lifecycle:
          {{- . | toYaml | nindent 10 }}
        {{- end }}
  {{- end }}
{{- end }}

{{/* Generate volumes */}}
{{- define "binderhub.builder.volumes" }}
  {{- if eq .Values.containerBuilderPod "dind" -}}
      - name: dockerlib-dind
        hostPath:
          path: {{ .Values.dind.hostLibDir }}
          type: DirectoryOrCreate
      - name: rundind
        hostPath:
          path: {{ .Values.dind.hostSocketDir }}
          type: DirectoryOrCreate
      {{- with .Values.dind.daemonset.extraVolumes }}
      {{- . | toYaml | nindent 6 }}
      {{- end }}
  {{- end }}
  {{- if eq .Values.containerBuilderPod "pink" -}}
      - name: podman-containers
        hostPath:
          path: {{ .Values.pink.hostStorageDir }}
          type: DirectoryOrCreate
      - name: podman-socket
        hostPath:
          path: {{ .Values.pink.hostSocketDir }}
          type: DirectoryOrCreate
      {{- with .Values.pink.daemonset.extraVolumes }}
      {{- . | toYaml | nindent 6 }}
      {{- end }}
  {{- end }}
{{- end }}
