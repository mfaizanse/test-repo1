#!/bin/bash

git checkout -b test_branch

yq e '.global.images.mothership_reconciler.tag' values.yaml

yq e -i '.global.images.mothership_reconciler.tag = "cool123456"' values.yaml

git commit -m "dasda"

git push --set-upstream origin test_branch

gh pr create --base main --title "My first cli PR" --body "What did I do?"


git rev-parse --short HEAD


gh pr status --json state | jq '.currentBranch."state"'
"MERGED"