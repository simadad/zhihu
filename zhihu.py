import csv
import json
import re
import requests
from collections import namedtuple
from time import sleep
from lxml import etree


def get_total_quantity(url, headers):
    """
    获取用户总数
    """
    r = requests.get(url=url, headers=headers)
    page = etree.HTML(r.text)
    print('page:\t', page)
    numb = page.find('.//*[@id="zh-question-side-header-wrap"]/div/div/a/strong')
    print('total:\t', numb.text)
    return int(numb.text)


def get_user_data(users_page):
    """
    解析单次请求数据，返回昵称、hash_id、活跃度列表信息
    """
    page = etree.HTML(users_page)
    user_list = page.findall('.//div[@class="zm-profile-card zm-profile-section-item zg-clear no-hovercard"]')
    print('nickname:', end='\t')
    for user_data in user_list:
        try:
            nickname = user_data.xpath('.//@title')[0]
            hash_id = user_data.xpath('.//@data-id')[0]
            info = user_data.xpath('.//a[@class="zg-link-gray-normal"]/text()')
            info = [re.findall(r'\d+', x)[0] for x in info]
            yield [nickname, hash_id] + info
            print(nickname, end=',\t')
        except Exception as e:
            print('ERROR:\t', e)
    else:
        print()


def get_user_list(url, headers, max_set, sleep_time):
    """
    循环抓取并返回用户信息页面
    """
    offset = 0
    while offset <= max_set:
        offset += 20
        form_data = {
            'start': 0,
            'offset': offset
        }
        r = requests.post(url=url, data=form_data, headers=headers)
        print('request:\t', r.request.body)
        data = json.loads(r.text)
        yield data['msg'][1]
        sleep(sleep_time)


def get_active_users(file_name):
    """
    读取文件，返回用户数据
    """
    with open(file_name, encoding='utf8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        Row = namedtuple('Row', headers)
        for r in reader:
            nickname, hash_id, followers, asks, answers, approvals = Row(*r)
            if _activity_judge(followers, asks, answers, approvals):
                print('active:\t', nickname)
                yield hash_id


def _activity_judge(*r):
    """
    判断是否为活跃用户
    """
    followers, asks, answers, approvals = r
    if int(followers) > 1000 and int(asks) > 10 and int(answers) > 100 and int(approvals) > 5000:
        return True
    else:
        return False


def follow_them(hash_id, url_follow, headers):
    """
    关注活跃用户
    """
    print(hash_id)
    post_data = {
        'method': 'follow_member',
        'params': '{"hash_id": "%s"}' % hash_id,
    }
    requests.post(url_follow, data=post_data, headers=headers)


def main_loop():
    # 设定防封号循环间隔时间
    sleep_time = 0.1        
    # 感兴趣的问题 id
    qid = 20702054
    # 问题关注者列表地址
    url_followers = 'https://www.zhihu.com/question/{qid}/followers'.format(qid=qid)
    # 关注地址
    url_follow = 'https://www.zhihu.com/node/MemberFollowBaseV2'
    # 爬虫请求头伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'cookie': '_zap=0fd90ae1-ad89-448c-8fa1-2ff1e6baece2; d_c0="ACBCAx9VUAuPTjQlE2tsm1V6G0LG8TABnPU=|1487149584"; _zap=7f1656bd-9905-4907-b126-afed12fcc313; q_c1=f0a769f2656e44f9a41e088ad7fe8487|1504063314000|1487149584000; q_c1=f0a769f2656e44f9a41e088ad7fe8487|1504063314000|1487149584000; _xsrf=c40dc7ab2ea3886c66b6fae28059d466; aliyungf_tc=AQAAAIIyXWJ4DgUAJc/1ZfZNMLsA2kdy; r_cap_id="NzNiOTFjMWQwODk0NDcyOThlOWM2ODZiZjRkNDZiMTI=|1504934847|30390c08b943fb3814bb8995c3ce4045524f81be"; cap_id="M2YyOGVkMGUzNTg5NGIwZmJjNGY3ZTc3ZmUwYzgzMDU=|1504934847|f813ff485380ed07547e41bd467c9c15bdba0523"; l_cap_id="NjVhZGNmZTc4NmI0NGQzZmE4YTQ5YWMzOGFlNGE1ODE=|1504934865|3fdf0e439eb2da6bb6c0d794621d04df0e00b2ad"; z_c0=Mi4xX0FRNEFBQUFBQUFBSUVJREgxVlFDeGNBQUFCaEFsVk4zZ2piV1FCbmwxc1lTdTE4dXZBY09rYWhWd3JNUWhRMDF3|1504934878|ecbe32cd9cd3319ffd5ef16505292fbd52a6ecb1; _xsrf=c40dc7ab2ea3886c66b6fae28059d466; __utma=51854390.2003206662.1504794547.1504934845.1504961732.8; __utmc=51854390; __utmz=51854390.1504837475.3.3.utmcsr=shimo.im|utmccn=(referral)|utmcmd=referral|utmcct=/doc/ImYjjkLBb3EDXTnt; __utmv=51854390.100-1|2=registration_date=20140217=1^3=entry_date=20140217=1',
        'X-Xsrftoken': 'c40dc7ab2ea3886c66b6fae28059d466',
    }
    # 信息储存文件
    file_zhihu = 'zhihu.csv'
    # 储存文件表头
    titles = ['nickname', 'hash_id', 'followers', 'asks', 'answers', 'approvals']
    # 得到当前问题关注总人数
    max_set = get_total_quantity(url_followers, headers)
    # 得到每次“请求的返回信息”生成器
    users_page_list = get_user_list(url_followers, headers, max_set, sleep_time)
    # 打开保存用户信息的文件
    with open(file_zhihu, 'w', encoding='utf8', newline='') as f:
        # 建立 CSV 写入对象
        writer = csv.writer(f)
        # 写入题头
        writer.writerow(titles)
        # 循环调用单次请求的返回信息
        for users_page in users_page_list:
            # 得到清理后的“用户信息生成器”
            user_info_list = get_user_data(users_page)
            # 循环调用单个用户信息
            for user_info in user_info_list:
                # 写入用户信息
                writer.writerow(user_info)
    # 得到活跃用户 hash_id 生成器
    active_users = get_active_users(file_zhihu)
    # 循环调用单个活跃用户 hash_id
    for user_hash in active_users:
        # 关注活跃用户
        follow_them(user_hash, url_follow, headers)


if __name__ == '__main__':
    main_loop()
