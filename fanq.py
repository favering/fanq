#! /usr/bin/env python3
# -*- coding: gb18030 -*-

import urllib.request
import urllib.error
import re
import subprocess
import sys
import time
import os

# sslocal����
sslocal_proc = None
# ����ʹ�õ�ss������
current_s = None
# sslocal �����˿�
local_port = None
# ���������
browser_proc = None
# ����ss�˺ŵ���ҳ�����Ӧ���ʺŹؼ���
# �ñ����ɸ���ʵ�������������
ss_site = [
    {"site": "http://www.ishadowsocks.org",
     "server": "��������ַ:",
     "port": "�˿�:",
     "password": "����:",
     "method": "���ܷ�ʽ:"},

    {"site": "http://freessr.top",
     "server": "��������ַ:",
     "port": "�˿�:",
     "password": "����:",
     "method": "���ܷ�ʽ:"}
]

class ParseAddrError(Exception):
    """
    �޷���ָ��ҳ�������ȡ��ss�˺�
    """
    def __init__(self, err):
        self.err = err

def get_sserver():
    """
    ��ss_site����ַ�л�ȡss�˺�
    :return: ����ss�ʺ���Ϣ��list,ÿ��Ԫ�����ֵ�
    """
    l = []

    for site in ss_site:
        # �򿪰����ʺŵ���ҳ
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0"}
        try:
            request = urllib.request.Request(url=site["site"], headers=header)
            response = urllib.request.urlopen(request, timeout=8)
            html_text = decode_read(response)[1]
        except Exception as e:
            print("{} [{}]".format(e, site["site"]))
            continue

        # ��ָ����ss�ʺŹؼ�����������ƥ��ʽ
        server_reg = site["server"] + r"([\w\d\.]+)"
        port_reg = site["port"] + r"(\d+)"
        password_reg = site["password"] + r"([\w\d\.-]+)"
        method_reg = site["method"] + r"([\d\w-]+)"

        # �Ӹ���ҳ�����ȡ�ʺ���Ϣ
        matchs = list(re.finditer(server_reg, html_text))
        for idx in range(len(matchs)):
            if idx == len(matchs) - 1:
                lines = html_text[matchs[idx].start():]
            else:
                lines = html_text[matchs[idx].start():matchs[idx + 1].start()]

            try:
                server = matchs[idx].group(1)
                port = re.search(port_reg, lines).group(1)
                password = re.search(password_reg, lines).group(1)
                method = re.search(method_reg, lines).group(1)
            except Exception as e:
                print("reg match error [{}]".format(e))
                print("\n")
                continue

            l.append({'addr': server,
                      'port': port,
                      'pwd': password,
                      'enc': method,
                      'elapse': round(1000, 1)})
    return l

def decode_read(response):
    """
    ���Զ�response���н���
    :param response:
    :return charset: response���ַ���
    :return html_text: response�������ַ���
    """
    rdata = response.read()

    # ��ѡ����ҳ�����ַ������н���
    match = re.search("charset=(\w+)", response.getheader('Content-Type'))
    if match is not None:
        charset = match.group(1)
        html_text = rdata.decode(charset)
    # ���û�з����ַ��������������ַ���
    else:
        charset = 'unknown'
        if charset == 'unknown':
            try:
                html_text = rdata.decode("UTF-8")
            except UnicodeError as e:
                pass
            else:
                charset = 'UTF-8'

        if charset == 'unknown':
            try:
                html_text = rdata.decode("ISO-8859-1")
            except UnicodeError as e:
                pass
            else:
                charset = 'ISO-8859-1'

        if charset == 'unknown':
            try:
                html_text = rdata.decode("gb18030")
            except UnicodeError as e:
                pass
            else:
                charset = 'gb18030'

    if charset == 'unknown':
        raise ParseAddrError("Cannot decode the page")
    return charset, html_text

def request_webpage_via_ss_proxy(url, proxy):
    """
    ʹ��SOCKS5�������http����
    proxy[0] ����IP
    proxy[1] ����˿�
    """
    import socks
    from sockshandler import SocksiPyHandler
    opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5, proxy[0], int(proxy[1])))
    return opener.open(url, timeout=6)

def check_pysocks():
    """
    ���PySocks�Ƿ��Ѱ�װ
    """
    try:
        import socks
    except ImportError:
        return False
    else:
        return True

def start_sslocal(sserver, local_port, output=False):
    """
    ����sslocal
    """
    cmd = ['sslocal', '-s', sserver['addr'], '-p', sserver['port'],
           '-l', local_port, '-k', sserver['pwd'], '-m', sserver['enc']]
    if output == False:
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif output == True:
        return subprocess.Popen(cmd)

def find_an_available_sserver():
    """
    ��ָ��ҳ���ȡһ������ss�˺š�û�еĻ�����None
    """
    sserver_list = get_sserver()
    import random
    random.shuffle(sserver_list)

    # �û�ȡ���˺ų��Է�
    for i in range(len(sserver_list)):
        s = sserver_list[i]
        print("[Info] Trying \"{}\" (port:{} password:{})...".format(s['addr'], s['port'], s['pwd']))
        proc = start_sslocal(s, local_port)
        time.sleep(1)

        try:
            request_webpage_via_ss_proxy("https://www.google.com", ("127.0.0.1", local_port))
        except Exception as e:
            print(e)
            print()
            continue
        else:
            break
        finally:
            proc.terminate()
    else:
        return None

    return sserver_list[i]

