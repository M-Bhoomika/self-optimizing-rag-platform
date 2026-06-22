# Terraform Scaffold — RAG Platform

This directory contains a **template-only** Terraform layout. It has not been
applied to a cloud account from this repository.

## Layout

- `main.tf` — provider placeholders and module wiring
- `variables.tf` — input variables
- `outputs.tf` — exported endpoints

## Usage

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file=terraform.tfvars.example
```

Populate real values locally before any apply. Do not commit secrets.
