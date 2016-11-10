# fanq.py
基于shadowsocks的翻墙脚本，在浏览器上实现一键翻墙。(仅适用于Linux，在kali和ubuntu下已测试。)

该脚本从设定的网站上获取免费shadowsocks账号，测试到可翻的帐号后自动设置本地sslocal代理，并自动打开chromium浏览器。然后后台运行，周期性的测试各帐号，自动更新到最快的代理帐号。

# usage
直接运行该脚本即可。该脚本已内置两个包含免费shadowsocks账号的页面，根据实际情况需不定期地更新。

翻墙成功后会自动打开chromium并转到google主页。（如果未安装chromium，需手动设置你的浏览器的SOCKS5代理）
