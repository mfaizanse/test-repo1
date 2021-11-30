#!/bin/bash

export BRANCH_NAME="reconciler_image_bump"
export RECONCILER_IMAGE_TAG=$(git rev-parse --short HEAD)
export VALUES_YAML_PATH="values.yaml"

echo ${RECONCILER_IMAGE_TAG}

git config --global user.email "kyma.bot@sap.com"
git config --global user.name "Kyma Bot"

git checkout -B ${BRANCH_NAME}

# yq e '.global.images.mothership_reconciler.tag' values.yaml

yq e -i '.global.images.mothership_reconciler.tag = "'"${RECONCILER_IMAGE_TAG}"'"' ${VALUES_YAML_PATH}
yq e -i '.global.images.component_reconciler.tag = "'"${RECONCILER_IMAGE_TAG}"'"' ${VALUES_YAML_PATH}

git commit -a -m "Bumped reconcile images to ${RECONCILER_IMAGE_TAG}"

git push --set-upstream origin ${BRANCH_NAME}

PR_STATUS=$(gh pr status --json state | jq -r '.currentBranch."state"')

if [[ ! ${PR_STATUS} = "OPEN" ]]; then
    gh pr create --base main --title "Reconciler image bump [Kyma-bot]" --body "Bumped reconciler images." --label bug
else
    echo "Pull Request (PR) already exists."
fi

PR_URL=$(gh pr status --json url | jq -r '.currentBranch."url"')
echo "Pull Request (PR): ${PR_URL}"

#"MERGED", "OPEN"

# eu.gcr.io/kyma-project/test-infra/prow-tools:v20211110-ab51bd20
# eu.gcr.io/kyma-project/test-infra/kyma-integration:v20211104-fac1690a
# eu.gcr.io/kyma-project/test-infra/buildpack-golang:v20211110-ab51bd20

# install yq and gh commands