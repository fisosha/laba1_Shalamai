#!/usr/bin/env bash
# Розгортання PARCS-Python у Microsoft Azure.
# Запускати в Azure Cloud Shell (Bash): bash cloud/azure_deploy.sh
set -euo pipefail

LOCATION="${LOCATION:-denmarkeast}"
SIZE="${SIZE:-Standard_A1_v2}"
MASTER_SIZE="${MASTER_SIZE:-Standard_B1s}"
WORKERS="${WORKERS:-4}"
RG="parcs-rg"
IMAGE="hummer12007/parcs-node"

az group create --name "$RG" --location "$LOCATION" -o none
az network vnet create --resource-group "$RG" --name parcs-vnet --subnet-name default -o none

# Студентська підписка дає лише 3 публічні IP. Публічний IP має тільки master (для веб-інтерфейсу),
# а воркери виходять в інтернет (щоб завантажити Docker-образ) через один NAT-шлюз.
az network public-ip create --resource-group "$RG" --name parcs-nat-ip --sku Standard -o none
az network nat gateway create --resource-group "$RG" --name parcs-nat --public-ip-addresses parcs-nat-ip -o none
az network vnet subnet update --resource-group "$RG" --vnet-name parcs-vnet --name default --nat-gateway parcs-nat -o none

make_init() {
  cat <<INIT
#!/bin/bash
apt-get update
apt-get install -y docker.io
docker run -d --restart unless-stopped --network host -e PARCS_ARGS="$1" $IMAGE
INIT
}

make_init "master" > master-init.sh
az vm create --resource-group "$RG" --name master --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts:latest --size "$MASTER_SIZE" \
  --admin-username azureuser --generate-ssh-keys \
  --vnet-name parcs-vnet --subnet default --custom-data master-init.sh -o none
az vm open-port --resource-group "$RG" --name master --port 8080 -o none

MASTER_IP=$(az vm list-ip-addresses -g "$RG" -n master \
  --query "[0].virtualMachine.network.privateIpAddresses[0]" -o tsv)
MASTER_PUBLIC=$(az vm list-ip-addresses -g "$RG" -n master \
  --query "[0].virtualMachine.network.publicIpAddresses[0].ipAddress" -o tsv)

make_init "worker $MASTER_IP" > worker-init.sh
for i in $(seq 1 "$WORKERS"); do
  az vm create --resource-group "$RG" --name "worker$i" --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts:latest --size "$SIZE" \
    --admin-username azureuser --generate-ssh-keys --public-ip-address "" \
    --vnet-name parcs-vnet --subnet default --custom-data worker-init.sh -o none
done

az vm list --resource-group "$RG" --show-details \
  --query "[].{name:name, privateIp:privateIps, publicIp:publicIps, state:powerState}" -o table

echo
echo "Веб-інтерфейс PARCS: http://$MASTER_PUBLIC:8080"
echo "Перші хвилини 3-5 машини встановлюють Docker, потім воркери з'являться на сторінці Workers."
echo "Після замірів обов'язково: bash cloud/azure_cleanup.sh"
