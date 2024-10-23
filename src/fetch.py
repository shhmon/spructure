import requests
import json

with open ('./config/query.txt', 'r') as f:
    query = f.read()

url = 'https://surfaces-graphql.splice.com/graphql'
authorization = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjR0NDJqSk1mV1YwaDk0eU9nTy1lQiJ9.eyJodHRwczovL3NwbGljZS5jb20vdXNlcl91dWlkIjoiYTBkNzYwYzQtMDc1MC00MzgwLTVjYmYtZTk4ODQyNTRjZjY2ZGY4ZTIwMCIsImlzcyI6Imh0dHBzOi8vYXV0aC5zcGxpY2UuY29tLyIsInN1YiI6ImF1dGgwfHNwbGljZS1hcGl8YTBkNzYwYzQtMDc1MC00MzgwLTVjYmYtZTk4ODQyNTRjZjY2ZGY4ZTIwMCIsImF1ZCI6WyJodHRwczovL3NwbGljZS5jb20iLCJodHRwczovL3NwbGljZS1wcm9kdWN0aW9uLnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3Mjk2ODczMzUsImV4cCI6MTcyOTc3MzczNSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF6cCI6Iko1SlZDR2tKbXRvTTVlaUk4TEdrUHVtYTkzZXhRVjhIIn0.kjBdv-9slb7OACChiaDe-ovPl7xw8G21UfeNCux6TJRreE3t2qF2bPuH04JXY074H1P2RzYBM9WerG8RHwIDZbrTX9ziMJ8LK7h4hG5D1JcqtZmVwEJM68NjLuypGoBbQM7GoSYSOsav4jn4vVajvZF3PPgJXbo1kT0pgFa9qPvDX-13etaJmvJPWSvifU3KdKgR663tGQTYwJjpWeotsGhk-u8Dk32T0IPDT6xQDuB-UxObGUFfYl6c6kUrkFsQABqxD7YSCBdGBgIgIGp2KExS61ivSYoGZQVIjNGuXOn2bzo4WqkY-DN3rJNqZcN05YKP911HrsfsUThB3nY_tw'

headers = {
    "Authorization": authorization,
    "Content-Type": "application/json"
}

body = {
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
        "tags": [], #"kicks", "drums"
        "tags_exclude": [],
        "filepath": "hello"
    }
}

def main():
    res = requests.post(url, json=body)
    data = json.loads(res.content)
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
