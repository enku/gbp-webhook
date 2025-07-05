# gbp-webhook

[gbp-webhook](https://github.com/enku/gbp-webhook) is a web service that
responds to webhook notifications given from the
[gbp-notifications](https://github.com/enku/gbp-notifications) plugin. It
shows a nice desktop notification whenever the machines of your choice pull a
build. That's what it does by default, however plugins can be written to
respond to any event that gbp-notifications responds to.

![screenshot](https://raw.githubusercontent.com/enku/screenshots/refs/heads/master/gbp-notifications/desktop-notification.png)

## Features

- Command-line interface integrates with [gbpcli](https://github/com/enku/gbpcli)
- Does not require root access to run
- Security
  - IP whitelisting
  - Pre-shared key
  - Optional SSL (TLS) support
- Plugin support to handle gbp-notifications however you like


## Installation

These instructions assume you already have
[gbpcli](https://github.com/enku/gbpcli), the command-line interface for
Gentoo Build Publisher, installed on your desktop.

If you've installed gbpcli via `pip install --user`:

```sh
pip install --user gbp-webhook
```

If you've installed gbpcli via [pipx](https://pipx.pypa.io/stable/):

```sh
pipx inject gbpcli gbp-webhook
```

## Usage

Set the pre-shared key with an environment variable

```sh
GBP_WEBHOOK_PRE_SHARED_KEY=our_little_secret
export GBP_WEBHOOK_PRE_SHARED_KEY
```

Run the server

```sh
gbp webhook serve --port 5000 --allow 10.10.10.23
```

The `--port` argument is the port you wish the webhook to listen on. It is
optional and defaults to `5000`.

The `--allow` argument is an IP or IP/mask that is allowed to send requests to
the webhook server. Multiple IPs can be passed.  All other IPs are forbidden
so if no `--allow` flags are passed then the server will refuse all requests.

gbp-webhook uses [nginx](https://nginx.org) as a front-end. You do not need to
be root to start nginx or run nginx as a system service, however you do need
to tell gbp-webhook where the nginx executable resides if it is anywhere other
than `/usr/sbin/nginx`. This is done with the `--nginx` argument. For example:

```sh
gbp webhook serve --port 5000 --nginx ~/.local/bin/nginx
```

Ok so now the service is running on your desktop system, but you need to
configure the server. This is where gbp-notifications comes in.  Refer to the
gbp-notifications installation instructions, then configure it to talk to your
gbp-webhook server. Here's an exampl TOML config:

```toml
[recipients]
laptop = { webhook = "http://10.10.10.100:5000/webhook|X-Pre-Shared-Key=our_little_secret" }

[subscriptions]
"*" = {build_pulled = ["laptop"]}
```

If you use the TOML config you won't need to restart the GBP service to read
the config.  However if you are using environment variables configuration you
will.

Now when a build is pulled, gbp-notifications will send an HTTP request to the
webhook service on your laptop, which will in turn display a desktop
notification.

## Systemd Integration

gbp-webhook can be run manually from the command line as outlined above.
However it's nicer if it is able to automatically start in the background when
you log into your desktop environment.  For this gbp-webhook is able to
install a [systemd](https://systemd.io/) unit file for you:

```sh
gbp webhook install --port 5000 --nginx ~/.local/bin/nginx
```

This installs a `gbp-webhook.service` unit in `~/.local/share/systemd/user`.
It also installs a config file in `~/.config/gbp-webhook.conf`.  You can then
enable and start the service with:

```sh
systemctl enable --user --now gbp-webhook
```

Now it will start automatically when you log in.  To uninstall the service:

```sh
gbp webhook uninstall
```

## Environment Variables

The following variables are read from `~/.config/gbp-webhook.conf`:

- `GBP_WEBHOOK_PRE_SHARED_KEY`: as explained above, the pre-shared key
  exchanged between Gentoo Build Publisher and gbp-webhook.
- `GBP_WEBHOOK_NGINX`: If defined, this is the full path to the nginx
  executable. The default is `/usr/sbin/nginx`.
- `GBP_WEBHOOK_ARGS`: additional arguments to pass to `gbp-webhook`.
  Run `gbp webhook --help` to see the available arguments.


## Plugins

gbp-webhook has a plugin mechanism were the webhook can call arbitrary
handlers. The following additional plugins are known to exist:

| Plugin | Description |
| ------ | ----------- |
| [playsound](https://github.com/enku/gbp-webhook-playsound) | A plugin that plays a sound on build pulled events |
| [tts](https://github.com/enku/gbp-webhook-tts) | A text-to-speech plugin to speak the name of a machine or machines when a build is pulled for that machine |
