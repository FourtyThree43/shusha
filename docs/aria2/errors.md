# aria2 Error Codes & Exception Mapping

| Exit Code | Symbol | Message Description | Recoverable |
| :---: | :--- | :--- | :---: |
| `0` | `SUCCESS` | Successful | Yes |
| `1` | `UNKNOWN_ERROR` | Unknown error occurred | No |
| `2` | `TIMEOUT` | Time out occurred | Yes |
| `3` | `RESOURCE_NOT_FOUND` | Resource was not found (HTTP 404 / FTP 550) | No |
| `4` | `MAX_FILE_NOT_FOUND` | aria2 saw the specified number of 'resource not found' errors | No |
| `5` | `SPEED_TOO_SLOW` | Download speed was too slow | Yes |
| `6` | `NETWORK_PROBLEM` | Network problem occurred | Yes |
| `7` | `UNFINISHED_DOWNLOADS` | There were unfinished downloads | Yes |
| `8` | `RESUME_NOT_SUPPORTED` | Remote server did not support resume when resume was required | No |
| `9` | `NOT_ENOUGH_DISK_SPACE` | There was not enough disk space available | No |
| `10` | `PIECE_LENGTH_DIFFERENT` | Piece length was different from one in .aria2 control file | No |
| `11` | `DUPLICATE_INFO_HASH` | aria2 was downloading the same info hash | No |
| `12` | `DUPLICATE_TORRENT` | aria2 was downloading the same torrent | No |
| `13` | `FILE_ALREADY_EXISTS` | File already existed | No |
| `14` | `RENAMING_FAILED` | Renaming file failed | No |
| `15` | `CANNOT_OPEN_FILE` | aria2 could not open an existing file | No |
| `16` | `CANNOT_CREATE_TRUNCATE` | aria2 could not create new file or truncate existing file | No |
| `17` | `FILE_IO_ERROR` | File I/O error occurred | No |
| `18` | `CANNOT_CREATE_DIR` | aria2 could not create directory | No |
| `19` | `NAME_RESOLUTION_FAILED` | Name resolution failed (DNS failure) | Yes |
| `20` | `CANNOT_PARSE_METALINK` | aria2 could not parse Metalink document | No |
| `21` | `FTP_COMMAND_FAILED` | FTP command failed | Yes |
| `22` | `BAD_HTTP_HEADER` | HTTP response header was bad or unexpected | Yes |
| `23` | `TOO_MANY_REDIRECTS` | Too many redirects occurred | No |
| `24` | `HTTP_AUTH_FAILED` | HTTP authorization failed (HTTP 401 / 403) | No |
| `25` | `CANNOT_PARSE_BENCODE` | aria2 could not parse bencoded file (.torrent) | No |
| `26` | `CORRUPTED_TORRENT` | .torrent file was corrupted or missing information | No |
| `27` | `BAD_MAGNET_URI` | Magnet URI was bad | No |
| `28` | `BAD_OPTION` | Bad/unrecognized option was given or unexpected option value | No |
| `29` | `SERVER_OVERLOAD` | Remote server was unable to handle request (HTTP 503) | Yes |
| `30` | `CANNOT_PARSE_JSONRPC` | aria2 could not parse JSON-RPC request | No |
| `31` | `RESERVED` | Reserved | No |
| `32` | `CHECKSUM_FAILED` | Checksum validation failed | No |