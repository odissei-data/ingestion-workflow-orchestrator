# JMESPath queries for querying values in json metadata: https://jmespath.org/
CBS_ID_QUERY = "datasetVersion.metadataBlocks.citation.fields[?typeName == 'otherId'].value[*].otherIdValue.value[] | [0]"
DIST_DATE_QUERY = "datasetVersion.metadataBlocks.citation.fields[?typeName == 'distributionDate'].value | [0]"