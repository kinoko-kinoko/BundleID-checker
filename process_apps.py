import os
import json
import requests
import time
import random
from datetime import datetime
SEARCH_DIR = 'search'
DONE_DIR = 'done'
NOT_FOUND_LOG_DIR = 'done'
LOOKUP_API_ENDPOINT = 'https://itunes.apple.com/lookup'
SEARCH_API_ENDPOINT = 'https://itunes.apple.com/search'

def get_app_info(app_id=None, app_name=None):
    """
    iTunes APIを使用してアプリ情報を検索する (lookup or search)
    """
    if app_id:
        print(f"Looking up app info with ID: {app_id}")
        params = {'id': app_id, 'country': 'jp', 'entity': 'software'}
        api_url = LOOKUP_API_ENDPOINT
    elif app_name:
        print(f"Searching for app info with name: {app_name}")
        params = {'term': app_name, 'country': 'jp', 'media': 'software', 'entity': 'software', 'limit': 1}
        api_url = SEARCH_API_ENDPOINT
    else:
        return None

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('resultCount', 0) > 0:
            result = data['results'][0]
            return {
                'id': result.get('trackId'),
                'bundleID': result.get('bundleId'),
                'iconUrlSmall': result.get('artworkUrl60'),
                'iconUrlLarge': result.get('artworkUrl100')
            }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for app ({app_id or app_name}): {e}")
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
        # Check if any of the required fields are empty
        if not all(app.get(key) for key in ['id', 'bundleID', 'iconUrlSmall', 'iconUrlLarge']):
            wait_time = random.uniform(3, 5)
            print(f"Waiting for {wait_time:.2f} seconds before next API call...")
            time.sleep(wait_time)

            info = get_app_info(app_id=app.get('id'), app_name=app.get('name'))

            if info:
                app['id'] = info.get('id') or app.get('id')
                app['bundleID'] = info.get('bundleID') or app.get('bundleID')
                app['iconUrlSmall'] = info.get('iconUrlSmall') or app.get('iconUrlSmall')
                app['iconUrlLarge'] = info.get('iconUrlLarge') or app.get('iconUrlLarge')
                print(f"API call for '{app.get('name')}' processed.")

    # After attempting to update all apps, check which ones are still incomplete.
    not_found_apps = []
    for app in apps_to_process:
        missing_fields = []
        if not app.get('id'): missing_fields.append('id')
        if not app.get('bundleID'): missing_fields.append('bundleID')
        if not app.get('iconUrlSmall'): missing_fields.append('iconUrlSmall')
        if not app.get('iconUrlLarge'): missing_fields.append('iconUrlLarge')

        if missing_fields:
            details = {
                'name': app.get('name', 'Unknown'),
                'id': app.get('id', ''),
                'missing': ', '.join(missing_fields)
            }
            not_found_apps.append(details)
            print(f"Info for '{details['name']}' remains incomplete. Missing: {details['missing']}")

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
                    f.write(f"Apps not found or incomplete: {len(not_found_apps)}\n\n")
                    f.write("The following apps have missing information:\n")
                    for app in not_found_apps:
                        f.write(f"ID: {app['id']}, Name: {app['name']}, Missing fields: {app['missing']}\n")
                print(f"Saved not-found log to {log_filepath}")

if __name__ == '__main__':
    main()