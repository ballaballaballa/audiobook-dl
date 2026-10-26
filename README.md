# audiobook-dl
![GitHub top language](https://img.shields.io/github/languages/top/ballaballaballa/audiobook-dl)
![License](https://img.shields.io/github/license/ballaballaballa/audiobook-dl)

CLI tool for downloading audiobooks from online sources.

> **This is a fork** of [jo1gi/audiobook-dl](https://github.com/jo1gi/audiobook-dl)
> by Joakim Holm. It is not published to PyPI; install it from this
> repository (see [Installation](#installation)). `pip install audiobook-dl`
> installs the original project, not this fork.

### Changes in this fork
- Fixes for Storytel, Nextory and other sources, ffmpeg combining and HLS streams
- Better metadata for audiobook apps (MP3/ID3 and MP4/M4B tags, chapters, series)
- Cover images normalized to JPEG and limited in size for app compatibility
- Progress bars for ffmpeg conversion, combining and chapter embedding
- Configurable MP4 audio encoder (`--mp4-audio-encoder`)
- CLI flags that override config values (`--no-combine`, `--chapters`, ...)
- A failing book or URL no longer stops the rest of a batch or series

## Supported Services
audiobook-dl currently supports downloading from the following sources:
- [audiobooks.com](https://audiobooks.com)
- [Blinkist](https://www.blinkist.com)
- [BookBeat](https://www.bookbeat.com)
- [Chirp](https://www.chirpbooks.com/)
- [eReolen](https://ereolen.dk)
- [Everand (previously Scribd)](https://everand.com)
- [Librivox](https://librivox.org)
- [Nextory](https://nextory.com)
- [Overdrive](https://www.overdrive.com/)
- [Podimo](https://podimo.com)
- [Saxo](https://saxo.com)
- [Storytel](https://www.storytel.com/) / [Mofibo](https://mofibo.com)
- [YourCloudLibrary](https://www.yourcloudlibrary.com/)

[More info](./supported_sites.md)

## Installation
This fork of audiobook-dl can be installed from this repo itself.

To install, run:
```shell
pip install "git+https://github.com/ballaballaballa/audiobook-dl.git"
```
or
```shell
git clone https://github.com/ballaballaballa/audiobook-dl.git
cd audiobook-dl
pip install .
```

Some features require [ffmpeg](https://ffmpeg.org/) which can be installed
through most package managers or from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

## Authentication

### Cookies
audiobook-dl uses Netscape cookie files for authentication in most cases. I use
[this](https://github.com/rotemdan/ExportCookies) extension to export my cookies
from the browser.

Cookies can be placed in current dir as `cookies.txt` or be given with the
`--cookies` argument.

### Login
[Some sources](./supported_sites.md) support authentication through login with
username and password (and sometimes library). Use the `--username` and
`--password` arguments or enter them through an interactive prompt.

## Downloading audiobooks
```shell
audiobook-dl -c <cookie file> <url>
```
**Most sites require you to provide the listening page and not just the
information page**

## Arguments

| Argument               | Value                                                             |
|------------------------|-------------------------------------------------------------------|
| url                    | The url of the page where you listen to the audiobook             |
| -c/--cookies           | Path to a Netscape cookie file                                    |
| --combine              | Combine all output files into a single file (requires ffmpeg)     |
| --no-combine           | Don't combine output files (overrides config)                     |
| --config               | Alternative location of config file                               |
| --cover                | Only download cover                                               |
| -d/--debug             | Print debug information                                           |
| --database_directory   | Directory for sources to store data                               |
| -f/--output-format     | Output file format                                                |
| --input-file           | File with one url to download per line                            |
| --library              | Specific library on service (Sometimes required when using login) |
| --mp4-audio-encoder    | Audio encoder for MP4/M4A/M4B files (default: aac)                |
| --no-chapters          | Don't include chapters in output file                             |
| --chapters             | Include chapters in output file (overrides config)                |
| -o/--output            | Output location (default: `{title}`)                              |
| --password             | Password to source (Required when using login)                    |
| --print-output         | Prints the output locations instead of downloading                |
| -q/--quiet             | Quiet mode                                                        |
| --remove-chars         | List of characters that will be removed from output path          |
| --skip-downloaded      | Skip downloading books if the output file or directory exists     |
| --no-skip-downloaded   | Download books even if they exist (overrides config)              |
| --username             | Username to source (Required when using login)                    |
| --verbose-ffmpeg       | Show ffmpeg output in terminal                                    |
| --write-json-metadata  | Write metadata in a separate json file                            |
| --no-write-json-metadata | Don't write a separate json metadata file (overrides config)    |

## Output
By default, audiobook-dl saves all audiobooks to `{title}` relative to the
current path. This can be changed with the `--output` argument. Path can be
customized by audiobook with the following fields:
- `title`
- `author`
- `narrator`
- `series`
- `series_order`
- `genre`
- `publisher`
- `isbn`
- `release_date`

Not all fields are available for all audiobooks. Missing fields are replaced
with `NA`. If a book has no author, the narrator is used instead.

The file extension can be changed with the `--output-format` argument.

## Configuration
audiobook-dl can be configured using a configuration file, which should be placed at:
- Windows: `C:\\Users\\$user\\AppData\\Local\\jo1gi\\audiobook-dl\\audiobook-dl.toml`
- Mac: `/Users/$user/Library/Application Support/audiobook-dl/audiobook-dl.toml`
- Linux: `$XDG_CONFIG_HOME/audiobook-dl/audiobook-dl.toml` (usually `~/.config/audiobook-dl/audiobook-dl.toml`)

### Authentication
Source credentials can be provided in the configuration file:
```toml
[sources.yourcloudlibrary]
username = "yourusername"
password = "supersecretpassword"
library = "hometown"
```

Cookie files can be specified in a similar way:
```toml
[sources.everand]
cookie_file = "./everand_cookies.txt"
```
Relative paths are resolved from the directory containing the configuration file.

### General Options
You can also set default values for command-line options in the configuration file:
```toml
output_template = "{author}/{title}"
database_directory = "/path/to/database"
skip_downloaded = true
combine = true
remove_chars = ":/"
no_chapters = false
output_format = "m4b"
write_json_metadata = true
mp4_audio_encoder = "aac"
```

All of these options correspond to their command-line argument equivalents.
Command-line arguments take precedence over the configuration file.

## Contributions
Issues, bug reports and pull requests for this fork are welcome
[here](https://github.com/ballaballaballa/audiobook-dl/issues).

## Credits
audiobook-dl was created by Joakim Holm ([jo1gi](https://github.com/jo1gi)).
