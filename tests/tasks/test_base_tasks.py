from tasks import base_tasks


def test_version_is_stored_with_the_source_identifier(monkeypatch):
    stored = []
    monkeypatch.setattr(base_tasks, 'store_workflow_version',
                        lambda version: stored.append(version) or 'https://tracker/1')
    metadata = base_tasks.add_workflow_versioning_url.fn(
        {}, {'source': {'provider': 'DataverseNL'}}, 'doi:10.34894/IXUUK9')
    assert stored == [{'source': {'provider': 'DataverseNL',
                                  'identifier': 'doi:10.34894/IXUUK9'}}]
    workflow = metadata['datasetVersion']['metadataBlocks']['provenance']['fields'][0]
    assert workflow['value']['workflowURI']['value'] == 'https://tracker/1'
