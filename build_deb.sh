#!/bin/bash
set -e

PKG_NAME="pdf2ocr"
VERSION="1.0.0"
ARCH="all"
BUILD_DIR="${PKG_NAME}_${VERSION}"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/local/bin"
mkdir -p "$BUILD_DIR/opt/$PKG_NAME"

# Copy files
cp -r pdf2ocr "$BUILD_DIR/opt/$PKG_NAME/"
cp debian/control "$BUILD_DIR/DEBIAN/"
[ -f debian/postinst ] && cp debian/postinst "$BUILD_DIR/DEBIAN/"
chmod 755 "$BUILD_DIR/DEBIAN"/*

# Create launcher script
cat << EOF > "$BUILD_DIR/usr/local/bin/$PKG_NAME"
#!/bin/bash
python3 /opt/$PKG_NAME/pdf2ocr/main.py "\$@"
EOF

chmod +x "$BUILD_DIR/usr/local/bin/$PKG_NAME"

# Build the package
dpkg-deb --build "$BUILD_DIR"

echo "✅ Package built: ${BUILD_DIR}.deb"
