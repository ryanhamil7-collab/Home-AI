#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
fi

log "Checking dependencies..."
for cmd in lb debootstrap; do
    if ! command -v $cmd &> /dev/null; then
        error "$cmd is not installed. Run: sudo apt install live-build debootstrap"
    fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ISO_DIR="$PROJECT_ROOT/iso"
BUILD_DIR="$PROJECT_ROOT/build"
OUTPUT_DIR="$PROJECT_ROOT/output"

log "Project root: $PROJECT_ROOT"
log "ISO config: $ISO_DIR"
log "Build directory: $BUILD_DIR"
log "Output directory: $OUTPUT_DIR"

if [ -d "$BUILD_DIR" ]; then
    warn "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

log "Copying ISO configuration..."
cp -r "$ISO_DIR"/* "$BUILD_DIR/"

cd "$BUILD_DIR"

log "Configuring live-build..."
lb config \
    --architectures amd64 \
    --distribution noble \
    --archive-areas "main restricted universe multiverse" \
    --mirror-bootstrap "http://archive.ubuntu.com/ubuntu/" \
    --mirror-binary "http://archive.ubuntu.com/ubuntu/" \
    --apt-recommends false \
    --binary-images iso-hybrid \
    --bootappend-live "boot=live components quiet splash" \
    --debian-installer false \
    --iso-application "Home AI OS" \
    --iso-publisher "Home AI Project" \
    --iso-volume "HomeAI-OS" \
    --memtest none

log "Building ISO (this may take 30-60 minutes)..."
lb build 2>&1 | tee "$OUTPUT_DIR/build.log"

if [ ! -f live-image-amd64.hybrid.iso ]; then
    error "ISO build failed. Check $OUTPUT_DIR/build.log for details"
fi

ISO_NAME="homeai-os-$(date +%Y%m%d).iso"
log "Moving ISO to output directory..."
mv live-image-amd64.hybrid.iso "$OUTPUT_DIR/$ISO_NAME"

log "Calculating checksums..."
cd "$OUTPUT_DIR"
sha256sum "$ISO_NAME" > "$ISO_NAME.sha256"
md5sum "$ISO_NAME" > "$ISO_NAME.md5"

log "Build complete!"
echo ""
echo "ISO file: $OUTPUT_DIR/$ISO_NAME"
echo "Size: $(du -h "$OUTPUT_DIR/$ISO_NAME" | cut -f1)"
echo "SHA256: $(cat "$OUTPUT_DIR/$ISO_NAME.sha256" | cut -d' ' -f1)"
echo ""
echo "To test in VM, run: ./scripts/run-vm.sh"
echo "To write to USB, run: sudo dd if=$OUTPUT_DIR/$ISO_NAME of=/dev/sdX bs=4M status=progress"
