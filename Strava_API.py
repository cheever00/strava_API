import threading
import requests
import time
import json
import queue

# Replace YOUR_CLIENT_ID, YOUR_CLIENT_SECRET, and YOUR_REFRESH_TOKEN
# with your Strava API client ID, client secret, and refresh token
CLIENT_ID = ""
CLIENT_SECRET = ""
REFRESH_TOKEN = ""
USER_ID = 
session = requests.Session()

# Function to refresh the access token using the refresh token
def refresh_access_token():
    # Set up the API request to refresh the access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data=data
    )
    # Return the new access token
    return response.json()["access_token"]

# Function to make a single API call to retrieve a page of activities
def get_activity_page(access_token, start_page, end_page, session, result_queue):
    # Set up a list to store the results of the API calls
    activities = []
    # Set up a session to reuse the same HTTP connection
    session = requests.Session()

    # Loop through the pages in the range
    for page in range(start_page, end_page + 1):
        # Set up the API request
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        params = {
            "page": page,
            "per_page": 200
        }
        response = session.get(
            f"https://www.strava.com/api/v3/athletes/{USER_ID}/activities",
            headers=headers,
            params=params
        )

        try:
            # Check the status code of the response
            if response.status_code == 401:
                # The access token has expired, so refresh it and try again
                access_token = refresh_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                response = session.get(
                    f"https://www.strava.com/api/v3/athletes/{USER_ID}/activities",
                    headers=headers,
                    params=params
                )
            # Append the response from the API to the list of activities
            activities += response.json()
        except json.decoder.JSONDecodeError as e:
            # Log a message to indicate that the response was empty
            print(f"Empty response for page {page}")
    
    # Put the list of activities in the result queue
    result_queue.put(activities)

# Function to make multiple API calls concurrently
def get_all_activities():
    # Set up a list to store the results of the API calls
    all_activities = []
    # Set up a list of threads
    threads = []
    # Set up a queue to collect the results from the threads
    result_queue = queue.Queue()
    # Set the number of threads to create
    num_threads = 10
    # Set the number of pages to retrieve per thread
    pages_per_thread = 1
    # Set the initial page to retrieve
    page = 1
    # Set up a session to reuse the same HTTP connection
    session = requests.Session()
    # Refresh the access token
    access_token = refresh_access_token()
    # Continue making API calls as long as there are more pages to retrieve
    while True:
        # Set the flag to false initially
        more_pages = False
        # Create and start the threads
        for i in range(num_threads):
            # Calculate the range of pages for this thread to retrieve
            start_page = page + i * pages_per_thread
            end_page = start_page + pages_per_thread - 1
            # Create the thread
            thread = threading.Thread(target=get_activity_page, args=(access_token, start_page, end_page, session, result_queue))
            # Add the thread to the list
            threads.append(thread)
            # Start the thread
            thread.start()
        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        # Collect the results from the queue
        while not result_queue.empty():
            result = result_queue.get()
            # Check if the result is None
            if result is not None:
                # Append the result to the list of activities
                all_activities += result
        # Reset the list of threads
        threads = []
        # Update the page counter
        page += num_threads * pages_per_thread
        # Check if there are more pages to retrieve
        if len(all_activities) >= page * 200:
            more_pages = True
        else:
            more_pages = False
        if not more_pages:
            break
            # Return the list of all activities
    return all_activities
all_activities = get_all_activities()
with open("activities.json", "w") as f:
    json.dump(all_activities, f)

# Print a message to indicate that the file has been saved
print("Activities saved to activities.json")
#print(all_activities)
