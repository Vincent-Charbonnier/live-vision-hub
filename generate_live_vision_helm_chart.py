import os
import shutil

chart_name = "live-vision"
chart_version = "0.0.1"
base_dir = f"./{chart_name}"
templates_dir = os.path.join(base_dir, "templates")


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if os.path.exists(base_dir):
    print(f"Removing existing chart at '{base_dir}'...")
    shutil.rmtree(base_dir)

print(f"Creating Helm chart directory structure at '{base_dir}'...")
os.makedirs(templates_dir, exist_ok=True)

print("Writing Chart.yaml...")
chart_yaml = f"""\
apiVersion: v2
name: {chart_name}
description: Helm chart for Live Vision (frontend + backend)
type: application
version: {chart_version}
appVersion: "{chart_version}"
"""
write_file(os.path.join(base_dir, "Chart.yaml"), chart_yaml)

print("Writing values.yaml...")
values_yaml = """\
replicaCount:
  frontend: 1
  backend: 1

image:
  frontend:
    repository: vinchar/live-vision-hub
    tag: "0.0.1"
    pullPolicy: IfNotPresent
  backend:
    repository: live-vision-backend
    tag: "0.0.1"
    pullPolicy: IfNotPresent

service:
  frontend:
    type: ClusterIP
    port: 80
  backend:
    type: ClusterIP
    port: 8000

resources:
  frontend:
    limits: {}
    requests: {}
  backend:
    limits: {}
    requests: {}

nodeSelector: {}
tolerations: []
affinity: {}

readinessProbe:
  frontend:
    path: "/"
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  backend:
    path: "/health"
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1

livenessProbe:
  frontend:
    path: "/"
    initialDelaySeconds: 30
    periodSeconds: 20
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  backend:
    path: "/health"
    initialDelaySeconds: 30
    periodSeconds: 20
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1

persistence:
  enabled: false
  storageClassName: ""
  accessModes:
    - ReadWriteOnce
  size: 1Gi

emotion:
  endpoint: ""
  model: "nvidia/nemotron-nano-12b-v2-vl"
  tokenSecretName: ""
  tokenSecretKey: "token"
  createTokenSecret: false
  tokenValue: ""

ingress:
  enabled: false
  className: ""
  host: live-vision.example.com
  annotations: {}
  tls:
    enabled: false
    secretName: ""

istio:
  enabled: true
  gateway: "istio-system/ezaf-gateway"
  host: "live-vision.${DOMAIN_NAME}"
"""
write_file(os.path.join(base_dir, "values.yaml"), values_yaml)

print("Writing _helpers.tpl...")
helpers_tpl = """\
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
"""
write_file(os.path.join(templates_dir, "_helpers.tpl"), helpers_tpl)

print("Writing frontend-deployment.yaml...")
frontend_deployment_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "live-vision.fullname" . }}-frontend
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  replicas: {{ .Values.replicaCount.frontend }}
  selector:
    matchLabels:
      app: {{ include "live-vision.name" . }}
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        app: {{ include "live-vision.name" . }}
        app.kubernetes.io/component: frontend
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: frontend
          image: "{{ .Values.image.frontend.repository }}:{{ .Values.image.frontend.tag }}"
          imagePullPolicy: {{ .Values.image.frontend.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.frontend.port }}
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.frontend.path | quote }}
              port: {{ .Values.service.frontend.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.frontend.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.frontend.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.frontend.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.frontend.failureThreshold }}
            successThreshold: {{ .Values.readinessProbe.frontend.successThreshold }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.frontend.path | quote }}
              port: {{ .Values.service.frontend.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.frontend.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.frontend.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.frontend.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.frontend.failureThreshold }}
            successThreshold: {{ .Values.livenessProbe.frontend.successThreshold }}
          resources:
            {{- toYaml .Values.resources.frontend | nindent 12 }}
"""
write_file(os.path.join(templates_dir, "frontend-deployment.yaml"), frontend_deployment_yaml)

print("Writing backend-deployment.yaml...")
backend_deployment_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "live-vision.fullname" . }}-backend
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.replicaCount.backend }}
  selector:
    matchLabels:
      app: {{ include "live-vision.name" . }}
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        app: {{ include "live-vision.name" . }}
        app.kubernetes.io/component: backend
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: backend
          image: "{{ .Values.image.backend.repository }}:{{ .Values.image.backend.tag }}"
          imagePullPolicy: {{ .Values.image.backend.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.backend.port }}
          env:
            - name: EMOTION_ENDPOINT
              value: {{ .Values.emotion.endpoint | quote }}
            - name: EMOTION_MODEL
              value: {{ .Values.emotion.model | quote }}
            - name: EMOTION_CONFIG_PATH
              value: "/data/emotion-config.json"
            - name: EMOTION_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ include "live-vision.emotionTokenSecretName" . }}
                  key: {{ .Values.emotion.tokenSecretKey | quote }}
                  optional: true
          volumeMounts:
            - name: backend-data
              mountPath: /data
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.backend.path | quote }}
              port: {{ .Values.service.backend.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.backend.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.backend.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.backend.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.backend.failureThreshold }}
            successThreshold: {{ .Values.readinessProbe.backend.successThreshold }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.backend.path | quote }}
              port: {{ .Values.service.backend.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.backend.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.backend.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.backend.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.backend.failureThreshold }}
            successThreshold: {{ .Values.livenessProbe.backend.successThreshold }}
          resources:
            {{- toYaml .Values.resources.backend | nindent 12 }}
      volumes:
        - name: backend-data
          {{- if .Values.persistence.enabled }}
          persistentVolumeClaim:
            claimName: {{ include "live-vision.fullname" . }}-backend-data
          {{- else }}
          emptyDir: {}
          {{- end }}
"""
write_file(os.path.join(templates_dir, "backend-deployment.yaml"), backend_deployment_yaml)