def background_update_sserver():
    """
    ��̨�����Եز��Ը�ss���������Զ��л������ķ�����
    """
    while True:
        # ÿ��5�����һ��
        time.sleep(5)

        # ��ȡss�������б�
        sserver_list = get_sserver()
        if len(sserver_list) == 0:
            continue

        # ����ÿһ��ss���������ٶȣ�������ٶ�������һ��
        for i in range(len(sserver_list)):
            test_sserver_speed(sserver_list[i])
        fastest_s = sorted(sserver_list, key=lambda s: s['elapse'])[0]

        # ���Ե�ǰss���������ٶ�
        global current_s
        test_sserver_speed(current_s)

        # ������ʾ
        print("\n[Updated ss server elapse]")
        tmp = sorted(sserver_list, key=lambda s: s['elapse'])
        for t in tmp:
            print('{', end='')
            print("{}:{}, ".format("elapse", t["elapse"]), end='')
            print("{}:{}, ".format("addr", t["addr"]), end='')
            print("{}:{}, ".format("port", t["port"]), end='')
            print("{}:{}, ".format("pwd", t["pwd"]), end='')
            print("{}:{}".format("enc", t["enc"]), end='')
            print('}')
        print("\n[Updated current ss server elapse]")
        print('{', end='')
        print("{}:{}, ".format("elapse", current_s["elapse"]), end='')
        print("{}:{}, ".format("addr", current_s["addr"]), end='')
        print("{}:{}, ".format("port", current_s["port"]), end='')
        print("{}:{}, ".format("pwd", current_s["pwd"]), end='')
        print("{}:{}".format("enc", current_s["enc"]), end='')
        print('}')
        print()

        # �ٶ����ıȵ�ǰss�������ٶȿ� 1/3 ʱ���л������ķ�����
        if fastest_s['elapse']/current_s['elapse'] < (2/3):
            print("\n[Info] Switch to \"{}\" (port:{} password:{})".format(
                fastest_s['addr'], fastest_s['port'], fastest_s['pwd']))
            global sslocal_proc
            sslocal_proc.terminate()
            sslocal_proc = start_sslocal(fastest_s, local_port, output=True)
            current_s = fastest_s

def test_sserver_speed(s):
    """
    ���Է�ǽ����ٶ�
    """
    tmp_port = str(int(local_port) + 1)
    proc = start_sslocal(s, tmp_port)
    time.sleep(1)

    # ��ǰʱ��
    s_time = time.time()
    try:
        for i in range(3):
            request_webpage_via_ss_proxy("https://www.google.com", ("127.0.0.1", tmp_port))
            request_webpage_via_ss_proxy("https://zh.wikipedia.org", ("127.0.0.1", tmp_port))
            request_webpage_via_ss_proxy("https://gist.github.com", ("127.0.0.1", tmp_port))
    except Exception as e:
        print("[Error] request_webpage_via_ss_proxy error [{} \"{}\"]".format(e, s['addr']))
        # ����ͨ���������ֵ
        s['elapse'] = round(1000, 1)
    else:
        # �ó���ʱ
        e_time = time.time()
        s['elapse'] = round(e_time - s_time, 1)
    finally:
        proc.terminate()

def launch_webbrowser():
    """
    �������
    Ŀǰֻ֧��chromium
    """
    global browser_proc
    b_args = ["www.google.com",
              "--user-data-dir",
              "--proxy-server=SOCKS5://127.0.0.1:{}".format(local_port)]
    # root�û����--no-sandbox����
    if os.geteuid() == 0:
        b_args.insert(0, "--no-sandbox")

    p_open = False
    if not p_open:
        browser = ["chromium"]
        try:
            browser_proc = subprocess.Popen(browser+b_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(e)
        else:
            p_open = True
    if not p_open:
        browser = ["chromium-browser"]
        try:
            browser_proc = subprocess.Popen(browser+b_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(e)
        else:
            p_open = True
    return p_open


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="A python script to automatically set SOCKS5 proxy on linux system.")
    parser.add_argument('-p', '--local_port', default='1080')
    return parser.parse_args()

def main():
    if sys.version[0] != '3':
        print("[Error] Python3 is needed.")
        sys.exit(-1)

    # check if sslocal installed
    try:
        subprocess.call("sslocal", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        print("[Error] sslocal is needed. Use \"pip install sslocal\" to install it.")
        sys.exit(-1)

    global sslocal_proc, current_s, local_port
    local_port = parse_args().local_port

    # Ѱ�ҿ����˺�
    while True:
        s = find_an_available_sserver()
        # û���ҵ������˺ţ�ѯ���Ƿ����Ѱ��
        if s is None:
            print("[Error] Could not find an available ss server.")
            if input("[Quest] Try again? Y/N: ").lower() == 'y':
                print()
                continue
            else:
                sys.exit(-1)
        # �����õ�ss��������Ϊ��ǰ��������
        else:
            current_s = s
            break

    # ����sslocal
    print('[Info] Connected to \"{}\"\n'.format(current_s['addr']))
    sslocal_proc = start_sslocal(current_s, local_port, output=True)
    time.sleep(1)

    # PySocks��װ���
    if not check_pysocks():
        print("[Warn] PySocks not installed, could not backgroud update to fastest SOCKS5 proxy automatically.")
        print("[Info] Use \"pip install PySocks\" to install it.\n")

    # �������
    if not launch_webbrowser():
        ss_addr = "127.0.0.1:%s" % local_port
        print("[Warn] Chrome browser could not be launched.\n"
              "[Info] Open your web browser and manually set SOCKS5 proxy to {}\n".format(ss_addr))

    # �ɽ��к�̨����
    if check_pysocks():
        background_update_sserver()
    # ����ʲôҲ���ɣ�����
    else:
        while True:
            input()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        pass
    finally:
        if sslocal_proc is not None:
            sslocal_proc.terminate()
        if browser_proc is not None:
            browser_proc.terminate()
    print()
