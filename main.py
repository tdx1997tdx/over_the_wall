# coding:utf-8
# !/bin/python3
import os, subprocess
from jinja2 import FileSystemLoader, Environment
import config


def main():
    while True:
        print('###############################')
        print('1. 填写相关配置信息')
        print('2. 一键安装配置')
        print('3. 退出脚本')
        print('###############################')
        n = input("请输入操作:")
        if n == '1':
            input_config()
            print('设置完成')
        elif n == '2':
            print('开始')
            before_config()
            v2ray()
            nginx()
            certificate()
            nginx_config()
        elif n == '3':
            break
        else:
            print('输入正确的命令')


def input_config():
    config.domain_name = input('请输入域名:')


def kill(name):
    def get_process_id(name):
        child = subprocess.Popen(["pgrep", "-f", name], stdout=subprocess.PIPE, shell=False)
        response = bytes.decode(child.communicate()[0])
        return response

    pid = get_process_id(name)
    if not pid:
        print("no target pid to kill,please check")
    else:
        print('process_pid:', pid)
        result = os.system("kill -9 " + pid)
        if result == 0:
            print("execute kill success")


def before_config():
    os.popen('setenforce 0')
    os.popen('\cp -f selinux_config /etc/selinux/config')
    os.popen('systemctl stop firewalld')
    os.popen('systemctl disable firewalld.service')
    print('防火墙和selinux已关闭')


def v2ray():
    f = os.popen('curl https://install.direct/go.sh | sh')
    print(f.read())
    f = os.popen('\cp -f v2ray_config.json %s' % (config.v2ray_config_path))
    print(f.read())
    f = os.popen('systemctl start v2ray')
    print(f.read())


def nginx():
    kill('nginx')
    f = os.popen('yum install nginx -y')
    print(f.read())
    f = os.popen('systemctl enable nginx')
    print(f.read())
    f = os.popen('systemctl restart nginx')
    print(f.read())
    print('nginx安装完成')


def certificate():
    f = os.popen('rm -rf ~/.acme.sh/%s' % (config.domain_name))
    print(f)
    key_path = '~/.acme.sh/%s/%s.key' % (config.domain_name, config.domain_name)
    fullchain_path = '~/.acme.sh/%s/fullchain.cer' % (config.domain_name)
    print('开始安装步骤')
    f = os.popen('curl https://get.acme.sh | sh')
    print(f.read())
    print('开始自动检测证书')
    f = os.popen('00 00 * * * root /root/.acme.sh/acme.sh --cron --home /root/.acme.sh &>/var/log/acme.sh.logs')
    print('开始生成证书')
    f = os.popen('/root/.acme.sh/acme.sh --issue -d %s --nginx' % (config.domain_name))
    print(f.read())
    # print('开始复制证书')
    # f = os.popen(
    #     '/root/.acme.sh/acme.sh --install-cert -d %s --key-file %s --fullchain-file %s --reloadcmd "systemctl restart nginx"' % (
    #     config.domain_name, key_path, fullchain_path))
    # print(f.read())


def nginx_config():
    env = Environment(
        loader=FileSystemLoader(searchpath="./"))
    template = env.get_template('nginx_templete.conf')  # 获取一个模板文件
    res = template.render(hostname=config.domain_name)  # 渲染
    f = open(config.nginx_condig_path, 'w')
    f.write(res)
    f.close()
    os.popen('systemctl restart nginx')
    print('nginx配置完成')


def notify():
    print('---------------------------------------')
    print('**默认id:', 'd59b9d35-be8b-41f5-86e9-4dc6be7f2cw5')
    print('**默认端口号:', '12345')
    print('**默认接口:', 'ws')
    print('---------------------------------------')


if __name__ == '__main__':
    main()
