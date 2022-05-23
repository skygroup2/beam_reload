from beam_reload import DeploySSH, find_beam
import argparse
import os


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Beam Reloader')
    parser.add_argument('--app', type=str, default=None, help='app name')
    parser.add_argument('--host', type=str, default=None, help='Target server ip')
    parser.add_argument('--port', type=int, default=22, help='Target server port')
    parser.add_argument('--user', type=str, default=None, help='Target server user')
    parser.add_argument('--password', type=str, default=None, help='Target server password')
    parser.add_argument('--target', type=str, default=None, help='Target deployed dir')
    parser.add_argument('--script', type=str, default=None, help='reload script')
    args, unknown_args = parser.parse_known_args()
    upload_ = [
        (args.script, '/tmp/reload.py')
    ]
    for m in unknown_args:
        upload_.append(find_beam(args.app, os.curdir, args.target, m))
    if len(upload_) > 1:
        script_ = 'python3 -u /tmp/reload.py'
        script_args_ = [' '.join(unknown_args).strip()]
        sv = DeploySSH(args.user, args.password, args.host, args.port)
        sv.key_ = 'LOCAL'
        sv.upload_ = upload_
        sv.script_ = script_
        sv.run(script_args_)
    else:
        print('please input modules to reload')
