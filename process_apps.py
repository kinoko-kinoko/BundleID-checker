import os
import json
import requests
import time

SEARCH_DIR = 'search'
DONE_DIR = 'done'
NOT_FOUND_LOG_DIR = 'done'
API_ENDPOINT = 'https://itunes.apple.com/search'

def search_app_info(app_name):
    """
    iTunes Search APIを使用してアプリ情報を検索する
    """
    params = {
        'term': app_name,
        'country': 'jp',
        'media': 'software',
        'entity': 'software',
        'limit': 1  # 最も関連性の高い結果を1つだけ取得
    }
    try:
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        data = response.json()
        if data['resultCount'] > 0:
            result = data['results'][0]
            return {
                'id': result.get('trackId', ''),
                'bundleID': result.get('bundleId', ''),
                'iconUrlSmall': result.get('artworkUrl60', ''),
                'iconUrlLarge': result.get('artworkUrl100', '')
            }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {app_name}: {e}")
    return None

def process_json_file(filepath):
    """
    単一のJSONファイルを処理する
    """
    not_found_apps = []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated_apps = []
    if 'apps' in data and isinstance(data['apps'], list):
        for app in data['apps']:
            app_name = app.get('name')
            if not app_name:
                updated_apps.append(app)
                continue

            # Check if any of the required fields are empty
            if not all([app.get('id'), app.get('bundleID'), app.get('iconUrlSmall'), app.get('iconUrlLarge')]):
                print(f"Fetching info for {app_name}...")
                info = search_app_info(app_name)
                time.sleep(1) # API制限を避けるために1秒待機

                if info:
                    app['id'] = info.get('id', app.get('id'))
                    app['bundleID'] = info.get('bundleID', app.get('bundleID'))
                    app['iconUrlSmall'] = info.get('iconUrlSmall', app.get('iconUrlSmall'))
                    app['iconUrlLarge'] = info.get('iconUrlLarge', app.get('iconUrlLarge'))
                    print(f"Successfully updated {app_name}.")
                else:
                    not_found_apps.append({'name': app_name, 'id': app.get('id', '')})
                    print(f"Could not find info for {app_name}.")

            updated_apps.append(app)

    data['apps'] = updated_apps
    return data, not_found_apps

def main():
    """
    メイン処理
    """
    if not os.path.exists(DONE_DIR):
        os.makedirs(DONE_DIR)

    for filename in os.listdir(SEARCH_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(SEARCH_DIR, filename)
            print(f"Processing {filepath}...")

            updated_data, not_found_apps = process_json_file(filepath)

            # Write updated JSON to done directory
            done_filepath = os.path.join(DONE_DIR, filename)
            with open(done_filepath, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
            print(f"Saved updated JSON to {done_filepath}")

            # Write not found apps to a text file
            if not_found_apps:
                log_filename = os.path.splitext(filename)[0] + '_not_found.txt'
                log_filepath = os.path.join(NOT_FOUND_LOG_DIR, log_filename)
                with open(log_filepath, 'w', encoding='utf-8') as f:
                    f.write("Information could not be found for the following apps:\n")
                    for app in not_found_apps:
                        f.write(f"ID: {app['id']}, Name: {app['name']}\n")
                print(f"Saved not-found log to {log_filepath}")

if __name__ == '__main__':
    main()