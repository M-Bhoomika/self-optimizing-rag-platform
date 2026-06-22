terraform {
  required_version = ">= 1.5.0"
}

variable "project_name" {
  type    = string
  default = "rag-platform"
}

output "project_name" {
  value = var.project_name
}
