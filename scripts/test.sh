#!/bin/bash
echo "Testing Eye..."

# Start server
export EYE_AUTH_TOKEN="test-token"
./bin/eye-server &
SERVER_PID=$!

sleep 3

# Test
curl -s http://localhost:8080/health

# Cleanup
kill $SERVER_PID