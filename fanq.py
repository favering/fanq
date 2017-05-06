#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import urllib.request
import urllib.error
import re
import subprocess
import sys
import time
import os


# 正在使用的ss服务器
current_sserver = {'url': None,
                   'port': None,
                   'pwd': None,
                   'enc': None,
                   'elapse': round(1000, 1)}

# sslocal 本机端口
sslocal_port = None

# sslocal 进程
sslocal_proc = None

# 浏览器进程
browser_proc = None

# 包含ss账号的网页及其对应的帐号关键字
# 该变量可根据实际情况经常更新
ss_site = [
    {"url": "https://github.com/Alvin9999/new-pac/wiki/ss%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7",
     "server": r"服务器[\d]+：",
     "port": "端口：",
     "password": "密码：",
     "method": "加密方式："},

    {"url": "http://www.ishadow.info",
     "server": "服务器地址:",
     "port": "端口:",
     "password": "密码:",
     "method": "加密方式:"},

    {"url": "http://freevpnss.me/",
     "server": "服务器地址：",
     "port": "端口：",
     "password": "码：",
     "method": "加密方式："},

    {"url": "http://freessr.xyz",
     "server": "服务器地址:",
     "port": "端口:",
     "password": "密码:",
     "method": "加密方式:"}
]


class ParseAddrError(Exception):
    """
    无法从指定页面解析获取到ss账号
    """
    def __init__(self, err):
        self.err = err


def log(e):
    print("[Fanq | Log]: {}".format(str(e)))


def err(e):
    print("[Fanq | Err]: {}".format(str(e)))


def get_sserver(site):
    """
    从指定的site页面中获取ss账号
    :return: 包含ss帐号信息的list,每个元素是字典
    """
    sserver_list = []

    # 打开url页面
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0"}
    try:
        request = urllib.request.Request(url=site['url'], headers=header)
        response = urllib.request.urlopen(request, timeout=8)
        html_text = decode_read(response)[1]
    except Exception as e:
        raise NotImplementedError("{} | {}".format(str(e), site['url']))

    # 按指定的ss帐号关键字生成正则匹配式
    server_reg = site["server"] + r"\s*([\w\d\.]+)"
    port_reg = site["port"] + r"\s*(\d+)"
    password_reg = site["password"] + r"\s*([\w\d\.-]+)"
    method_reg = site["method"] + r"\s*([\d\w-]+)"

    # 从该网页逐个提取帐号信息
    matchs = list(re.finditer(server_reg, html_text))
    for idx in range(len(matchs)):
        if idx == len(matchs) - 1:
            lines = html_text[matchs[idx].start():]
        else:
            lines = html_text[matchs[idx].start():matchs[idx + 1].start()]

        # server
        try:
            server = matchs[idx].group(1)
        except Exception as e:
            err("server match error | {}".format(site['url']))
            continue

        # port
        try:
            port = re.search(port_reg, lines).group(1)
        except Exception as e:
            err("port match error | {} | {}".format(site['url'], server))
            continue

        # password
        try:
            password = re.search(password_reg, lines).group(1)
        except Exception as e:
            err("password match error | {} | {}".format(site['url'], server))
            continue

        # method
        try:
            method = re.search(method_reg, lines).group(1)
        except Exception as e:
            err("method match error | {} | {}".format(site['url'], server))
            continue

        sserver_list.append({'url': server,
                             'port': port,
                             'pwd': password,
                             'enc': method,
                             'elapse': round(1000, 1)})
    return sserver_list


