from ast import List
from dataclasses import dataclass, field
import argparse
import sqlite3
from os import environ
from typing import Mapping
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError


@dataclass
class Track:
    id: str
    title: str


@dataclass
class Playlist:
    id: str
    name: str
    tracks: list[str] = field(default_factory=list)

    def stored_on_youtube(self, youtube_playlists) -> bool:
        for playlist in youtube_playlists.keys():
            if playlist == self.name:
                self.id = youtube_playlists.get(playlist).id
                return True
        return False

    def create_playlist_on_youtube(self, youtube: Resource):
        try:
            playlist_response = (
                youtube.playlists()
                .insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": self.name,
                            "description": "Remove when I'm famous",
                            "tags": [self.name],
                            "defaultLanguage": "en",
                        },
                        "status": {"privacyStatus": "public"},
                    },
                )
                .execute()
            )
        except HttpError as e:
            print(f"Failed to create Playlist: {self.name} on YT due {e.error_details}")

    def add_track_to_playlist(self, track: Track, youtube: Resource):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.id,
                        "resourceId": {"kind": "youtube#video", "videoId": track.id},
                    }
                },
            ).execute()
        except HttpError as e:
            print(
                f"Wrong couldn't add {track.title} to {self.name} due to {e.error_details}"
            )
        except ValueError:
            print(f"ValueError for {track.title} in {self.name}, already added??")

    def add_tracks_to_youtube_account(self, youtube: Resource):
        for track in self.tracks:
            self.add_track_to_playlist(track, youtube)

    def __str__(self) -> str:
        return f"{self.name} {self.tracks}"


def get_youtube_playlists(channel_id: str, youtube: Resource) -> Mapping[str, Playlist]:
    playlists = {}
    request = youtube.playlists().list(
        part="snippet", channelId=channel_id, maxResults=50
    )
    playlists_response = request.execute()
    playlists_response = playlists_response.get("items", [])
    for playlist in playlists_response:
        playlist = Playlist(id=playlist["id"], name=playlist["snippet"]["title"])
        # Using name as opposed to id for comparing with new pipe playlist names
        playlists.update({playlist.name: playlist})
    return playlists


db_conn = sqlite3.connect(environ["NEW_PIPE_DB"])
cursor = db_conn.cursor()


def fetch_new_pipe_playlist_data():
    playlist_streams_join_query = "select url, title from streams \
    where uid in \
    (select stream_id from playlist_stream_join where playlist_id = ?) \
    order by \
    (select join_index from playlist_stream_join where stream_id = uid and playlist_id = ?);"
    # ('https://www.youtube.com/watch?v=wxCMqH4BZSw', 'ENNY - Charge It')
    all_playlists = cursor.execute("SELECT uid, name from playlists").fetchall()
    results = []
    for id, name in all_playlists:
        tracks_metadata = cursor.execute(
            playlist_streams_join_query, [id, id]
        ).fetchall()
        playlist = Playlist(id, name)
        for id, title in tracks_metadata:
            id = id.split("=")[1]
            playlist.tracks.append(Track(id, title))
        results.append(playlist)
    return results


def fetch_new_pipe_subscriptions():
    return cursor.execute("SELECT url from subscriptions").fetchall()


def subscribe_on_youtube(subscription_urls, youtube: Resource):
    for url in subscription_urls:
        url = url[0].split("/")
        youtube.subscriptions().insert(
            part="snippet",
            body={
                "snippet": {
                    "resourceId": {
                        "kind": "youtube#channel",
                        "channelId": url[len(url) - 1],
                    }
                }
            },
        ).execute()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "channelId",
        help="Id of the Youtube channel to add playlists too",
        default=environ["CHANNEL_ID"],
    )
    parser.add_argument(
        "oauthCredentials",
        help="Full path to the OAuth client json file",
        default=environ["SECRETS_FILE"],
    )
    parser.add_argument(
        "subscriptions",
        help="Do you want to import subscriptions",
        default=environ["SUBSCRIPTIONS_IMPORT_DEFAULT"],
    )
    args = parser.parse_args()

    scopes = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]
    flow = InstalledAppFlow.from_client_secrets_file(args.oauthCredentials, scopes)
    flow.run_local_server()
    youtube = build(serviceName="youtube", version="v3", credentials=flow.credentials)

    new_pipe_playlists = fetch_new_pipe_playlist_data()
    # check YT for playlist, create if not on YT
    current_youtube_playlists = get_youtube_playlists(args.channelId, youtube)
    for new_pipe_playlist in new_pipe_playlists:
        if not new_pipe_playlist.stored_on_youtube(current_youtube_playlists):
            new_pipe_playlist.create_playlist_on_youtube(youtube)
        new_pipe_playlist.add_tracks_to_youtube_account(youtube)
    if bool(environ["SUBSCRIPTIONS_IMPORT_DEFAULT"]):
        subscribe_on_youtube(fetch_new_pipe_subscriptions(), youtube=youtube)
