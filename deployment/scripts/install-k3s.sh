#!/bin/bash
# =============================================================================
# Install k3s (Lightweight Kubernetes) on Oracle Cloud Always Free
# Production-ready Kubernetes using only 512MB RAM
# =============================================================================

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Installing k3s (Lightweight Kubernetes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if running on Oracle Cloud (ARM64)
if [ "$(uname -m)" != "aarch64" ]; then
    echo "⚠️  Warning: Not running on ARM64 architecture"
    echo "This script is optimized for Oracle Cloud Ampere A1 instances"
fi

# =============================================================================
# STEP 1: System Preparation
# =============================================================================
echo ""
echo "📋 Step 1: Preparing system..."

# Update system
sudo apt-get update
sudo apt-get install -y curl wget

# Enable IP forwarding (required for Kubernetes)
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# =============================================================================
# STEP 2: Install k3s
# =============================================================================
echo ""
echo "📦 Step 2: Installing k3s..."

# Install k3s with customizations
curl -sfL https://get.k3s.io | sh -s - \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --disable servicelb \
    --flannel-backend=vxlan \
    --node-name oracle-k3s-master

# Wait for k3s to be ready
echo ""
echo "⏳ Waiting for k3s to be ready..."
sleep 10

# Check k3s status
sudo systemctl status k3s --no-pager

# =============================================================================
# STEP 3: Configure kubectl
# =============================================================================
echo ""
echo "🔧 Step 3: Configuring kubectl..."

# Create .kube directory
mkdir -p ~/.kube

# Copy k3s config to standard location
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Set KUBECONFIG environment variable
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
export KUBECONFIG=~/.kube/config

# Install kubectl (if not already installed)
if ! command -v kubectl &> /dev/null; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
fi

# =============================================================================
# STEP 4: Install Helm (Kubernetes Package Manager)
# =============================================================================
echo ""
echo "📦 Step 4: Installing Helm..."

curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# =============================================================================
# STEP 5: Install nginx-ingress (for external access)
# =============================================================================
echo ""
echo "🌐 Step 5: Installing nginx-ingress controller..."

# Add nginx-ingress Helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install nginx-ingress
helm install nginx-ingress ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.service.type=NodePort \
    --set controller.service.nodePorts.http=30080 \
    --set controller.service.nodePorts.https=30443

# =============================================================================
# STEP 6: Install cert-manager (for SSL certificates)
# =============================================================================
echo ""
echo "🔒 Step 6: Installing cert-manager (Let's Encrypt SSL)..."

# Add cert-manager Helm repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --set installCRDs=true

# =============================================================================
# STEP 7: Install Metrics Server (for kubectl top)
# =============================================================================
echo ""
echo "📊 Step 7: Installing Metrics Server..."

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for k3s
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# =============================================================================
# STEP 8: Create namespaces
# =============================================================================
echo ""
echo "📁 Step 8: Creating namespaces..."

kubectl create namespace production || true
kubectl create namespace staging || true
kubectl create namespace monitoring || true

# =============================================================================
# STEP 9: Install Prometheus & Grafana (Monitoring)
# =============================================================================
echo ""
echo "📈 Step 9: Installing Prometheus & Grafana..."

# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set prometheus.prometheusSpec.retention=30d \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi \
    --set grafana.adminPassword=admin \
    --set grafana.service.type=NodePort \
    --set grafana.service.nodePort=30300

# =============================================================================
# STEP 10: Verification
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ k3s Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display cluster info
echo "📊 Cluster Information:"
kubectl cluster-info
echo ""

# Display nodes
echo "🖥️  Nodes:"
kubectl get nodes -o wide
echo ""

# Display all pods
echo "🐳 System Pods:"
kubectl get pods --all-namespaces
echo ""

# Display services
echo "🌐 Services:"
kubectl get svc --all-namespaces
echo ""

# Display ingress
echo "🔗 Ingress Controllers:"
kubectl get svc -n ingress-nginx
echo ""

# Display monitoring
echo "📈 Monitoring:"
kubectl get svc -n monitoring
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 k3s is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Access Grafana: http://your-ip:30300 (admin/admin)"
echo "2. Configure Oracle firewall to allow ports 30080, 30443, 30300"
echo "3. Deploy your applications with kubectl"
echo ""
echo "🔧 Useful commands:"
echo "  kubectl get pods --all-namespaces     # List all pods"
echo "  kubectl get nodes                     # List nodes"
echo "  kubectl get svc --all-namespaces      # List services"
echo "  kubectl top nodes                     # Node resource usage"
echo "  kubectl top pods --all-namespaces     # Pod resource usage"
echo ""
echo "📖 k3s documentation: https://docs.k3s.io/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
