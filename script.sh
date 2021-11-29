#!/bin/bash

export BRANCH_NAME=test_branch
export RECONCILER_IMAGE_TAG=$(git rev-parse --short HEAD)
export VALUES_YAML_PATH="values.yaml"

echo ${RECONCILER_IMAGE_TAG}

git checkout -B ${BRANCH_NAME}

# yq e '.global.images.mothership_reconciler.tag' values.yaml

yq e -i '.global.images.mothership_reconciler.tag = "'"${RECONCILER_IMAGE_TAG}"'"' ${VALUES_YAML_PATH}
yq e -i '.global.images.component_reconciler.tag = "'"${RECONCILER_IMAGE_TAG}"'"' ${VALUES_YAML_PATH}

git commit -a -m "Bumped reconcile images to ${RECONCILER_IMAGE_TAG}"

git push --set-upstream origin ${BRANCH_NAME}

# gh pr status --json state | jq '.currentBranch."state"'

# gh pr create --base main --title "My first cli PR" --body "What did I do?"


# git rev-parse --short HEAD



#"MERGED"