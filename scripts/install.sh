#!/bin/bash
echo "Installing Eye..."
make deps
make build
sudo make install
echo "✅ Installed"