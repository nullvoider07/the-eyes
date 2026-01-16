#!/bin/bash
set -e

VERSION=$1
REPO="nullvoider07/the-eye"

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/publish_release.sh <version>"
    echo "Example: ./scripts/publish_release.sh 0.1.0"
    exit 1
fi

# Ensure clean working directory
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory not clean"
    exit 1
fi

echo "Creating release v${VERSION}..."

# Update version in files
sed -i "s/version=\".*\"/version=\"${VERSION}\"/" setup.py
sed -i "s/__version__ = \".*\"/__version__ = \"${VERSION}\"/" eye/__init__.py

# Commit version bump
git add setup.py eye/__init__.py
git commit -m "Bump version to ${VERSION}"

# Create tag
git tag -a "v${VERSION}" -m "Release v${VERSION}"

# Push
git push origin main
git push origin "v${VERSION}"

echo "✅ Release v${VERSION} created!"
echo ""
echo "GitHub Actions will now:"
echo "  1. Build all platform binaries"
echo "  2. Create GitHub release"
echo "  3. Upload release assets"
echo "  4. Publish to PyPI (if configured)"
echo ""
echo "Monitor: https://github.com/$REPO/actions"