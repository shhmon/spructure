import click
import requests
import json

with open ('./config/query.txt', 'r') as f:
    query = f.read()

url = 'https://surfaces-graphql.splice.com/graphql'

def get_body(search: str, tags=[]):
    return {
        "operationName": "SamplesSearch",
        "query": query,
        "variables": {
            "attributes": [],
            "bundled_content_daws": [],
            "includeSubscriberOnlyResults": False,
            "legacy": True,
            "limit": 50,
            "order": "DESC",
            "sort": "popularity",
            "tags": tags,
            "tags_exclude": [],
            "filepath": search
        }
    }

@click.command()
def main():
    body = get_body("Hello")
    res = requests.post(url, json=body)

    data = json.loads(res.content)
    print(data)
    items = data.get('data').get('assetsSearch').get('items')

    item = items[10]
    files = item.get('files')
    for file in files:
        if file.get('asset_file_type_slug') == 'preview_mp3':
            file_url = file.get('url')
            print(file_url)
            print()
            print('\n\n'.join('\n\n'.join(file_url.split('?')).split('&')))

if __name__ == "__main__":
    main()
