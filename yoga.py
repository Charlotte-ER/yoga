import argparse, sys, requests, webbrowser
import os

from googleapiclient.discovery import build
import re
import math
import random

def main():
    channel_name = 'yogawithadriene'

    max_playtime = validate(get_user_input())

    with build('youtube', 'v3', developerKey=os.environ.get('YT_API_KEY')) as youtube:
        uploads_playlist_id = get_uploads_playlist_from_channel_name(youtube, channel_name)
        all_channel_videos = get_videos_in_playlist(youtube, uploads_playlist_id)
        videos = get_videos_of_correct_length(youtube, all_channel_videos, max_playtime)

    random_video = random.choice(list(videos))
    url = f'https://www.youtube.com/watch?v={random_video}'

    if check_link(url):
        webbrowser.open_new(url)


def get_user_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n')
    args = parser.parse_args()
    return args.n


def validate(str):
    try:
        n = int(str)
    except ValueError:
        sys.exit("Enter time in minutes")
    if n <= 0:
        sys.exit("No time!")
    return n


def get_uploads_playlist_from_channel_name(youtube, channel_name):
    """Given channel name, return id of uploads playlist."""
    request = youtube.channels().list(part='contentDetails', forUsername=channel_name)
    response = request.execute()
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def get_videos_in_playlist(youtube, playlist_id):
    """Given a playlist id, returns list of videos in playlist."""
    nextPageToken = None
    videos = []
    while True:
        request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=nextPageToken
            )
        response = request.execute()

        for item in response['items']:
            videos.append(item['contentDetails']['videoId'])
        nextPageToken = response.get('nextPageToken')
        
        if not nextPageToken:
            break

    return videos


def get_videos_of_correct_length(youtube, videos, max_playtime):
    """Given a list of video ids and maximum available time, 
    returns dict of videos that have a duration that is no longer than the user's available time
    and no shorter than 5 minutes less than the user's available time."""
    yt_max_batch_size = 50
    video_lengths = {}
    batches_needed = int(math.ceil(len(videos)/yt_max_batch_size))
    batch_index = 0
    
    for _ in range(batches_needed):
        try:
            batch = videos[batch_index : batch_index + yt_max_batch_size]
        except IndexError:
            batch = videos[batch_index : ]

        batch_index += yt_max_batch_size
        request = youtube.videos().list(part='contentDetails', id=','.join(batch))
        response = request.execute()
        
        for item in response['items']:
            playtime = item['contentDetails']['duration']
            duration = reformat_playtime_to_minutes(playtime)
            if max_playtime >= duration and get_minimum_playtime(max_playtime) <= duration:
                video_lengths.update({item['id'] : duration})
    
    return video_lengths


def reformat_playtime_to_minutes(t):
    """Given a playtime in YouTube's format, returns duration rounded down to nearest whole minute."""
    matches = re.search(r'^PT(\d+H)?(\d+)M(\d+)S$', t)
    minutes = int(matches.group(2)) if matches else 0
    return minutes


def get_minimum_playtime(max):
    if max <= 5:
        min = 0
    else:
        min = max - 5
    return min


def check_link(url):
    success_state = False
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException:
        pass
    else:
        if response.status_code == 200:
            success_state = True
    return success_state


if __name__ == '__main__':
    main()