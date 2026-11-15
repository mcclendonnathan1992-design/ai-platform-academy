provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = var.kube_context
  }
}

# Module 04 created this namespace by hand. Adopt it:
#   terraform import kubernetes_namespace.ai_lab ai-lab
resource "kubernetes_namespace" "ai_lab" {
  metadata {
    name = var.namespace
    labels = {
      "pod-security.kubernetes.io/enforce" = "baseline"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "helm_release" "monitoring" {
  count            = var.install_monitoring ? 1 : 0
  name             = "monitoring"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = lookup(var.chart_versions, "kube-prometheus-stack", null)
  values           = [file("${path.module}/../../k8s/observability/values-kube-prometheus-stack.yaml")]
}

resource "helm_release" "argocd" {
  count            = var.install_argocd ? 1 : 0
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  version          = lookup(var.chart_versions, "argo-cd", null)
}

resource "helm_release" "kyverno" {
  count            = var.install_kyverno ? 1 : 0
  name             = "kyverno"
  repository       = "https://kyverno.github.io/kyverno/"
  chart            = "kyverno"
  namespace        = "kyverno"
  create_namespace = true
  version          = lookup(var.chart_versions, "kyverno", null)
}