def decode_read(response):
    """
    尝试对response进行解码
    :param response:
    :return charset: response的字符集
    :return html_text: response解码后的字符串
    """
    rdata = response.read()

    # 首选按网页返回字符集进行解码
    match = re.search("charset=(\w+)", response.getheader('Content-Type'))
    if match is not None:
        charset = match.group(1)
        html_text = rdata.decode(charset)
    # 如果没有返回字符集，则尝试其他字符集
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
    使用SOCKS5代理进行http请求
    proxy[0] 代理IP
    proxy[1] 代理端口
    """
    import socks
    from sockshandler import SocksiPyHandler
    opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5, proxy[0], int(proxy[1])))
    return opener.open(url, timeout=6)


def start_sslocal(sserver, local_port):
    """
    启动sslocal
    """
    cmd = ['sslocal', '-s', sserver['url'], '-p', sserver['port'],
           '-l', local_port, '-k', sserver['pwd'], '-m', sserver['enc']]
    #return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.Popen(cmd)


def test_sserver_speed(sserver):
    """
    测试使用指定的ss server翻强的速度
    """
    if sserver['url'] is None:
        sserver['elapse'] = round(1000, 1)
        return

    test_port = str(int(local_port) + 1)
    test_proc = start_sslocal(sserver, test_port)
    # a little wait for test process starting
    time.sleep(1)

    # 当前时刻
    start_time = time.time()
    try:
        for i in range(3):
            request_webpage_via_ss_proxy("https://www.google.com", ("127.0.0.1", test_port))
            request_webpage_via_ss_proxy("https://zh.wikipedia.org", ("127.0.0.1", test_port))
            request_webpage_via_ss_proxy("https://gist.github.com", ("127.0.0.1", test_port))
    except Exception as e:
        err("request_webpage_via_ss_proxy | {} | {}".format(sserver['url'], e))
        # 连不通，设为超大值
        sserver['elapse'] = round(1000, 1)
    else:
        # 得出耗时
        end_time = time.time()
        sserver['elapse'] = round(end_time - start_time, 1)
    finally:
        test_proc.terminate()


def launch_webbrowser():
    """
    打开浏览器
    目前只支持chromium
    """
    b_args = ["www.google.com",
              "--user-data-dir",
              "--proxy-server=SOCKS5://127.0.0.1:{}".format(local_port)]
    # root用户需加--no-sandbox参数
    if os.geteuid() == 0:
        b_args.insert(0, "--no-sandbox")

    bproc = None
    if bproc is None:
        browser = ["chromium"]
        try:
            bproc = subprocess.Popen(browser+b_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            pass
    if bproc is None:
        browser = ["chromium-browser"]
        try:
            bproc = subprocess.Popen(browser+b_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            pass
    return bproc


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="A python script to automatically set SOCKS5 proxy on linux system.")
    parser.add_argument('-p', '--local_port', default='1080')
    return parser.parse_args()


def try_all_sserver():

    # 循环测试每一个提供ss帐号的页面内的帐号
    for site in ss_site:
        try:
            sserver_list = get_sserver(site)
        except Exception as e:
            err(e)
            continue

        # 每一个sserver和当前sserver的速度比较
        for sserver in sserver_list:

            global sslocal_proc, current_sserver
            # 测试该sserver和当前sserver的速度
            test_sserver_speed(sserver)
            test_sserver_speed(current_sserver)

            # 当该sserver速度比当前sserver速度快 1/3 时，
            if sserver['elapse']/current_sserver['elapse'] < (2/3):
                # 切换为该sserver
                if sslocal_proc is not None:
                    sslocal_proc.terminate()
                sslocal_proc = start_sslocal(sserver, local_port)
                current_sserver = sserver

                # log
                log("Elapse: {} | Connected to: {} | port:{} pwd:{} enc:{}".format(
                    sserver['elapse'], sserver['url'], sserver['port'], sserver['pwd'], sserver['enc']))

                # 打开浏览器
                global browser_proc
                if browser_proc is None:
                    browser_proc = launch_webbrowser()
                    if browser_proc is None:
                        err("Chromium browser could not be launched.")


def main():
    # check python version
    if sys.version[0] != '3':
        print("[Error] Python3 is needed.")
        sys.exit(-1)

    # check if sslocal installed
    try:
        subprocess.call("sslocal", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        err("shadowsocks is needed. Use \"sudo pip(3) install shadowsocks\" to install it.")
        sys.exit(-1)

    # check if PySocks installed
    try:
        import socks
    except ImportError as e:
        print("PySocks is needed. Use \"sudo pip(3) install PySocks\" to install it.")
        sys.exit(-1)

    global sslocal_proc, current_s, local_port
    local_port = parse_args().local_port

    # do it
    while True:
        try_all_sserver()
        time.sleep(1.5)


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
