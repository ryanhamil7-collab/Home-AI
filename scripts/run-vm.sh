#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/output"

ISO_FILE=$(ls -t "$OUTPUT_DIR"/homeai-os-*.iso 2>/dev/null | head -1)

if [ -z "$ISO_FILE" ]; then
    echo "No ISO found in $OUTPUT_DIR"
    echo "Build one first with: sudo ./scripts/build-iso.sh"
    exit 1
fi

log "Using ISO: $ISO_FILE"

if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "QEMU is not installed."
    echo "Install with: sudo apt install qemu-system-x86"
    exit 1
fi

VM_NAME="homeai-os-test"
VM_MEMORY="4096"  # 4GB RAM
VM_CPUS="4"
VM_DISK_SIZE="20G"
VM_DISK="$OUTPUT_DIR/$VM_NAME.qcow2"

if [ ! -f "$VM_DISK" ]; then
    log "Creating virtual disk ($VM_DISK_SIZE)..."
    qemu-img create -f qcow2 "$VM_DISK" "$VM_DISK_SIZE"
fi

KVM_OPTS=""
if [ -e /dev/kvm ]; then
    log "KVM acceleration available"
    KVM_OPTS="-enable-kvm"
else
    warn "KVM not available, VM will be slower"
fi

log "Starting VM..."
log "Memory: ${VM_MEMORY}MB, CPUs: $VM_CPUS"
log "Press Ctrl+Alt+G to release mouse/keyboard"
log "Press Ctrl+Alt+F to toggle fullscreen"

qemu-system-x86_64 \
    $KVM_OPTS \
    -m "$VM_MEMORY" \
    -smp "$VM_CPUS" \
    -cdrom "$ISO_FILE" \
    -hda "$VM_DISK" \
    -boot d \
    -vga virtio \
    -display gtk \
    -device virtio-net-pci,netdev=net0 \
    -netdev user,id=net0 \
    -usb \
    -device usb-tablet \
    -name "$VM_NAME"

log "VM exited"
