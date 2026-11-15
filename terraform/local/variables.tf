variable "kube_context" {
  description = "kubeconfig context to use."
  type        = string
  default     = "kind-ai-lab"
}

variable "namespace" {
  type    = string
  default = "ai-lab"
}

variable "install_monitoring" {
  description = "Install kube-prometheus-stack."
  type        = bool
  default     = false
}

variable "install_argocd" {
  type    = bool
  default = false
}

variable "install_kyverno" {
  type    = bool
  default = false
}

variable "chart_versions" {
  description = "Pin chart versions after your first successful install (null = latest)."
  type        = map(string)
  default     = {}
}
