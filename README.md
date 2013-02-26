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
In order to install this software, you need to execute the `tools.sh` script,
found in this dir. To install the package to `targetdir`:

    ./tools.sh install targetdir

## Development
If you would like to develop, specify a directory, where the environment will
be put. This assumes that you have the sources checked out to the current
directory.

    git clone git@github.com:citrix-openstack/osnotify.git osnotify
    cd osnotify
    ./tools.sh develop .env

## Testing
If you have a minimal ubuntu image, and your user have passwordless sudo, just
execute:

    ./tools.sh ci
