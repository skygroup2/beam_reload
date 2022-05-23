import socks
import socket
import paramiko
import os.path
import re
from io import BytesIO, StringIO
from Crypto.PublicKey import RSA
from paramiko.ssh_exception import AuthenticationException


def sftp_exists(s, path):
    try:
        s.stat(path)
        return True
    except FileNotFoundError:
        return False


def mkdir_p(sftp, remote_directory):
    dir_path = ''
    for dir_folder in remote_directory.split('/'):
        if dir_folder == '':
            continue
        dir_path += f'/{dir_folder}'
        if sftp_exists(sftp, dir_path) is False:
            sftp.mkdir(dir_path)


class DeploySSH:
    """Abstract class to represent deploy step"""

    def __init__(self, username: str, passwd: str, host: str, port: int = 22):
        self.username_ = username
        self.passwd_ = passwd
        self.host_ = host
        self.port_ = port
        self.client_ = None
        self.ftp_ = None
        self.key_ = None
        self.script_ = None
        self.upload_ = []
        self.provider_ = None
        self.proxy_ = None
        self.sock_ = None

    def connect_proxy(self):
        if self.proxy_ is not None:
            self.sock_ = socks.socksocket()
            self.sock_.settimeout(60)
            self.sock_.set_proxy(proxy_type=socks.SOCKS5, addr=self.proxy_['host'], port=self.proxy_['port'],
                                 username=self.proxy_['user'], password=self.proxy_['passwd'])
            self.sock_.connect((self.host_, self.port_))

    def connect(self):
        self.connect_proxy()
        if self.key_ != 'LOCAL':
            k = paramiko.RSAKey.from_private_key(StringIO(self.key_['private_key']))
        else:
            k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/id_rsa'))
        self.client_ = paramiko.SSHClient()
        self.client_.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print('IP %s:%d -> connecting by key SOCK=%s' % (self.host_, self.port_, self.sock_ is not None))
        try:
            if self.sock_ is None:
                self.client_.connect(self.host_, self.port_, username=self.username_, pkey=k,
                                     timeout=50, banner_timeout=120)
            else:
                self.client_.connect(self.host_, self.port_, username=self.username_, pkey=k,
                                     timeout=50, banner_timeout=120, sock=self.sock_)
        except Exception as e:
            if isinstance(e, AuthenticationException):
                print('IP %s:%d -> connecting by password SOCK=%s' % (self.host_, self.port_, self.sock_ is not None))
                # if self.sock_ is None:
                self.client_.connect(self.host_, self.port_, username=self.username_, password=self.passwd_,
                                     timeout=30)
                # else:
                #     self.client_.connect(self.host_, self.port_, username=self.username_, password=self.passwd_,
                #                          timeout=30, sock=self.sock_)
            elif isinstance(e, socket.timeout):
                print('IP %s:%d -> connecting timeout' % (self.host_, self.port_))
                raise e
            else:
                raise e
        print('IP %s:%d -> connected' % (self.host_, self.port_))
        self.ftp_ = self.client_.open_sftp()

    def close(self):
        if self.ftp_ is not None:
            self.ftp_.close()
        if self.client_ is not None:
            self.client_.close()

    def run(self, args):
        ret = None
        self.connect()
        for s, d in self.upload_:
            sftp_dir = os.path.dirname(d)
            if not sftp_exists(self.ftp_, sftp_dir):
                mkdir_p(self.ftp_, sftp_dir)
            self.ftp_.put(s, d)
            print('SYNC: %s -> sftp://%s@%s:%d%s' % (s, self.username_, self.host_, self.port_, d))
        if self.script_ is not None:
            print(('IP %s:%d -> Run ' % (self.host_, self.port_)) + self.script_ + '\n')
            for a in args:
                script = self.script_
                if a != '':
                    script = script + ' ' + a
                ret = self.exec(script)
            for _, tmp_uploaded in self.upload_:
                if '/tmp/' in tmp_uploaded and sftp_exists(self.ftp_, tmp_uploaded):
                    self.ftp_.remove(tmp_uploaded)
        self.close()
        return ret

    def write_file(self, filename: str, content: bytes):
        self.ftp_.putfo(BytesIO(content), filename)

    def exec(self, command: str):
        if self.username_ in ['vps']:
            command = 'sudo ' + command
        print('%s : RUN %s' % (self.host_, command))
        (stdin, stdout, stderr) = self.client_.exec_command(command)
        out = '\n'.join(stdout.readlines())
        err = '\n'.join(stderr.readlines())
        if out.strip():
            print('------------- OUTPUT -------------')
            print(out)
        if err.strip():
            print('------------- ERROR  -------------')
            print(err)
        return out, err
