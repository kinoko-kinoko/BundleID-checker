import os
import json
import requests
import time
import random
from datetime import datetime
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
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    apps_to_process = []
    is_dict_format = False

    if isinstance(data, dict) and 'apps' in data and isinstance(data['apps'], list):
        apps_to_process = data['apps']
        is_dict_format = True
    elif isinstance(data, list):
        apps_to_process = data
    else:
        print(f"Warning: Skipping {filepath} due to unrecognized JSON format.")
        return data, [], 0

    total_apps_count = len(apps_to_process)

    for app in apps_to_process:
        app_name = app.get('name')
        if not app_name:
            continue

        # Check if any of the required fields are empty
        if not all([app.get('id'), app.get('bundleID'), app.get('iconUrlSmall'), app.get('iconUrlLarge')]):
            print(f"Fetching info for {app_name}...")
            # API制限を避けるために3〜5秒のランダムな待機
            wait_time = random.uniform(3, 5)
            print(f"Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)

            info = search_app_info(app_name)

            if info:
                app['id'] = info.get('id') or app.get('id')
                app['bundleID'] = info.get('bundleID') or app.get('bundleID')
                app['iconUrlSmall'] = info.get('iconUrlSmall') or app.get('iconUrlSmall')
                app['iconUrlLarge'] = info.get('iconUrlLarge') or app.get('iconUrlLarge')
                print(f"API call for {app_name} processed.")

    # After attempting to update all apps, check which ones are still incomplete.
    not_found_apps = []
    for app in apps_to_process:
        if not all([app.get('id'), app.get('bundleID'), app.get('iconUrlSmall'), app.get('iconUrlLarge')]):
            not_found_apps.append({'name': app.get('name', 'Unknown'), 'id': app.get('id', '')})
            print(f"Info for '{app.get('name')}' remains incomplete.")

    if is_dict_format:
        data['apps'] = apps_to_process
        return data, not_found_apps, total_apps_count
    else:
        return apps_to_process, not_found_apps, total_apps_count

def main():
    """
    メイン処理
    """
    if not os.path.exists(DONE_DIR):
        os.makedirs(DONE_DIR)

    today_str = datetime.now().strftime('%Y%m%d')

    for filename in os.listdir(SEARCH_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(SEARCH_DIR, filename)
            print(f"Processing {filepath}...")

            updated_data, not_found_apps, total_apps_count = process_json_file(filepath)

            base_filename, ext = os.path.splitext(filename)

            # Add date to the output filename
            new_filename = f"{base_filename}_{today_str}{ext}"
            done_filepath = os.path.join(DONE_DIR, new_filename)
            with open(done_filepath, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
            print(f"Saved updated JSON to {done_filepath}")

            # Write not found apps to a text file with date
            if not_found_apps:
                log_filename = f"{base_filename}_{today_str}_not_found.txt"
                log_filepath = os.path.join(NOT_FOUND_LOG_DIR, log_filename)
                with open(log_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Total apps processed: {total_apps_count}\n")
                    f.write(f"Apps not found: {len(not_found_apps)}\n\n")
                    f.write("Information could not be found for the following apps:\n")
                    for app in not_found_apps:
                        f.write(f"ID: {app['id']}, Name: {app['name']}\n")
                print(f"Saved not-found log to {log_filepath}")

if __name__ == '__main__':
    main()