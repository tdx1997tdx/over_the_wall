[TOC]



# centos翻墙一键配置脚本

审查越来越严格，用shawdowsocks的tcp直连翻墙经常被封。这里使用v2ray作为翻墙工具，使用websocket和tls协议模拟https请求直连nginx的443端口以达到欺骗的目的，安全稳定，目前试过的最安全的翻墙策略。然而这种策略缺点就是配置麻烦，就需要一套脚本进行自动配置。

## 手动步骤

### selinux关闭

```sh
setenforce 0
```

永久关闭

```sh
vim /etc/selinux/config
```

我们可以将它后面的值修改为permissive或者disabled，这样即使重启电脑以后，它默认的状态都会是permissve或disabled状态，而不会恢复到enforcing状态

### 防火墙关闭

```sh
systemctl stop firewalld
systemctl disable firewalld.service
```

### 安装配置v2ray

1. 安装

```sh
curl https://install.direct/go.sh | sh
```

2. 配置

```sh
vim /etc/v2ray/config.json
```

配置文件如下

```json
{
  "inbounds": [{
    "port": 12345, //v2ray暴露的端口号
    "protocol": "vmess", //通信协议
    "settings": {
      "clients": [
        {
          "id": "d59b9d35-be8b-41f5-86e9-4dc6be7f2cw5", //uuid
          "level": 1,
          "alterId": 1
        }
      ]
    },
    "streamSettings": { //这里是配置websocket协议的关键"/ws"说明映射到这个uri
        "network": "ws",
        "wsSettings": {
            "path": "/ws"
        }
    } 
  }],
  "outbounds": [{
    "protocol": "freedom",
    "settings": {}
  },{
    "protocol": "blackhole",
    "settings": {},
    "tag": "blocked"
  }],
  "routing": {
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "blocked"
      }
    ]
  }
}
```

3. 重启

```sh
systemctl restart v2ray
```

### 安装配置nginx

1. 安装

```sh
yum install nginx -y
```

2. 启动

```shell
systemctl enable nginx　　#设置nginx为开机启动
systemctl start nginx　　#启动nginx服务
```

### 配置nginx文件

nginx服务的默认配置文件在 /etc/nginx/nginx.conf

```sh
vim /etc/nginx/nginx.conf
```

将下面配置加上

```conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  你的域名;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        location / {
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }

	# Settings for a TLS enabled server.
    server{
        listen 443 ssl;
        ssl_certificate 路径/fullchain.cer;
        ssl_certificate_key 路径/你的域名.key;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers HIGH:!aNULL:!MD5;
        location /ws {
          proxy_redirect off;
          proxy_pass http://127.0.0.1:12345;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $http_host;
        }
    }

}

```

重启nginx

```sh
systemctl restart nginx
```

### 域名申请

这里推荐一个免费域名网站[freenom](https://www.freenom.com/zh/index.html?lang=zh)，不过可能需要先翻墙才能进去，可以向朋友先借一下。

### 证书申请

1.安装acme.sh

```sh
curl https://get.acme.sh | sh
```

2.安装后的配置
把 acme.sh 安装到你的 home 目录下:~/.acme.sh/并创建 一个 bash 的 alias, 方便你的使用:

```sh
alias acme.sh=~/.acme.sh/acme.sh
echo 'alias acme.sh=~/.acme.sh/acme.sh' >>/etc/profile
```

安装过程中会自动为你创建 cronjob, 每天 0:00 点自动检测所有的证书, 如果快过期了, 需要更新, 则会自动更新证书(可执行crontab -l 查看)。

```
00 00 * * * root /root/.acme.sh/acme.sh --cron --home /root/.acme.sh &>/var/log/acme.sh.logs
```

3.生成证书

```
acme.sh --issue --nginx -d tang.dexuannb.ml
```

只需要指定域名, 并指定域名所在的网站根目录【命令中/data/wwwroot/dexuan为域名的根目录路径】. acme.sh 会全自动的生成验证文件, 并放到网站的根目录, 然后自动完成验证. 最后会聪明的删除验证文件. 整个过程没有任何副作用.

4. 设置重认证（写进去可能会报错）

```sh
acme.sh --install-cert -d tang.dexuannb.ml \
--key-file /root/.acme.sh/tang.dexuannb.ml/tang.dexuannb.ml.key \
--fullchain-file /root/.acme.sh/tang.dexuannb.ml/tang.dexuannb.ml.cer \
--reloadcmd      "systemctl restart nginx"
```



### 启动bbr加速

bbr 是 Google 提出的一种新型拥塞控制算法，可以使 Linux 服务器显著地提高吞吐量和减少 TCP 连接的延迟。这里是一件脚本。

```sh
wget -N --no-check-certificate "https://raw.githubusercontent.com/hotmop/Linux-NetSpeed/master/tcp.sh"
```

```sh
chmod +x tcp.sh
```

```sh
./tcp.sh
```

选择安装bbr内核和加速，推荐魔改版。



### 客户端配置

![image](https://img-blog.csdnimg.cn/20200425220932145.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3FxXzM4NzgzMjU3,size_16,color_FFFFFF,t_70)

## 脚本使用

安装依赖

```sh
pip3 install jinja2
```

克隆项目

```sh
git clone https://github.com/tdx1997tdx/over_the_wall.git
```

直接运行

```sh
python3 main.py
```

