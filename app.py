from flask import Flask, render_template, jsonify, request, send_file
import requests
import os
import json
import tempfile
import zipfile
from urllib.parse import quote

app = Flask(__name__)

PYPI_API_URL = "https://pypi.org/pypi/{package}/json"
SEARCH_API_URL = "https://pypi.org/search/"

PLATFORMS = {
    "Windows": ["win_amd64", "win32"],
    "Linux": ["manylinux1_x86_64", "manylinux2014_x86_64", "manylinux2014_aarch64"],
    "macOS": ["macosx_10_9_x86_64", "macosx_11_0_arm64", "macosx_14_0_arm64"]
}

PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

def get_latest_version(package_name):
    try:
        response = requests.get(PYPI_API_URL.format(package=package_name), timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['info']['version']
        return None
    except:
        return None

def get_package_info(package_name, version=None):
    try:
        url = PYPI_API_URL.format(package=package_name)
        if version:
            url += f"/{version}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def search_packages(query):
    try:
        from rank_bm25 import BM25Okapi
        response = requests.get(f"https://pypi.org/search/?q={quote(query)}", timeout=10)
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for item in soup.select('.package-snippet'):
                name = item.select_one('.package-snippet__name')
                version = item.select_one('.package-snippet__version')
                description = item.select_one('.package-snippet__description')
                if name:
                    results.append({
                        'name': name.get_text(strip=True),
                        'version': version.get_text(strip=True) if version else '',
                        'description': description.get_text(strip=True) if description else ''
                    })
            return results[:20]
        return []
    except Exception as e:
        return []

def get_download_urls(package_name, platform, python_version, version=None):
    package_info = get_package_info(package_name, version)
    if not package_info:
        return []

    version = version or package_info['info']['version']
    urls = []

    releases = package_info.get('releases', {})
    version_releases = releases.get(version, [])

    platform_map = {
        "win_amd64": "win",
        "win32": "win",
        "manylinux1_x86_64": "linux",
        "manylinux2014_x86_64": "linux",
        "manylinux2014_aarch64": "linux",
        "macosx_10_9_x86_64": "macosx",
        "macosx_11_0_arm64": "macosx",
        "macosx_14_0_arm64": "macosx"
    }

    target_platform = None
    for p in PLATFORMS:
        if platform in PLATFORMS[p]:
            target_platform = p
            break

    for release in version_releases:
        filename = release['filename'].lower()
        if any(p in filename for p in PLATFORMS.get(target_platform, [])):
            if python_version.replace('.', '') in filename or 'py3' in filename or 'py2' in filename or 'none' in filename:
                urls.append({
                    'filename': release['filename'],
                    'url': release['url'],
                    'size': release.get('size', 0)
                })

    if not urls:
        for release in version_releases:
            filename = release['filename'].lower()
            if any(p in filename for p in PLATFORMS.get(target_platform, [])):
                urls.append({
                    'filename': release['filename'],
                    'url': release['url'],
                    'size': release.get('size', 0)
                })

    return urls

@app.route('/')
def index():
    return render_template('index.html',
                         platforms=PLATFORMS,
                         python_versions=PYTHON_VERSIONS)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = search_packages(query)
    return jsonify(results)

@app.route('/api/package/<package_name>')
def api_package_info(package_name):
    info = get_package_info(package_name)
    if info:
        return jsonify({
            'name': info['info']['name'],
            'version': info['info']['version'],
            'description': info['info']['summary'],
            'home_page': info['info']['home_page'],
            'releases': list(info.get('releases', {}).keys())
        })
    return jsonify(None)

@app.route('/api/downloads')
def api_downloads():
    package = request.args.get('package', '')
    platform = request.args.get('platform', '')
    py_version = request.args.get('py_version', '')
    version = request.args.get('version', '')

    if not package or not platform:
        return jsonify({'error': 'Missing parameters'})

    urls = get_download_urls(package, platform, py_version, version)
    return jsonify({
        'urls': urls,
        'command': f'pip download {package}' + (f'=={version}' if version else '') + f' --platform {platform} --python-version {py_version.replace(".", "")} --only-binary=:all:'
    })

@app.route('/api/download-package', methods=['POST'])
def api_download_package():
    data = request.json
    package = data.get('package', '')
    version = data.get('version')
    platform = data.get('platform', 'win_amd64')
    py_version = data.get('py_version', '3.11')

    if not package:
        return jsonify({'error': 'Package name required'}), 400

    urls = get_download_urls(package, platform, py_version, version)
    if not urls:
        return jsonify({'error': 'No compatible package found'}), 404

    temp_dir = tempfile.mkdtemp()
    downloaded_files = []

    for url_info in urls[:5]:
        try:
            response = requests.get(url_info['url'], timeout=30)
            if response.status_code == 200:
                filename = os.path.join(temp_dir, url_info['filename'])
                with open(filename, 'wb') as f:
                    f.write(response.content)
                downloaded_files.append({
                    'filename': url_info['filename'],
                    'size': len(response.content),
                    'path': filename
                })
        except:
            continue

    if not downloaded_files:
        return jsonify({'error': 'Failed to download package'}), 500

    if len(downloaded_files) == 1:
        return send_file(downloaded_files[0]['path'],
                        as_attachment=True,
                        download_name=downloaded_files[0]['filename'])

    zip_path = os.path.join(temp_dir, f'{package}_{version or "latest"}_packages.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in downloaded_files:
            zipf.write(f['path'], f['filename'])

    return send_file(zip_path,
                    as_attachment=True,
                    download_name=f'{package}_{version or "latest"}_packages.zip')

@app.route('/api/commands')
def api_commands():
    packages = request.args.get('packages', '')
    platform = request.args.get('platform', '')
    py_version = request.args.get('py_version', '')

    if not packages or not platform:
        return jsonify({'error': 'Missing parameters'})

    package_list = [p.strip() for p in packages.split(',') if p.strip()]

    download_cmd = f"pip download {' '.join(package_list)} --platform {platform} --python-version {py_version.replace('.', '')} --only-binary=:all:"
    install_cmd = f"pip install --no-index --find-links=/path/to/wheels {' '.join(package_list)}"

    return jsonify({
        'download_command': download_cmd,
        'install_command': install_cmd,
        'packages': package_list,
        'platform': platform,
        'python_version': py_version
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)