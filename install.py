import os
import sys

def is_termux():
    return 'com.termux' in os.environ.get('PREFIX', '')

choice = input('[+] To install press (Y) to uninstall press (N) >> ')
run = os.system

if choice.lower() == 'y':
    if is_termux():
        prefix = os.environ.get('PREFIX')
        bin_path = os.path.join(prefix, 'bin', 'webextractor')
        share_path = os.path.join(prefix, 'share', 'webextractor')

        run('chmod 777 webextractor.py')
        run(f'mkdir -p {share_path}')
        run(f'cp webextractor.py {share_path}/webextractor.py')

        termux_launcher = f'#! /data/data/com.termux/files/usr/bin/sh\nexec python3 {share_path}/webextractor.py "$@"'
        with open(bin_path, 'w') as file:
            file.write(termux_launcher)

        run(f'chmod +x {bin_path} && chmod +x {share_path}/webextractor.py')
        print('''\n\n[+] WebExtractor installed successfully in Termux
[+] Now just type \x1b[6;30;42mwebextractor\x1b[0m in terminal''')

    else:
        if os.geteuid() != 0:
            print("Please run as root or with sudo")
            sys.exit(1)

        run('chmod 777 webextractor.py')
        run('mkdir -p /usr/share/webextractor')
        run('cp webextractor.py /usr/share/webextractor/webextractor.py')

        linux_launcher = '#! /bin/sh\nexec python3 /usr/share/webextractor/webextractor.py "$@"'
        with open('/usr/bin/webextractor', 'w') as file:
            file.write(linux_launcher)

        run('chmod +x /usr/bin/webextractor && chmod +x /usr/share/webextractor/webextractor.py')
        print('''\n\n[+] WebExtractor installed successfully on Linux
[+] Now just type \x1b[6;30;42mwebextractor\x1b[0m in terminal''')

elif choice.lower() == 'n':
    if is_termux():
        prefix = os.environ.get('PREFIX')
        run(f'rm -rf {prefix}/share/webextractor')
        run(f'rm -f {prefix}/bin/webextractor')
        print('[!] WebExtractor removed from Termux successfully')
    else:
        if os.geteuid() != 0:
            print("Please run as root or with sudo")
            sys.exit(1)
        run('rm -rf /usr/share/webextractor')
        run('rm -f /usr/bin/webextractor')
        print('[!] WebExtractor removed from Linux successfully')
