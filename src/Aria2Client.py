import xmlrpc.client
import subprocess
import os
from pathlib import Path
import platform
import time


class Aria2Client:
    def __init__(self, host, port, aria2_path, secret=None):
        self.aria2_path = Path(aria2_path)
        self.host = host
        self.port = port
        self.server_uri = f'http://{host}:{port}/rpc'
        self.server = xmlrpc.client.ServerProxy(self.server_uri, allow_none=True)
        self.secret = secret

    def check_aria_path(self):
        return self.aria2_path.exists() and self.aria2_path.is_file()

    def initialize_aria2d(self, aria2_path):
        if not self.check_aria_path():
            # If aria2_path is not provided or is not a valid file, use a default path
            cwd = Path(sys.argv[0]).parent
            aria2d = cwd / "aria2c.exe"  # Default aria2c.exe path
        else:
            aria2d = self.aria2_path

        return aria2d

    def start_aria(self):
        # if not self.check_aria_path():
        #     raise ValueError("Aria2 path is not valid or does not exist.")
        aria2d = self.initialize_aria2d(aria2_path)

        if platform.system() == "Windows":
            NO_WINDOW = 0x08000000
            subprocess.Popen([str(aria2d), '--no-conf', '--enable-rpc', '--rpc-listen-port=' + str(self.port),
                              '--rpc-max-request-size=2M', '--rpc-listen-all', '--quiet=true'],
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             shell=False,
                             creationflags=NO_WINDOW)
        else:
            raise NotImplementedError("Starting Aria2 is not implemented for this platform.")


    def shutdown_aria(self):
        if not self.check_aria_path():
            raise ValueError("Aria2 path is not valid or does not exist.")

        subprocess.run([self.aria2_path, "--shutdown"])


    def _build_request_params(self, method, params=None):
        request_params = [self.secret] if self.secret else []
        if params:
            request_params.extend(params)
        return request_params

    def _call_method(self, method, params=None):
        request_params = self._build_request_params(method, params)
        try:
            return getattr(self.server.aria2, method)(*request_params)
        except xmlrpc.client.Fault as e:
            print(f"XML-RPC Error: {e.faultString}")
            return None


    def add_uri(self, uris, options=None, position=None):
        return self._call_method('addUri', [uris, options, position])

    def add_torrent(self, torrent, uris=None, options=None, position=None):
        return self._call_method('addTorrent', [torrent, uris, options, position])

    def add_metalink(self, metalink, options=None, position=None):
        return self._call_method('addMetalink', [metalink, options, position])

    def remove(self, gid):
        return self._call_method('remove', [gid])

    def force_remove(self, gid):
        return self._call_method('forceRemove', [gid])

    def pause(self, gid):
        return self._call_method('pause', [gid])

    def pause_all(self):
        return self._call_method('pauseAll')

    def force_pause(self, gid):
        return self._call_method('forcePause', [gid])

    def force_pause_all(self):
        return self._call_method('forcePauseAll')

    def unpause(self, gid):
        return self._call_method('unpause', [gid])

    def unpause_all(self):
        return self._call_method('unpauseAll')

    def get_files(self, gid):
        return self._call_method('getFiles', [gid])

    def get_servers(self, gid):
        return self._call_method('getServers', [gid])

    def tell_active(self, keys=None):
        return self._call_method('tellActive', [keys])

    def tell_waiting(self, offset, num, keys=None):
        return self._call_method('tellWaiting', [offset, num, keys])

    def tell_stopped(self, offset, num, keys=None):
        return self._call_method('tellStopped', [offset, num, keys])

    def change_position(self, gid, pos, how):
        return self._call_method('changePosition', [gid, pos, how])

    def change_uri(self, gid, file_index, del_uris, add_uris, position=None):
        return self._call_method('changeUri', [gid, file_index, del_uris, add_uris, position])

    def get_option(self, gid):
        return self._call_method('getOption', [gid])

    def change_option(self, gid, options):
        return self._call_method('changeOption', [gid, options])

    def get_global_option(self):
        return self._call_method('getGlobalOption')

    def change_global_option(self, options):
        return self._call_method('changeGlobalOption', [options])

    def get_global_stat(self):
        return self._call_method('getGlobalStat')

    def purge_download_result(self):
        return self._call_method('purgeDownloadResult')

    def remove_download_result(self, gid):
        return self._call_method('removeDownloadResult', [gid])

    def get_version(self):
        return self._call_method('getVersion')

    def get_session_info(self):
        return self._call_method('getSessionInfo')

    def shutdown(self):
        return self._call_method('shutdown')

    def force_shutdown(self):
        return self._call_method('forceShutdown')

    def save_session(self):
        return self._call_method('saveSession')

    def multicall(self, methods):
        return self._call_method('system.multicall', [methods])

    def list_methods(self):
        return self._call_method('system.listMethods')

    def list_notifications(self):
        return self._call_method('system.listNotifications')

    def get_uris(self, gid):
        return self._call_method('getUris', [gid])

    def tell_status(self, gid, keys=None):
        return self._call_method('tellStatus', [gid, keys])


if __name__ == "__main__":
  aria2_path = "aria2c.exe"
  host = 'localhost'
  port = 6800
  aria2_client = Aria2Client(host, port, aria2_path)

  # Check Aria2 path
  if aria2_client.check_aria_path():
      print("Aria2 path is valid.")
  else:
      print("Aria2 path is not valid.")

  # Start Aria2
  aria2_client.start_aria()
  print("Aria2 started.")

  time.sleep(2)

  try:
    verison = aria2_client.get_version()
    print(version)
  except:
    print("Aria2 didn't respond!", "ERROR")

  # url = "https://codeload.github.com/FourtyThree43/shusha/zip/refs/heads/dev"
  # dl_path = "/download/"

  # # # Example method call
  # result = aria2_client.add_uri([f'{url}'], {'dir': '{dl_path}'})
  # print(f'New download GID: {result}')

  # # Shutdown Aria2
  # aria2_client.shutdown_aria()
  # print("Aria2 shut down.")
