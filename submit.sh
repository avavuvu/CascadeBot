#!/bin/bash


set -e

mkdir -p submissions

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
ZIP_NAME="submissions/cascade_${TIMESTAMP}.zip"

zip -r "$ZIP_NAME" "agent" "referee"

echo "Created: $ZIP_NAME"