print("Writing frontend-service.yaml...")
frontend_service_yaml = """\
apiVersion: v1
kind: Service
metadata:
  name: {{ include "live-vision.fullname" . }}-frontend
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  type: {{ .Values.service.frontend.type }}
  ports:
    - port: {{ .Values.service.frontend.port }}
      targetPort: {{ .Values.service.frontend.port }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "live-vision.name" . }}
    app.kubernetes.io/component: frontend
"""
write_file(os.path.join(templates_dir, "frontend-service.yaml"), frontend_service_yaml)

print("Writing backend-service.yaml...")
backend_service_yaml = """\
apiVersion: v1
kind: Service
metadata:
  name: {{ include "live-vision.fullname" . }}-backend
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  type: {{ .Values.service.backend.type }}
  ports:
    - port: {{ .Values.service.backend.port }}
      targetPort: {{ .Values.service.backend.port }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "live-vision.name" . }}
    app.kubernetes.io/component: backend
"""
write_file(os.path.join(templates_dir, "backend-service.yaml"), backend_service_yaml)

print("Writing emotion-token-secret.yaml...")
secret_yaml = """\
{{- if .Values.emotion.createTokenSecret }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "live-vision.emotionTokenSecretName" . }}
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{ .Values.emotion.tokenSecretKey }}: {{ .Values.emotion.tokenValue | quote }}
{{- end }}
"""
write_file(os.path.join(templates_dir, "emotion-token-secret.yaml"), secret_yaml)

print("Writing pvc.yaml...")
pvc_yaml = """\
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "live-vision.fullname" . }}-backend-data
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
spec:
  accessModes:
    {{- toYaml .Values.persistence.accessModes | nindent 4 }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClassName }}
  storageClassName: {{ .Values.persistence.storageClassName | quote }}
  {{- end }}
{{- end }}
"""
write_file(os.path.join(templates_dir, "pvc.yaml"), pvc_yaml)

print("Writing ingress.yaml...")
ingress_yaml = """\
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "live-vision.fullname" . }}
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
  annotations:
    {{- toYaml .Values.ingress.annotations | nindent 4 }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className | quote }}
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "live-vision.fullname" . }}-frontend
                port:
                  number: {{ .Values.service.frontend.port }}
          - path: /vision
            pathType: Prefix
            backend:
              service:
                name: {{ include "live-vision.fullname" . }}-backend
                port:
                  number: {{ .Values.service.backend.port }}
          - path: /emotion-config
            pathType: Prefix
            backend:
              service:
                name: {{ include "live-vision.fullname" . }}-backend
                port:
                  number: {{ .Values.service.backend.port }}
  {{- if .Values.ingress.tls.enabled }}
  tls:
    - hosts:
        - {{ .Values.ingress.host | quote }}
      secretName: {{ .Values.ingress.tls.secretName | quote }}
  {{- end }}
{{- end }}
"""
write_file(os.path.join(templates_dir, "ingress.yaml"), ingress_yaml)

print("Writing virtualservice.yaml...")
virtualservice_yaml = """\
{{- if .Values.istio.enabled }}
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: {{ include "live-vision.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "live-vision.labels" . | nindent 4 }}
spec:
  gateways:
    - {{ .Values.istio.gateway }}
  hosts:
    - {{ .Values.istio.host }}
  http:
    - match:
        - uri:
            prefix: /vision
      route:
        - destination:
            host: {{ include "live-vision.fullname" . }}-backend.{{ .Release.Namespace }}.svc.cluster.local
            port:
              number: {{ .Values.service.backend.port }}
    - match:
        - uri:
            prefix: /emotion-config
      route:
        - destination:
            host: {{ include "live-vision.fullname" . }}-backend.{{ .Release.Namespace }}.svc.cluster.local
            port:
              number: {{ .Values.service.backend.port }}
    - match:
        - uri:
            prefix: /
      route:
        - destination:
            host: {{ include "live-vision.fullname" . }}-frontend.{{ .Release.Namespace }}.svc.cluster.local
            port:
              number: {{ .Values.service.frontend.port }}
{{- end }}
"""
write_file(os.path.join(templates_dir, "virtualservice.yaml"), virtualservice_yaml)

print("Writing NOTES.txt...")
notes_txt = """\
Thank you for installing the live-vision chart.

This chart deploys:
  - frontend (React/nginx) on port 80
  - backend (FastAPI) on port 8000

Emotion runtime configuration:
  - .Values.emotion.endpoint
  - .Values.emotion.model
  - EMOTION_TOKEN from secret:
      name: {{ include "live-vision.emotionTokenSecretName" . }}
      key:  {{ .Values.emotion.tokenSecretKey }}

If you want the chart to create the token secret:
  emotion.createTokenSecret: true
  emotion.tokenValue: "<token>"

Install:
  helm install live-vision ./live-vision

Upgrade:
  helm upgrade --install live-vision ./live-vision -f my-values.yaml
"""
write_file(os.path.join(templates_dir, "NOTES.txt"), notes_txt)

print(f"Helm chart folder created at: {base_dir}")
print("Packaging Helm chart into .tgz archive...")
exit_code = os.system(f"helm package {base_dir}")

if exit_code == 0:
    print("Chart packaged successfully!")
    print(f"Install with: helm install live-vision {chart_name}-{chart_version}.tgz")
else:
    print("Failed to package chart. Ensure Helm is installed and on PATH.")
