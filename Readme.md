# NewPipe to Youtube populator

CLI application that adds playlists & subscriptions from a NewPipe export to a Youtube account.

## Description

Python script that extracts playlist tracks and subscriptions from an exported NewPipe database and adds
them a specified Youtube channel.

## Getting Started

1. Obtain Oauth Credentials for Google API access, [more info](https://developers.google.com/youtube/registering_an_application)
   1a. Create credentials for a Desktop client.
   1b. Enable the Youtube Data API, can be found under Library.
   1c. Download the JSON credentials file.

2. [Install](https://pipx.pypa.io/stable/installation/) pipx.

3. Install the package from source control with pipx.

```
pipx install git+https://github.com/SciDeving/NewPipeExtractor.git
```

4. Get your "channelId" from Youtube, copied from the "Share" button on Youtube channel profile page.

### Executing program

- Run the app

```
NewPipeExtractor <channelId> </Full/Path/OauthCredentials> <True|False>
```

Note: If a playlist already exists in Youtube with the same name then the songs will be added to that playlist.

## Authors

[@SciDeving](https://github.com/SciDeving)

```

```
