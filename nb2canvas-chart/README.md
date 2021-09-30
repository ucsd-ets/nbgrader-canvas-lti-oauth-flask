# nb2canvas-chart

## Refactoring

- Convert repo to have kubernetes resources as file names rather than by app component. This will help elucidate k8s structure to other developers

- full path for postgres storage and move `nfs` under `postgres` in `values.yaml`

- add `{{- include "nb2canvas-chart.labels" . | nindent 4 }}` to each k8s resource under labels