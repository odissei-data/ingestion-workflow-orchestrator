#!/bin/sh
# Download each mapping and its template at the tag listed in resources/mapping-versions.
set -eu
cd "$(dirname "$0")/resources"
mkdir -p mappings templates
url=https://raw.githubusercontent.com/odissei-data/mappings/refs/tags
while read -r name version; do
    curl -fsS -o "mappings/$name-mapping.json" \
        "$url/$name/$version/mappings/$name-mapping.json"
    curl -fsS -o "templates/${name}_dataverse_template.json" \
        "$url/$name/$version/templates/${name}_dataverse_template.json"
done < mapping-versions
