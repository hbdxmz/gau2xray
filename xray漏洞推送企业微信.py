from flask import Flask, request
import requests
import datetime
import logging

app = Flask(__name__)

#参考xray文档：https://docs.xray.cool/#/scenario/xray_vuln_alert

def push_wechat_group(content):
    #替换key为你的企业微信群key
    resp = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key",
                         json={"msgtype": "markdown",
                               "markdown": {"content": content}})

@app.route('/webhook', methods=['POST'])
def xray_webhook():
    data = request.json
    typed = data["type"]
    if typed == "web_statistic":
        return 'ok'
    vuln = data["data"]

    url = vuln["detail"]["addr"] if "addr" in vuln["detail"] else ""

    #sourcemap/default、sensitive/statistic这类漏洞就忽略
    plugin = vuln["plugin"] if "plugin" in vuln else ""
    if plugin in ["dirscan/sourcemap/default", "dirscan/sensitive/statistic"]:
        return 'ok'

    #如果扫出来一个cve漏洞，这时vuln["detail"]中不含key等参数，就推送不了漏洞消息，对于这种某个参数不存在的漏洞，可将该参数置为"",防止推送失败错过漏洞消息
    position = vuln["detail"]["extra"]["param"]["position"] if "extra" in vuln["detail"] and "param" in vuln["detail"][
        "extra"] and "position" in vuln["detail"]["extra"]["param"] else ""

    key = vuln["detail"]["extra"]["param"]["key"] if "extra" in vuln["detail"] and "param" in vuln["detail"][
        "extra"] and "key" in vuln["detail"]["extra"]["param"] else ""

    payload = vuln["detail"]["payload"] if "payload" in vuln["detail"] else ""

    vul = vuln["plugin"] if "plugin" in vuln else ""

    snapshot = ""
    for i, snap in enumerate(vuln["detail"]["snapshot"], start=1):
        request_snapshot = snap[0]  # 遍历获取请求包，对于盲注漏洞，一般会有多个请求包
        snapshot += f"Request{i}:\n{request_snapshot}\n\n"


    content = """## {vul}漏洞\n\n
    url: {url}\n\n
    plugin: {plugin}\n\n
    发现时间: {create_time}\n\n
    请求类型: {position}\n\n
    漏洞参数: {key}\n\n
    payload: {payload}\n\n
    请求包:\n
    {snapshot}
    """.format(
        create_time=str(datetime.datetime.fromtimestamp(vuln["create_time"] / 1000)),
        url=url,
        plugin=plugin,
        position=position,
        key=key,
        payload=payload,
        snapshot=snapshot,
        vul = vul.split('/')[0]
    )

    try:
        push_wechat_group(content)
    except Exception as e:
        logging.exception(e)
    return 'ok'


if __name__ == '__main__':
    app.run()
