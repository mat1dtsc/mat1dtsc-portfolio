#!/bin/bash
# Generate mapbox-config.js from Vercel environment variable
echo "window.MAPBOX_TOKEN = '${MAPBOX_TOKEN}';" > projects/simel-mercado-laboral/demo/mapbox-config.js
