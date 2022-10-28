{{/* vim: set filetype=mustache: */}}

{{/* Generate init containers */}}
{{- define "binderhub.builder.initContainers" }}
    {{- $builder := (index .Values .Values.containerBuilderPod) }}
    {{- with $builder.initContainers }}
      initContainers:
        {{- . | toYaml | nindent 8 }}
    {{- end }}
{{- end }}

{{/* Generate containers */}}
{{- define "binderhub.builder.containers"}}
  {{- $builder := (index .Values .Values.containerBuilderPod) }}
  {{- $daemonset := $builder.daemonset }}
      - name: {{ .Values.containerBuilderPod }}
        image: {{ $daemonset.image.name }}:{{ $daemonset.image.tag }}
        imagePullPolicy: {{ $daemonset.image.pullPolicy }}
        {{- with $daemonset.resources }}
          resources:
            {{- $daemonset.resources | toYaml | nindent 10 }}
        {{- end }}
  {{- if eq .Values.containerBuilderPod "dind" }}
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
          mountPath: {{ $builder.hostSocketDir }}
  {{- end }}
  {{- if eq .Values.containerBuilderPod "pink" }}
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
  {{- end }}
        {{- with $daemonset.extraVolumeMounts }}
        {{- . | toYaml | nindent 8 }}
        {{- end }}
        {{- with $daemonset.lifecycle }}
        lifecycle:
          {{- . | toYaml | nindent 10 }}
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
