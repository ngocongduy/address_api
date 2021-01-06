#!/bin/bash
reg="*[0-9]_*"
echo You should delete item if it is not in: $reg
echo All items:
for entry in ./*; do
  echo $entry
done
