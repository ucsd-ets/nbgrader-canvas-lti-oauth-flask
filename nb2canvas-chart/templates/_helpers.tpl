{{/*
Expand the name of the chart.
*/}}
{{- define "nb2canvas-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "nb2canvas-chart.fullname" -}}
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
{{- define "nb2canvas-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nb2canvas-chart.labels" -}}
helm.sh/chart: {{ include "nb2canvas-chart.chart" . }}
{{ include "nb2canvas-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nb2canvas-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "nb2canvas-chart.nbgrader2canvas.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.identifier: web
{{- end }}

{{- define "nb2canvas-chart.postgres.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.identifier: db
{{- end }}

{{- define "nb2canvas-chart.nb2canvas.pv.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
type: local
app.identifier: web
{{- end }}

{{- define "nb2canvas-chart.postgres.pv.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
type: local
app.identifier: db
{{- end }}

{{- define "nb2canvas-chart.nb2canvas.pvc.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.identifier: web

{{- end }}

{{- define "nb2canvas-chart.postgres.pvc.labels" -}}
app.kubernetes.io/name: {{ include "nb2canvas-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.identifier: db
{{- end }}

{{- define "nb2canvas-chart.namespace.labels" -}}
openpolicyagent.org/webhook: ignore
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "nb2canvas-chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "nb2canvas-chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}