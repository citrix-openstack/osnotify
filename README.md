# osnotify

OpenStack related notifications

## Notification Broadcast Station
This is a static part of the architecture. This component is accepting
connections, and broadcasting all the received messages. You can start it with:

    osnotify-proxy

## Push Notifications
As an example, if you might want to push notifications to the proxy from gerrit:

    ssh -p 29418 review.example.com gerrit stream-events | osnotify-publish --host yourproxy.com

`osnotify-publish` is reading its standard input line by line, and publish them
to the specified host.

## Install
To install the package

    ./tools.sh install

## Development
If you would like to develop:

    ./tools.sh develop

## Testing
If you have a minimal ubuntu image, just execute:

    ./tools.sh ci
