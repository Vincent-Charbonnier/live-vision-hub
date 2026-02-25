{{- define "live-vision.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "live-vision.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "live-vision.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "live-vision.labels" -}}
app.kubernetes.io/name: {{ include "live-vision.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "live-vision.emotionTokenSecretName" -}}
{{- if .Values.emotion.tokenSecretName -}}
{{- .Values.emotion.tokenSecretName -}}
{{- else -}}
{{- printf "%s-emotion-token" (include "live-vision.fullname" .) -}}
{{- end -}}
{{- end }}
