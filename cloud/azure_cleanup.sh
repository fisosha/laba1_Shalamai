#!/usr/bin/env bash
# Видаляє всі машини, мережу і диски, створені azure_deploy.sh.
az group delete --name parcs-rg --yes
az group list -o table
