output "namespace" {
  value = kubernetes_namespace.ai_lab.metadata[0].name
}
