import os
import time

import requests

# Configuration
BASE_URL = "http://127.0.0.1:8080"
HEADERS = {"X-User-ID": "local_test_user"}
PDF_PATH = "data/input/北京地铁17号线工程土建施工08合同段“5.14”.pdf"


def test_get_projects():
    """Test querying project list"""
    url = f"{BASE_URL}/api/v1/projects/"
    response = requests.get(url, headers=HEADERS)
    print(f"GET /api/v1/projects/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Projects count: {data.get('count', 0)}")
        return True
    print(f"Error: {response.text}")
    return False


def test_create_project():
    """Test creating a project"""
    url = f"{BASE_URL}/api/v1/projects/"
    payload = {"name": "Test Project"}
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"POST /api/v1/projects/ - Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        project_id = data["id"]
        print(f"Created project ID: {project_id}")
        return project_id
    print(f"Error: {response.text}")
    return None


def test_get_project_detail(project_id):
    """Test getting project detail"""
    url = f"{BASE_URL}/api/v1/projects/{project_id}/"
    response = requests.get(url, headers=HEADERS)
    print(f"GET /api/v1/projects/{project_id}/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Project name: {data['name']}")
        return True
    print(f"Error: {response.text}")
    return False


def test_upload_pdf(project_id):
    """Test uploading PDF file"""
    url = f"{BASE_URL}/api/v1/upload/"
    if not os.path.exists(PDF_PATH):
        print(f"PDF file not found: {PDF_PATH}")
        return None
    with open(PDF_PATH, "rb") as f:
        files = {"file": f}
        data = {"project_id": project_id}
        response = requests.post(url, files=files, data=data, headers=HEADERS)
    print(f"POST /api/v1/upload/ - Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        file_id = data["id"]
        print(f"Uploaded file ID: {file_id}")
        return file_id
    print(f"Error: {response.text}")
    return None


def test_get_file_detail_and_poll(file_id):
    """Test getting file detail and polling for completion"""
    url = f"{BASE_URL}/api/v1/files/{file_id}/"
    start_time = time.time()
    timeout = 600  # 10 minutes
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=HEADERS)
        print(f"GET /api/v1/files/{file_id}/ - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            print(f"File status: {status}")
            if status == "completed":
                print("File processing completed!")
                return True
            if status == "failed":
                print(f"File processing failed: {data.get('error_message', '')}")
                return False
            if status == "completed":
                return True
            print("File still processing, waiting 10 seconds...")
            time.sleep(10)
        else:
            print(f"Error: {response.text}")
            return False
    print("Timeout: File processing did not complete within 10 minutes")
    return False


def main():
    print("Starting integration tests...")

    # Test 1: Get projects
    if not test_get_projects():
        return

    # Test 2: Create project
    project_id = test_create_project()
    if not project_id:
        return

    # Test 3: Get project detail
    if not test_get_project_detail(project_id):
        return

    # Test 4: Upload PDF
    file_id = test_upload_pdf(project_id)
    if not file_id:
        return

    # Test 5: Get file detail and poll
    if not test_get_file_detail_and_poll(file_id):
        return

    print("All integration tests passed!")


if __name__ == "__main__":
    main()
